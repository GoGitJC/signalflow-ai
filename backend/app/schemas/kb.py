from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class KnowledgeBaseCreate(BaseModel):
    category: str = Field(default="general", max_length=120)
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    active: bool = True


class KnowledgeBaseUpdate(BaseModel):
    category: str | None = Field(default=None, max_length=120)
    question: str | None = Field(default=None, min_length=1)
    answer: str | None = Field(default=None, min_length=1)
    active: bool | None = None


class KnowledgeBaseRead(ORMModel):
    id: str
    business_id: str
    category: str
    question: str
    answer: str
    active: bool
