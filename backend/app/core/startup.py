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
    if not settings.frontend_origin or "localhost" in settings.frontend_origin:
        missing.append("SIGNALFLOW_FRONTEND_ORIGIN (non-localhost)")
    if settings.integration_mode == "live":
        if not settings.retell_webhook_secret and not settings.retell_api_key:
            missing.append("RETELL_WEBHOOK_SECRET or RETELL_API_KEY")
        if not settings.calcom_webhook_secret and settings.calcom_api_key:
            missing.append("SIGNALFLOW_CALCOM_WEBHOOK_SECRET (recommended when Cal.com live)")
    if not settings.auth_cookie_secure:
        missing.append("AUTH_COOKIE_SECURE=true")
    if missing:
        raise ProductionConfigError("Production configuration incomplete: " + ", ".join(missing))
