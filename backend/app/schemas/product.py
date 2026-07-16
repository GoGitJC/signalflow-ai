from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel
from app.schemas.kb import KnowledgeBaseCreate


class KnowledgeBaseVersionRead(ORMModel):
    id: str
    entry_id: str
    business_id: str
    version: int
    category: str
    question: str
    answer: str
    active: bool
    created_at: datetime


class KnowledgeBaseBulkImport(BaseModel):
    entries: list[KnowledgeBaseCreate] = Field(min_length=1, max_length=200)


class KnowledgeBaseBulkResult(BaseModel):
    created: int
    ids: list[str]


class AuditEventRead(BaseModel):
    id: str
    source: str
    business_id: str | None
    provider: str | None = None
    user_id: str | None = None
    action: str
    status: str
    detail: str | None
    created_at: datetime
