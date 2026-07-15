from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class AppointmentCreate(BaseModel):
    business_id: str
    caller_id: str
    call_id: str | None = None
    cal_event_id: str | None = None
    service: str
    start_time: datetime
    end_time: datetime
    status: str = "booked"


class AppointmentUpdate(BaseModel):
    service: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str | None = None


class AppointmentRead(ORMModel):
    id: str
    business_id: str
    caller_id: str
    call_id: str | None
    cal_event_id: str | None
    service: str
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime
