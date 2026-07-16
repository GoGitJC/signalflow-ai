from app.core.config import Settings, get_settings
from app.integrations.calcom_client import CalComClient
from app.integrations.mock_clients import MockCalComClient, MockTwilioClient
from app.integrations.retell_client import RetellClient


def get_retell_client(
    *, api_key: str | None = None, settings: Settings | None = None
) -> RetellClient:
    settings = settings or get_settings()
    key = api_key or settings.retell_api_key
    if not key:
        raise ValueError("Retell API key is required")
    return RetellClient(key, settings=settings)


def get_calcom_client(
    *,
    api_key: str | None = None,
    settings: Settings | None = None,
    event_type_id: str | None = None,
    event_type_slug: str | None = None,
    username: str | None = None,
) -> CalComClient:
    settings = settings or get_settings()
    key = api_key or settings.calcom_api_key
    if not key:
        raise ValueError("Cal.com API key is required")
    return CalComClient(
        key,
        settings=settings,
        event_type_id=event_type_id,
        event_type_slug=event_type_slug,
        username=username,
    )


def get_scheduling_provider(
    *,
    api_key: str | None = None,
    settings: Settings | None = None,
    event_type_id: str | None = None,
    event_type_slug: str | None = None,
    username: str | None = None,
):
    settings = settings or get_settings()
    if settings.mock_external_services:
        return MockCalComClient()
    return get_calcom_client(
        api_key=api_key,
        settings=settings,
        event_type_id=event_type_id,
        event_type_slug=event_type_slug,
        username=username,
    )


def get_twilio_provider(settings: Settings | None = None):
    settings = settings or get_settings()
    if settings.mock_external_services:
        return MockTwilioClient()
    raise NotImplementedError("Live Twilio provider is not implemented in this phase")
