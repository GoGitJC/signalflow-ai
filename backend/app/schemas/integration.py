from datetime import datetime

from pydantic import BaseModel, Field


class AvailabilityRequest(BaseModel):
    business_id: str
    event_type_id: str
    start: datetime
    end: datetime


class AvailabilityResponse(BaseModel):
    slots: list[datetime]
    mocked: bool


class BookingRequest(BaseModel):
    business_id: str
    event_type_id: str
    start: datetime
    name: str
    email: str
    phone: str | None = None
    service: str


class BookingResponse(BaseModel):
    cal_event_id: str
    start_time: datetime
    end_time: datetime
    status: str
    mocked: bool


class SmsSummaryRequest(BaseModel):
    business_id: str
    to: str = Field(min_length=3)
    message: str = Field(min_length=1, max_length=1500)


class SmsSummaryResponse(BaseModel):
    message_id: str
    status: str
    mocked: bool
