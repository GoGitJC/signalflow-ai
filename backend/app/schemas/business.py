from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class BusinessCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=120)
    phone_number: str | None = Field(default=None, max_length=32)
    forwarding_number: str | None = Field(default=None, max_length=32)
    timezone: str = "America/Chicago"
    business_hours: dict = Field(default_factory=dict)
    service_area: str | None = None


class BusinessUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=120)
    phone_number: str | None = Field(default=None, max_length=32)
    forwarding_number: str | None = Field(default=None, max_length=32)
    timezone: str | None = None
    business_hours: dict | None = None
    service_area: str | None = None


class BusinessRead(ORMModel):
    id: str
    name: str
    industry: str | None
    phone_number: str | None
    forwarding_number: str | None
    timezone: str
    business_hours: dict
    service_area: str | None
    created_at: datetime
    updated_at: datetime
