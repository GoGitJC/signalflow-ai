from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CallerPayload(BaseModel):
    name: str | None = None
    phone: str = Field(min_length=3, max_length=32)
    email: str | None = None


class AppointmentPayload(BaseModel):
    cal_event_id: str | None = None
    service: str
    start_time: datetime
    end_time: datetime
    status: str = "booked"


class RetellCallStartedPayload(BaseModel):
    event_id: str | None = None
    business_id: str
    retell_call_id: str
    direction: str = "inbound"
    started_at: datetime
    caller_phone: str | None = None


class RetellCallEndedPayload(BaseModel):
    event_id: str | None = None
    business_id: str
    retell_call_id: str
    direction: str = "inbound"
    started_at: datetime
    ended_at: datetime
    transcript: str = ""
    recording_url: str | None = None
    caller: CallerPayload
    intent: str | None = None
    urgency: str = "normal"
    outcome: str = "completed"
    summary: str | None = None
    requested_service: str | None = None
    appointment: AppointmentPayload | None = None


class CallRead(ORMModel):
    id: str
    business_id: str
    caller_id: str | None
    retell_call_id: str
    direction: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int | None
    transcript: str | None
    summary: str | None
    intent: str | None
    urgency: str | None
    outcome: str | None
    recording_url: str | None
    appointment_booked: bool


class CallWebhookResponse(BaseModel):
    status: str
    duplicate: bool = False
    call: CallRead | None = None
    appointment_id: str | None = None
