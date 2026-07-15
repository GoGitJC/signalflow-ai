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


class RetellToolAvailabilityRequest(BaseModel):
    retell_agent_id: str
    start: datetime
    end: datetime
    timezone: str | None = None


class RetellToolAvailabilityResponse(BaseModel):
    slots: list[datetime]


class RetellToolBookingRequest(BaseModel):
    retell_agent_id: str
    start: datetime
    name: str
    email: str
    phone: str | None = None
    service: str
    timezone: str | None = None


class RetellToolBookingResponse(BaseModel):
    cal_event_id: str
    start_time: datetime
    end_time: datetime
    status: str
    appointment_id: str

