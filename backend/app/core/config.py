from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SignalFlow AI"
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("SIGNALFLOW_ENVIRONMENT", "APP_ENV", "ENVIRONMENT"),
    )
    database_url: str = "postgresql+psycopg://signalflow:signalflow@db:5432/signalflow"
    frontend_origin: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("SIGNALFLOW_FRONTEND_ORIGIN", "FRONTEND_ORIGIN"),
    )
    # Comma-separated allowlist for credentialed CORS (www + app dashboards).
    cors_origins: str = Field(
        default="",
        validation_alias=AliasChoices("CORS_ORIGINS", "SIGNALFLOW_CORS_ORIGINS"),
    )
    trusted_hosts: str = Field(
        default="",
        validation_alias=AliasChoices("TRUSTED_HOSTS", "SIGNALFLOW_TRUSTED_HOSTS"),
    )
    app_public_api_url: str = Field(
        default="http://localhost:8000", validation_alias="APP_PUBLIC_API_URL"
    )

    # Legacy SIGNALFLOW_ names remain supported.
    credential_encryption_key: str = Field(default="", repr=False)
    retell_webhook_secret: str = Field(default="", repr=False)
    calcom_webhook_secret: str = Field(default="", repr=False)
    twilio_account_sid: str = Field(default="", repr=False)
    twilio_auth_token: str = Field(default="", repr=False)
    mock_external_services: bool = True

    integration_mode: Literal["mock", "live"] = Field(
        default="mock", validation_alias="INTEGRATION_MODE"
    )

    retell_api_key: str = Field(default="", repr=False, validation_alias="RETELL_API_KEY")
    retell_agent_id: str = Field(default="", validation_alias="RETELL_AGENT_ID")
    retell_agent_name: str = Field(default="Universal_Demo", validation_alias="RETELL_AGENT_NAME")
    retell_webhook_base_url: str = Field(default="", validation_alias="RETELL_WEBHOOK_BASE_URL")

    calcom_api_key: str = Field(default="", repr=False, validation_alias="CALCOM_API_KEY")
    calcom_api_base_url: str = Field(
        default="https://api.cal.com/v2", validation_alias="CALCOM_API_BASE_URL"
    )
    calcom_api_version: str = Field(default="2024-09-04", validation_alias="CALCOM_API_VERSION")
    calcom_event_type_id: str = Field(default="", validation_alias="CALCOM_EVENT_TYPE_ID")
    calcom_event_type_slug: str = Field(default="", validation_alias="CALCOM_EVENT_TYPE_SLUG")
    calcom_username: str = Field(default="", validation_alias="CALCOM_USERNAME")

    provider_timeout_seconds: float = 15.0
    owner_api_token: str = Field(default="", repr=False, validation_alias="OWNER_API_TOKEN")
    allow_live_booking: bool = Field(default=False, validation_alias="ALLOW_LIVE_BOOKING")
    calcom_event_types_api_version: str = Field(
        default="2024-06-14", validation_alias="CALCOM_EVENT_TYPES_API_VERSION"
    )
    jwt_secret: str = Field(default="", repr=False, validation_alias="JWT_SECRET")
    jwt_access_ttl_minutes: int = Field(default=30, validation_alias="JWT_ACCESS_TTL_MINUTES")
    jwt_refresh_ttl_days: int = Field(default=14, validation_alias="JWT_REFRESH_TTL_DAYS")
    jwt_refresh_remember_days: int = Field(default=30, validation_alias="JWT_REFRESH_REMEMBER_DAYS")
    auth_cookie_secure: bool = Field(default=False, validation_alias="AUTH_COOKIE_SECURE")
    auth_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax", validation_alias="AUTH_COOKIE_SAMESITE"
    )
    auth_cookie_domain: str = Field(
        default="",
        validation_alias=AliasChoices("AUTH_COOKIE_DOMAIN", "SIGNALFLOW_AUTH_COOKIE_DOMAIN"),
    )
    auth_access_cookie_name: str = "sf_access"
    auth_refresh_cookie_name: str = "sf_refresh"
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_json: bool = Field(default=True, validation_alias="LOG_JSON")
    rate_limit_enabled: bool = Field(default=True, validation_alias="RATE_LIMIT_ENABLED")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SIGNALFLOW_",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("auth_cookie_samesite", mode="before")
    @classmethod
    def normalize_samesite(cls, value: object) -> object:
        if isinstance(value, str):
            return value.lower()
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        # Render/Heroku style URLs use postgresql://; SQLAlchemy needs the psycopg driver.
        if isinstance(value, str) and value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value.removeprefix("postgresql://")
        if isinstance(value, str) and value.startswith("postgres://"):
            return "postgresql+psycopg://" + value.removeprefix("postgres://")
        return value

    @model_validator(mode="after")
    def sync_integration_mode(self) -> "Settings":
        if self.integration_mode == "mock":
            object.__setattr__(self, "mock_external_services", True)
        elif self.integration_mode == "live":
            object.__setattr__(self, "mock_external_services", False)
        return self

    @property
    def is_live_mode(self) -> bool:
        return self.integration_mode == "live"

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw:
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        if self.frontend_origin.strip():
            return [self.frontend_origin.strip()]
        return []

    @property
    def trusted_host_list(self) -> list[str]:
        raw = self.trusted_hosts.strip()
        if not raw:
            return []
        return [host.strip() for host in raw.split(",") if host.strip()]

    @property
    def retell_webhook_url(self) -> str:
        base = (self.retell_webhook_base_url or self.app_public_api_url).rstrip("/")
        return f"{base}/api/webhooks/retell"

    def require_live_retell_config(self) -> None:
        missing = []
        if not self.retell_api_key:
            missing.append("RETELL_API_KEY")
        if missing:
            raise ValueError(f"Live Retell mode requires: {', '.join(missing)}")

    def require_live_calcom_config(self) -> None:
        missing = []
        if not self.calcom_api_key:
            missing.append("CALCOM_API_KEY")
        if not self.calcom_event_type_id and not (
            self.calcom_event_type_slug and self.calcom_username
        ):
            missing.append("CALCOM_EVENT_TYPE_ID or CALCOM_EVENT_TYPE_SLUG+CALCOM_USERNAME")
        if missing:
            raise ValueError(f"Live Cal.com mode requires: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
