from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import assert_tenant_access, require_bootstrap_owner, require_business_member
from app.db.session import get_db
from app.models import Business
from app.schemas.business import BusinessCreate, BusinessRead, BusinessUpdate

router = APIRouter(prefix="/api/businesses", tags=["businesses"])


@router.post("", response_model=BusinessRead, status_code=201)
def create_business(
    payload: BusinessCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_bootstrap_owner),
) -> Business:
    business = Business(**payload.model_dump())
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.get("/{business_id}", response_model=BusinessRead)
def get_business(
    business_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
) -> Business:
    assert_tenant_access(tenant_id, business_id)
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.patch("/{business_id}", response_model=BusinessRead)
def update_business(
    business_id: str,
    payload: BusinessUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
) -> Business:
    assert_tenant_access(tenant_id, business_id)
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(business, field, value)
    db.commit()
    db.refresh(business)
    return business
