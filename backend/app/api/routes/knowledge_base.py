from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import assert_tenant_access, require_business_member
from app.db.session import get_db
from app.models import Business, KnowledgeBaseEntry
from app.schemas.kb import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate

router = APIRouter(tags=["knowledge-base"])


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
    db.commit()
    db.refresh(entry)
    return entry


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
    db.commit()
    db.refresh(entry)
    return entry


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
