from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class VoiceAgentUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    greeting: str | None = None
    system_prompt: str | None = None
    voice: str | None = Field(default=None, max_length=80)
    temperature: float | None = Field(default=None, ge=0, le=2)
    transfer_number: str | None = Field(default=None, max_length=32)
    transfer_rules: str | None = None
    active: bool | None = None


class VoiceAgentRead(ORMModel):
    id: str
    business_id: str
    retell_agent_id: str
    name: str
    retell_agent_name: str | None
    greeting: str
    system_prompt: str
    voice: str | None
    temperature: float | None
    transfer_number: str | None
    transfer_rules: str | None
    active: bool
    updated_at: datetime | None = None
