from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import assert_tenant_access, require_business_member
from app.db.session import get_db
from app.models import Appointment, Business, Call, Caller
from app.schemas.caller import CallerDetail, CallerRead, CallerUpdate

router = APIRouter(tags=["callers"])


def _enrich_caller(db: Session, caller: Caller) -> CallerRead:
    call_count = (
        db.scalar(select(func.count()).select_from(Call).where(Call.caller_id == caller.id)) or 0
    )
    appointment_count = (
        db.scalar(
            select(func.count()).select_from(Appointment).where(Appointment.caller_id == caller.id)
        )
        or 0
    )
    last_call = db.scalar(
        select(Call.started_at)
        .where(Call.caller_id == caller.id)
        .order_by(desc(Call.started_at))
        .limit(1)
    )
    last_appt = db.scalar(
        select(Appointment.start_time)
        .where(Appointment.caller_id == caller.id)
        .order_by(desc(Appointment.start_time))
        .limit(1)
    )
    last_interaction = None
    for candidate in (last_call, last_appt, caller.updated_at, caller.created_at):
        if candidate is None:
            continue
        if last_interaction is None or candidate > last_interaction:
            last_interaction = candidate

    tags = caller.tags if isinstance(caller.tags, list) else []
    return CallerRead(
        id=caller.id,
        business_id=caller.business_id,
        name=caller.name,
        phone=caller.phone,
        email=caller.email,
        notes=caller.notes,
        tags=[str(tag) for tag in tags],
        status=caller.status or "lead",
        created_at=caller.created_at,
        updated_at=caller.updated_at,
        call_count=int(call_count),
        appointment_count=int(appointment_count),
        last_interaction_at=last_interaction,
    )


@router.get("/api/businesses/{business_id}/callers", response_model=list[CallerRead])
def list_callers(
    business_id: str,
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    assert_tenant_access(tenant_id, business_id)
    if not db.get(Business, business_id):
        raise HTTPException(status_code=404, detail="Business not found")

    callers = list(db.scalars(select(Caller).where(Caller.business_id == business_id).limit(limit)))
    enriched = [_enrich_caller(db, caller) for caller in callers]
    if q:
        needle = q.strip().lower()
        enriched = [
            item
            for item in enriched
            if needle
            in " ".join(
                filter(
                    None,
                    [item.name, item.phone, item.email, item.notes, " ".join(item.tags)],
                )
            ).lower()
        ]
    if status:
        enriched = [item for item in enriched if item.status == status]
    if tag:
        enriched = [item for item in enriched if tag in item.tags]
    enriched.sort(
        key=lambda item: item.last_interaction_at or item.created_at,
        reverse=True,
    )
    return enriched


@router.get("/api/callers/{caller_id}", response_model=CallerDetail)
def get_caller(
    caller_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    caller = db.get(Caller, caller_id)
    if caller is None:
        raise HTTPException(status_code=404, detail="Caller not found")
    assert_tenant_access(tenant_id, caller.business_id)
    base = _enrich_caller(db, caller)
    recent_calls = list(
        db.scalars(
            select(Call.id)
            .where(Call.caller_id == caller.id)
            .order_by(desc(Call.started_at))
            .limit(10)
        )
    )
    recent_appts = list(
        db.scalars(
            select(Appointment.id)
            .where(Appointment.caller_id == caller.id)
            .order_by(desc(Appointment.start_time))
            .limit(10)
        )
    )
    return CallerDetail(
        **base.model_dump(),
        recent_call_ids=recent_calls,
        recent_appointment_ids=recent_appts,
    )


@router.patch("/api/callers/{caller_id}", response_model=CallerRead)
def update_caller(
    caller_id: str,
    payload: CallerUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    caller = db.get(Caller, caller_id)
    if caller is None:
        raise HTTPException(status_code=404, detail="Caller not found")
    assert_tenant_access(tenant_id, caller.business_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(caller, field, value)
    caller.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(caller)
    return _enrich_caller(db, caller)
