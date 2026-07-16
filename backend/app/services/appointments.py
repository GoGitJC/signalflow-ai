import hashlib
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.errors import ProviderConflictError, ProviderError
from app.models import Appointment, Call, Caller
from app.schemas.integration import BookingRequest
from app.services.audit import record_audit
from app.services.integrations import get_scheduling_for_business


def booking_idempotency_key(request: BookingRequest) -> str:
    raw = (
        f"{request.business_id}:{request.event_type_id}:{request.start.isoformat()}:"
        f"{request.email}:{request.phone or ''}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def _resolve_call_id(db: Session, request: BookingRequest) -> str | None:
    if request.call_id:
        call = db.scalar(
            select(Call).where(
                Call.id == request.call_id,
                Call.business_id == request.business_id,
            )
        )
        if call is None:
            raise HTTPException(status_code=404, detail="Call not found for business")
        return call.id
    if request.retell_call_id:
        call = db.scalar(
            select(Call).where(
                Call.retell_call_id == request.retell_call_id,
                Call.business_id == request.business_id,
            )
        )
        if call is None:
            return None
        return call.id
    return None


def book_appointment_transactional(
    db: Session,
    request: BookingRequest,
    *,
    allow_live: bool | None = None,
) -> tuple[Appointment, dict]:
    settings = get_settings()
    live_allowed = settings.allow_live_booking if allow_live is None else allow_live
    if settings.is_live_mode and not live_allowed and not settings.mock_external_services:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live Cal.com booking is disabled. Set ALLOW_LIVE_BOOKING=true to enable.",
        )

    provider = get_scheduling_for_business(db, request.business_id)
    idempotency_key = booking_idempotency_key(request)
    start_utc = request.start.astimezone(UTC)

    existing = db.scalar(
        select(Appointment).where(
            Appointment.business_id == request.business_id,
            Appointment.cal_event_id.isnot(None),
            Appointment.start_time == start_utc,
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
    else:
        caller.name = request.name or caller.name
        caller.email = request.email or caller.email

    call_id = _resolve_call_id(db, request)

    try:
        remote = provider.book(request, idempotency_key=idempotency_key)
    except ProviderConflictError as exc:
        record_audit(
            db,
            business_id=request.business_id,
            provider="calcom",
            action="booking_failed",
            status="error",
            detail="conflict",
        )
        db.commit()
        raise HTTPException(
            status_code=409, detail="Requested slot is no longer available"
        ) from exc
    except ProviderError as exc:
        record_audit(
            db,
            business_id=request.business_id,
            provider="calcom",
            action="booking_failed",
            status="error",
            detail=type(exc).__name__,
        )
        db.commit()
        raise HTTPException(
            status_code=exc.status_code or 502, detail="Cal.com booking failed"
        ) from exc
    except Exception as exc:
        record_audit(
            db,
            business_id=request.business_id,
            provider="calcom",
            action="booking_failed",
            status="error",
            detail="unexpected",
        )
        db.commit()
        raise HTTPException(status_code=502, detail="Cal.com booking failed") from exc

    start_time = remote["start_time"]
    if isinstance(start_time, datetime) and start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=UTC)
    end_time = remote["end_time"]
    if isinstance(end_time, datetime) and end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=UTC)

    appointment = Appointment(
        business_id=request.business_id,
        caller_id=caller.id,
        call_id=call_id,
        cal_event_id=remote["cal_event_id"],
        service=request.service,
        start_time=start_time,
        end_time=end_time,
        status=remote.get("status", "booked"),
    )
    db.add(appointment)
    if call_id:
        call = db.get(Call, call_id)
        if call is not None:
            call.appointment_booked = True

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
    return appointment, {
        **remote,
        "start_time": appointment.start_time,
        "end_time": appointment.end_time,
        "duplicate": False,
    }
