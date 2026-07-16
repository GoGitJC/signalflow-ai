from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import assert_tenant_access, require_business_member
from app.db.session import get_db
from app.models import Business, Call
from app.schemas.call import CallRead

router = APIRouter(tags=["calls"])


@router.get("/api/businesses/{business_id}/calls", response_model=list[CallRead])
def list_calls(
    business_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    assert_tenant_access(tenant_id, business_id)
    if not db.get(Business, business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    stmt = (
        select(Call)
        .where(Call.business_id == business_id)
        .order_by(desc(Call.started_at))
        .limit(limit)
    )
    return list(db.scalars(stmt))


@router.get("/api/calls/{call_id}", response_model=CallRead)
def get_call(
    call_id: str,
    business_id: str = Query(...),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    assert_tenant_access(tenant_id, business_id)
    call = db.scalar(select(Call).where(Call.id == call_id, Call.business_id == business_id))
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call
