from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import assert_tenant_access, require_business_member
from app.db.session import get_db
from app.models import Business, KnowledgeBaseEntry, KnowledgeBaseEntryVersion
from app.schemas.kb import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate
from app.schemas.product import (
    KnowledgeBaseBulkImport,
    KnowledgeBaseBulkResult,
    KnowledgeBaseVersionRead,
)

router = APIRouter(tags=["knowledge-base"])


def _snapshot_version(db: Session, entry: KnowledgeBaseEntry) -> None:
    current = db.scalar(
        select(func.max(KnowledgeBaseEntryVersion.version)).where(
            KnowledgeBaseEntryVersion.entry_id == entry.id
        )
    )
    version = int(current or 0) + 1
    db.add(
        KnowledgeBaseEntryVersion(
            entry_id=entry.id,
            business_id=entry.business_id,
            version=version,
            category=entry.category,
            question=entry.question,
            answer=entry.answer,
            active=entry.active,
        )
    )


@router.post(
    "/api/businesses/{business_id}/knowledge-base",
    response_model=KnowledgeBaseRead,
    status_code=201,
)
def create_entry(
    business_id: str,
    payload: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    assert_tenant_access(tenant_id, business_id)
    if not db.get(Business, business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    entry = KnowledgeBaseEntry(business_id=business_id, **payload.model_dump())
    db.add(entry)
    db.flush()
    _snapshot_version(db, entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.post(
    "/api/businesses/{business_id}/knowledge-base/bulk",
    response_model=KnowledgeBaseBulkResult,
    status_code=201,
)
def bulk_import(
    business_id: str,
    payload: KnowledgeBaseBulkImport,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    assert_tenant_access(tenant_id, business_id)
    if not db.get(Business, business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    ids: list[str] = []
    for item in payload.entries:
        entry = KnowledgeBaseEntry(business_id=business_id, **item.model_dump())
        db.add(entry)
        db.flush()
        _snapshot_version(db, entry)
        ids.append(entry.id)
    db.commit()
    return KnowledgeBaseBulkResult(created=len(ids), ids=ids)


@router.get("/api/businesses/{business_id}/knowledge-base", response_model=list[KnowledgeBaseRead])
def list_entries(
    business_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    assert_tenant_access(tenant_id, business_id)
    if not db.get(Business, business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    return list(
        db.scalars(select(KnowledgeBaseEntry).where(KnowledgeBaseEntry.business_id == business_id))
    )


@router.patch("/api/knowledge-base/{entry_id}", response_model=KnowledgeBaseRead)
def update_entry(
    entry_id: str,
    payload: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    entry = db.get(KnowledgeBaseEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge-base entry not found")
    assert_tenant_access(tenant_id, entry.business_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    entry.updated_at = datetime.now(UTC)
    _snapshot_version(db, entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get(
    "/api/knowledge-base/{entry_id}/versions",
    response_model=list[KnowledgeBaseVersionRead],
)
def list_versions(
    entry_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    entry = db.get(KnowledgeBaseEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge-base entry not found")
    assert_tenant_access(tenant_id, entry.business_id)
    return list(
        db.scalars(
            select(KnowledgeBaseEntryVersion)
            .where(KnowledgeBaseEntryVersion.entry_id == entry_id)
            .order_by(desc(KnowledgeBaseEntryVersion.version))
        )
    )


@router.delete("/api/knowledge-base/{entry_id}", status_code=204)
def delete_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
) -> Response:
    entry = db.get(KnowledgeBaseEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge-base entry not found")
    assert_tenant_access(tenant_id, entry.business_id)
    db.delete(entry)
    db.commit()
    return Response(status_code=204)
