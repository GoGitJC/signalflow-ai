from __future__ import annotations

from app.core.config import Settings


class ProductionConfigError(RuntimeError):
    pass


def validate_production_settings(settings: Settings) -> None:
    if settings.environment.lower() not in {"production", "prod"}:
        return
    missing: list[str] = []
    if not settings.jwt_secret:
        missing.append("JWT_SECRET")
    if not settings.credential_encryption_key:
        missing.append("SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY")
    origins = settings.cors_origin_list
    if not origins:
        missing.append("CORS_ORIGINS or SIGNALFLOW_FRONTEND_ORIGIN")
    elif any("localhost" in origin or "127.0.0.1" in origin for origin in origins):
        missing.append("CORS_ORIGINS must not include localhost in production")
    if settings.integration_mode == "live":
        if not settings.retell_webhook_secret and not settings.retell_api_key:
            missing.append("RETELL_WEBHOOK_SECRET or RETELL_API_KEY")
        if not settings.calcom_webhook_secret and settings.calcom_api_key:
            missing.append("SIGNALFLOW_CALCOM_WEBHOOK_SECRET (recommended when Cal.com live)")
    if not settings.auth_cookie_secure:
        missing.append("AUTH_COOKIE_SECURE=true")
    if settings.auth_cookie_samesite == "none" and not settings.auth_cookie_secure:
        missing.append("AUTH_COOKIE_SECURE=true required when SameSite=None")
    if not settings.app_public_api_url or "localhost" in settings.app_public_api_url:
        missing.append("APP_PUBLIC_API_URL (public https API URL)")
    if missing:
        raise ProductionConfigError("Production configuration incomplete: " + ", ".join(missing))
