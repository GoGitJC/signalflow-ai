from __future__ import annotations

import json
import logging
import re
import time
from contextvars import ContextVar
from typing import Any, cast
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

_SENSITIVE = re.compile(
    r"(?i)(password|api[_-]?key|authorization|token|secret|refresh_token|access_token)"
)
_PHONE = re.compile(r"\+?\d[\d\-\s()]{8,}\d")
_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_ctx.get("-"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level_name: str = "INFO", *, json_logs: bool = True) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler()
    if json_logs:
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s request_id=%(request_id)s"
            )
        )
    root.addHandler(handler)
    root.setLevel(level)

    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        record.request_id = request_id_ctx.get("-")  # type: ignore[attr-defined]
        return record

    logging.setLogRecordFactory(record_factory)


def redact_text(value: str) -> str:
    redacted = _EMAIL.sub("[redacted-email]", value)
    redacted = _PHONE.sub("[redacted-phone]", redacted)
    if _SENSITIVE.search(redacted):
        return "[redacted]"
    return redacted


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        token = request_id_ctx.set(request_id)
        started = time.perf_counter()
        try:
            response = cast(Response, await call_next(request))
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            response.headers["X-Request-ID"] = request_id
            logging.getLogger("signalflow.access").info(
                "request method=%s path=%s status=%s duration_ms=%s",
                request.method,
                request.url.path,
                getattr(response, "status_code", 0),
                duration_ms,
            )
            return response
        finally:
            request_id_ctx.reset(token)
