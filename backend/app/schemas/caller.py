from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CallerUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    notes: str | None = None
    tags: list[str] | None = None
    status: str | None = Field(default=None, max_length=40)


class CallerRead(ORMModel):
    id: str
    business_id: str
    name: str | None
    phone: str
    email: str | None
    notes: str | None
    tags: list[str]
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    call_count: int = 0
    appointment_count: int = 0
    last_interaction_at: datetime | None = None


class CallerDetail(CallerRead):
    recent_call_ids: list[str] = Field(default_factory=list)
    recent_appointment_ids: list[str] = Field(default_factory=list)
