from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SignalFlow AI"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://signalflow:signalflow@db:5432/signalflow"
    frontend_origin: str = "http://localhost:5173"
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SIGNALFLOW_",
        extra="ignore",
        populate_by_name=True,
    )

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
