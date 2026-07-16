from __future__ import annotations

from datetime import timedelta

from fastapi import Response

from app.core.config import Settings


def set_auth_cookies(
    response: Response,
    *,
    settings: Settings,
    access_token: str,
    refresh_token: str,
    remember_me: bool = False,
) -> None:
    refresh_days = (
        settings.jwt_refresh_remember_days if remember_me else settings.jwt_refresh_ttl_days
    )
    domain = settings.auth_cookie_domain or None
    response.set_cookie(
        key=settings.auth_access_cookie_name,
        value=access_token,
        max_age=int(timedelta(minutes=settings.jwt_access_ttl_minutes).total_seconds()),
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
        domain=domain,
    )
    response.set_cookie(
        key=settings.auth_refresh_cookie_name,
        value=refresh_token,
        max_age=int(timedelta(days=refresh_days).total_seconds()),
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
        domain=domain,
    )


def clear_auth_cookies(response: Response, *, settings: Settings) -> None:
    domain = settings.auth_cookie_domain or None
    for name in (settings.auth_access_cookie_name, settings.auth_refresh_cookie_name):
        response.delete_cookie(
            key=name,
            path="/",
            domain=domain,
            secure=settings.auth_cookie_secure,
            httponly=True,
            samesite=settings.auth_cookie_samesite,
        )
