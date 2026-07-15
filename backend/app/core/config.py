from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SignalFlow AI"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://signalflow:signalflow@db:5432/signalflow"
    frontend_origin: str = "http://localhost:5173"
    credential_encryption_key: str = Field(default="", repr=False)
    retell_webhook_secret: str = Field(default="", repr=False)
    calcom_webhook_secret: str = Field(default="", repr=False)
    twilio_account_sid: str = Field(default="", repr=False)
    twilio_auth_token: str = Field(default="", repr=False)
    mock_external_services: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SIGNALFLOW_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
