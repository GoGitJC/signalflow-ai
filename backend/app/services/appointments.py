import hashlib
import logging
import re
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import request_id_ctx
from app.integrations.errors import ProviderConflictError, ProviderError, ProviderValidationError
from app.models import Appointment, Call, Caller
from app.schemas.integration import BookingRequest
from app.services.audit import record_audit
from app.services.integrations import get_scheduling_for_business

logger = logging.getLogger("signalflow.booking")

_PLACEHOLDER_EMAIL = re.compile(
    r"(?i)@(example\.com|example\.org|example\.net|test\.com|mailinator\.com)$|^mail@example\.com$"
)


def booking_idempotency_key(request: BookingRequest) -> str:
    raw = (
        f"{request.business_id}:{request.event_type_id}:{request.start.isoformat()}:"
        f"{request.email}:{request.phone or ''}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def _mask_email(value: str | None) -> str:
    if not value or "@" not in value:
        return "***"
    local, _, domain = value.partition("@")
    return f"{local[:1]}***@{domain}"


def _mask_phone(value: str | None) -> str:
    if not value:
        return "***"
    digits = re.sub(r"\D", "", value)
    if len(digits) < 4:
        return "***"
    return f"***{digits[-4:]}"


def _reject_placeholder_attendee(request: BookingRequest, *, live_mode: bool) -> None:
    if not live_mode:
        return
    if _PLACEHOLDER_EMAIL.search(request.email.strip()):
        raise HTTPException(
            status_code=422,
            detail="Attendee email must be a real deliverable address (placeholders like @example.com are rejected).",
        )


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

    _reject_placeholder_attendee(request, live_mode=settings.is_live_mode)

    provider = get_scheduling_for_business(db, request.business_id)
    idempotency_key = booking_idempotency_key(request)
    start_utc = request.start.astimezone(UTC)
    correlation_id = request_id_ctx.get("-")

    logger.info(
        "booking_start correlation_id=%s business_id=%s retell_call_id=%s event_type_id=%s "
        "start_utc=%s timezone=%s attendee_email=%s attendee_phone=%s",
        correlation_id,
        request.business_id,
        request.retell_call_id or "-",
        request.event_type_id or "-",
        start_utc.isoformat(),
        request.timezone or "-",
        _mask_email(request.email),
        _mask_phone(request.phone),
    )

    existing = db.scalar(
        select(Appointment).where(
            Appointment.business_id == request.business_id,
            Appointment.cal_event_id.isnot(None),
            Appointment.start_time == start_utc,
            Appointment.service == request.service,
        )
    )
    if existing and existing.cal_event_id:
        logger.info(
            "booking_duplicate_local correlation_id=%s appointment_id=%s cal_event_id=%s",
            correlation_id,
            existing.id,
            existing.cal_event_id,
        )
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
        if request.phone:
            caller.phone = request.phone

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
        logger.info(
            "booking_provider_conflict correlation_id=%s business_id=%s",
            correlation_id,
            request.business_id,
        )
        raise HTTPException(
            status_code=409, detail="Requested slot is no longer available"
        ) from exc
    except ProviderValidationError as exc:
        record_audit(
            db,
            business_id=request.business_id,
            provider="calcom",
            action="booking_failed",
            status="error",
            detail="validation",
        )
        db.commit()
        logger.info(
            "booking_provider_validation correlation_id=%s business_id=%s",
            correlation_id,
            request.business_id,
        )
        raise HTTPException(status_code=400, detail="Cal.com rejected the booking request") from exc
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
        logger.info(
            "booking_provider_error correlation_id=%s business_id=%s status=%s",
            correlation_id,
            request.business_id,
            exc.status_code or 502,
        )
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
        logger.exception(
            "booking_unexpected_error correlation_id=%s business_id=%s",
            correlation_id,
            request.business_id,
        )
        raise HTTPException(status_code=502, detail="Cal.com booking failed") from exc

    # If provider succeeded earlier but local row already exists (retry), reuse it.
    by_uid = db.scalar(
        select(Appointment).where(
            Appointment.business_id == request.business_id,
            Appointment.cal_event_id == remote["cal_event_id"],
        )
    )
    if by_uid is not None:
        logger.info(
            "booking_idempotent_uid correlation_id=%s appointment_id=%s cal_event_id=%s",
            correlation_id,
            by_uid.id,
            by_uid.cal_event_id,
        )
        return by_uid, {
            "cal_event_id": by_uid.cal_event_id,
            "start_time": by_uid.start_time,
            "end_time": by_uid.end_time,
            "status": by_uid.status,
            "duplicate": True,
        }

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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        recovered = db.scalar(
            select(Appointment).where(
                Appointment.business_id == request.business_id,
                Appointment.cal_event_id == remote["cal_event_id"],
            )
        )
        if recovered is None:
            raise
        logger.info(
            "booking_integrity_recovered correlation_id=%s appointment_id=%s cal_event_id=%s",
            correlation_id,
            recovered.id,
            recovered.cal_event_id,
        )
        return recovered, {
            "cal_event_id": recovered.cal_event_id,
            "start_time": recovered.start_time,
            "end_time": recovered.end_time,
            "status": recovered.status,
            "duplicate": True,
        }

    db.refresh(appointment)
    logger.info(
        "booking_success correlation_id=%s appointment_id=%s cal_event_id=%s retell_call_id=%s",
        correlation_id,
        appointment.id,
        appointment.cal_event_id,
        request.retell_call_id or "-",
    )
    return appointment, {
        **remote,
        "start_time": appointment.start_time,
        "end_time": appointment.end_time,
        "duplicate": False,
    }
