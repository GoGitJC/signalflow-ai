from __future__ import annotations

import threading
import time
from typing import cast

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimiter:
    """Simple fixed-window counter suitable for single-instance deployments."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._windows: dict[str, tuple[int, float]] = {}

    def allow(self, key: str, *, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        with self._lock:
            count, reset_at = self._windows.get(key, (0, now + window_seconds))
            if now >= reset_at:
                count, reset_at = 0, now + window_seconds
            count += 1
            self._windows[key] = (count, reset_at)
            return count <= limit


rate_limiter = RateLimiter()

# path prefix -> (limit, window_seconds)
RATE_LIMIT_RULES: list[tuple[str, int, int]] = [
    ("/api/auth/login", 20, 60),
    ("/api/auth/register", 10, 60),
    ("/api/auth/forgot-password", 10, 60),
    ("/api/auth/reset-password", 10, 60),
    ("/api/auth/", 60, 60),
    ("/api/webhooks/", 120, 60),
    ("/api/retell/", 120, 60),
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        path = request.url.path
        client = request.client.host if request.client else "unknown"
        for prefix, limit, window in RATE_LIMIT_RULES:
            if path.startswith(prefix) or path == prefix.rstrip("/"):
                key = f"{client}:{prefix}"
                if not rate_limiter.allow(key, limit=limit, window_seconds=window):
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": {
                                "code": "rate_limited",
                                "message": "Too many requests. Please try again shortly.",
                                "request_id": request.headers.get("x-request-id"),
                            }
                        },
                        headers={"Retry-After": str(window)},
                    )
                break
        return cast(Response, await call_next(request))
