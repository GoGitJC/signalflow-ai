from datetime import datetime

from pydantic import BaseModel, Field


class AvailabilityRequest(BaseModel):
    business_id: str
    event_type_id: str | None = None
    start: datetime
    end: datetime
    timezone: str | None = None


class AvailabilityResponse(BaseModel):
    slots: list[datetime]
    mocked: bool = False


class BookingRequest(BaseModel):
    business_id: str
    event_type_id: str | None = None
    start: datetime
    name: str
    email: str
    phone: str | None = None
    service: str
    timezone: str | None = None
    call_id: str | None = None
    retell_call_id: str | None = None


class BookingResponse(BaseModel):
    cal_event_id: str
    start_time: datetime
    end_time: datetime
    status: str
    mocked: bool = False
    duplicate: bool = False
    appointment_id: str | None = None


class SmsSummaryRequest(BaseModel):
    business_id: str
    to: str = Field(min_length=3)
    message: str = Field(min_length=1, max_length=1500)


class SmsSummaryResponse(BaseModel):
    message_id: str
    status: str
    mocked: bool = False


class RetellIntegrationUpsert(BaseModel):
    api_key: str = Field(min_length=1)
    agent_id: str | None = None
    agent_name: str = "Universal_Demo"
    confirm_replace: bool = False


class CalComIntegrationUpsert(BaseModel):
    api_key: str = Field(min_length=1)
    event_type_id: str | None = None
    event_type_slug: str | None = None
    username: str | None = None
    confirm_replace: bool = False


class IntegrationStatusResponse(BaseModel):
    connected: bool
    mode: str
    last_test_at: datetime | None = None
    last_test_status: str | None = None
    last_test_error: str | None = None


class RetellStatusResponse(IntegrationStatusResponse):
    agent_name: str | None = None
    agent_id_masked: str | None = None
    webhook_url: str | None = None
    webhook_configured: bool = False


class CalComStatusResponse(IntegrationStatusResponse):
    event_type_name: str | None = None
    event_type_id: str | None = None
    event_type_slug: str | None = None
    username: str | None = None


class ConnectionTestResponse(BaseModel):
    ok: bool
    mocked: bool = False
    message: str | None = None


class VoiceFriendlySlot(BaseModel):
    option_id: str = Field(description="Stable ID the agent must pass back when booking")
    start: datetime
    label: str = Field(description="Spoken-friendly local time label")
    timezone: str


class RetellToolAvailabilityRequest(BaseModel):
    retell_agent_id: str = Field(min_length=1)
    start: datetime
    end: datetime
    timezone: str | None = Field(default="America/Chicago")
    max_options: int = Field(default=5, ge=1, le=10)


class RetellToolAvailabilityResponse(BaseModel):
    available: bool
    timezone: str
    options: list[VoiceFriendlySlot]
    spoken_summary: str
    message: str


class RetellToolBookingRequest(BaseModel):
    retell_agent_id: str = Field(min_length=1)
    start: datetime
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=32)
    service: str = Field(min_length=1, max_length=200)
    timezone: str | None = Field(default="America/Chicago")
    option_id: str | None = Field(
        default=None, description="option_id returned from check_availability"
    )
    caller_confirmed: bool = Field(
        description="Must be true after the caller explicitly confirms the selected slot"
    )
    retell_call_id: str | None = Field(
        default=None, description="Optional Retell call ID to link the appointment"
    )


class RetellToolBookingResponse(BaseModel):
    booked: bool
    cal_event_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str
    appointment_id: str | None = None
    spoken_summary: str
    message: str
    requires_confirmation: bool = False
    duplicate: bool = False
