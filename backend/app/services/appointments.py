import hashlib
from datetime import UTC

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Appointment, Caller
from app.schemas.integration import BookingRequest
from app.services.audit import record_audit
from app.services.integrations import get_scheduling_for_business


def booking_idempotency_key(request: BookingRequest) -> str:
    raw = f"{request.business_id}:{request.event_type_id}:{request.start.isoformat()}:{request.email}:{request.phone or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()


def book_appointment_transactional(db: Session, request: BookingRequest) -> tuple[Appointment, dict]:
    provider = get_scheduling_for_business(db, request.business_id)
    idempotency_key = booking_idempotency_key(request)

    existing = db.scalar(
        select(Appointment).where(
            Appointment.business_id == request.business_id,
            Appointment.cal_event_id.isnot(None),
            Appointment.start_time == request.start.astimezone(UTC),
            Appointment.service == request.service,
        )
    )
    if existing and existing.cal_event_id:
        return existing, {
            "cal_event_id": existing.cal_event_id,
            "start_time": existing.start_time,
            "end_time": existing.end_time,
            "status": existing.status,
            "duplicate": True,
        }

    caller = db.scalar(
        select(Caller).where(
            Caller.business_id == request.business_id,
            Caller.email == request.email,
        )
    )
    if caller is None and request.phone:
        caller = db.scalar(
            select(Caller).where(
                Caller.business_id == request.business_id,
                Caller.phone == request.phone,
            )
        )
    if caller is None:
        caller = Caller(
            business_id=request.business_id,
            name=request.name,
            email=request.email,
            phone=request.phone or "unknown",
        )
        db.add(caller)
        db.flush()

    try:
        remote = provider.book(request, idempotency_key=idempotency_key)
    except Exception as exc:
        record_audit(
            db,
            business_id=request.business_id,
            provider="calcom",
            action="booking_failed",
            status="error",
            detail=str(exc),
        )
        db.commit()
        raise HTTPException(status_code=502, detail="Cal.com booking failed") from exc

    appointment = Appointment(
        business_id=request.business_id,
        caller_id=caller.id,
        cal_event_id=remote["cal_event_id"],
        service=request.service,
        start_time=remote["start_time"],
        end_time=remote["end_time"],
        status=remote.get("status", "booked"),
    )
    db.add(appointment)
    record_audit(
        db,
        business_id=request.business_id,
        provider="calcom",
        action="booking_created",
        status="ok",
        detail=remote["cal_event_id"],
    )
    db.commit()
    db.refresh(appointment)
    return appointment, remote
