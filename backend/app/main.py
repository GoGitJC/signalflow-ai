from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import RequestContextMiddleware, configure_logging, request_id_ctx
from app.core.metrics import metrics
from app.core.rate_limit import RateLimitMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.startup import ProductionConfigError, validate_production_settings

settings = get_settings()
configure_logging(settings.log_level, json_logs=settings.log_json)
logger = logging.getLogger("signalflow")


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        validate_production_settings(settings)
    except ProductionConfigError as exc:
        logger.error("startup_validation_failed detail=%s", str(exc))
        raise
    logger.info(
        "startup environment=%s integration_mode=%s",
        settings.environment,
        settings.integration_mode,
    )
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)
if settings.rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        path = request.url.path
        route_family = "other"
        if path.startswith("/api/webhooks"):
            route_family = "webhook"
            metrics.incr("signalflow_webhook_requests_total", method=request.method)
        elif path.startswith("/api/auth"):
            route_family = "auth"
        elif "book" in path:
            route_family = "booking"
            metrics.incr("signalflow_booking_requests_total")
        metrics.incr(
            "signalflow_http_requests_total",
            method=request.method,
            family=route_family,
            status=str(response.status_code),
        )
        metrics.observe(
            "signalflow_http_request_duration_ms",
            elapsed_ms,
            family=route_family,
        )
        if response.status_code >= 500:
            metrics.incr("signalflow_http_errors_total", family=route_family)
        return response


app.add_middleware(MetricsMiddleware)
app.include_router(api_router)


def _error_payload(
    *,
    code: str,
    message: str,
    details: object | None = None,
) -> dict[str, object]:
    # Include legacy `detail` for existing clients/tests while rolling out the error schema.
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id_ctx.get("-"),
            "details": details,
        },
        "detail": message,
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        code = str(detail.get("code"))
        message = str(detail.get("message"))
        details = detail.get("details")
    elif isinstance(detail, str):
        code = "http_error"
        message = detail
        details = None
    else:
        code = "http_error"
        message = "Request failed"
        details = detail
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(code=code, message=message, details=details),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            code="validation_error",
            message="Request validation failed",
            details=exc.errors(),
        ),
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(_: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            code="validation_error",
            message="Validation failed",
            details=exc.errors(),
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled request error")
    metrics.incr("signalflow_http_errors_total", family="unhandled")
    return JSONResponse(
        status_code=500,
        content=_error_payload(
            code="internal_error",
            message="Internal server error",
        ),
    )
