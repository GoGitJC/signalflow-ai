import hashlib
import hmac
import json
from datetime import UTC

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.retell_signature import verify_retell_signature
from app.models import Appointment, Business, Call, Caller, WebhookEvent
from app.schemas.call import RetellCallEndedPayload
from app.services.audit import record_audit


def verify_hmac_signature(raw_body: bytes, signature: str | None, secret: str) -> None:
    if not secret:
        return
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing webhook signature"
        )
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    supplied = signature.removeprefix("sha256=")
    if not hmac.compare_digest(expected, supplied):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
        )


def verify_retell_webhook(
    raw_body: bytes,
    signature: str | None,
    *,
    settings: Settings | None = None,
    api_key: str | None = None,
    allow_bypass: bool = False,
) -> None:
    settings = settings or get_settings()
    if settings.mock_external_services:
        if allow_bypass or not settings.retell_webhook_secret:
            return
        verify_hmac_signature(raw_body, signature, settings.retell_webhook_secret)
        return
    verify_retell_signature(raw_body.decode("utf-8"), signature, api_key or settings.retell_api_key)


def event_key(payload: dict, explicit_id: str | None = None) -> str:
    if explicit_id:
        return explicit_id
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(canonical).hexdigest()


def claim_event(db: Session, provider: str, key: str, event_type: str) -> bool:
    if db.scalar(
        select(WebhookEvent).where(WebhookEvent.provider == provider, WebhookEvent.event_key == key)
    ):
        return False
    db.add(WebhookEvent(provider=provider, event_key=key, event_type=event_type))
    try:
        db.flush()
        return True
    except IntegrityError:
        db.rollback()
        return False


def build_summary(payload: RetellCallEndedPayload) -> str:
    if payload.summary:
        return payload.summary.strip()
    parts = [
        f"{payload.caller.name or 'Caller'} called about {payload.intent or 'an unspecified request'}."
    ]
    if payload.requested_service:
        parts.append(f"Requested service: {payload.requested_service}.")
    parts.append(f"Urgency: {payload.urgency}. Outcome: {payload.outcome}.")
    if payload.appointment:
        parts.append(f"Appointment booked for {payload.appointment.start_time.isoformat()}.")
    return " ".join(parts)


def process_completed_call(
    db: Session, payload: RetellCallEndedPayload
) -> tuple[Call, Appointment | None]:
    business = db.get(Business, payload.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    caller = db.scalar(
        select(Caller).where(
            Caller.business_id == payload.business_id, Caller.phone == payload.caller.phone
        )
    )
    if caller is None:
        caller = Caller(
            business_id=payload.business_id,
            name=payload.caller.name,
            phone=payload.caller.phone,
            email=payload.caller.email,
        )
        db.add(caller)
        db.flush()
    else:
        caller.name = payload.caller.name or caller.name
        caller.email = payload.caller.email or caller.email

    call = db.scalar(select(Call).where(Call.retell_call_id == payload.retell_call_id))
    duration = max(0, int((payload.ended_at - payload.started_at).total_seconds()))
    values = dict(
        business_id=payload.business_id,
        caller_id=caller.id,
        direction=payload.direction,
        started_at=payload.started_at.astimezone(UTC),
        ended_at=payload.ended_at.astimezone(UTC),
        duration_seconds=duration,
        transcript=payload.transcript,
        summary=build_summary(payload),
        intent=payload.intent,
        urgency=payload.urgency,
        outcome=payload.outcome,
        sentiment=payload.sentiment,
        recording_url=payload.recording_url,
        appointment_booked=payload.appointment is not None,
    )
    if call is None:
        call = Call(retell_call_id=payload.retell_call_id, **values)
        db.add(call)
        db.flush()
    else:
        if call.business_id != payload.business_id:
            raise HTTPException(status_code=409, detail="Call ID belongs to another business")
        for field, value in values.items():
            setattr(call, field, value)

    appointment = None
    if payload.appointment:
        if payload.appointment.cal_event_id:
            appointment = db.scalar(
                select(Appointment).where(
                    Appointment.cal_event_id == payload.appointment.cal_event_id
                )
            )
        if appointment is None:
            appointment = Appointment(
                business_id=payload.business_id,
                caller_id=caller.id,
                call_id=call.id,
                cal_event_id=payload.appointment.cal_event_id,
                service=payload.appointment.service,
                start_time=payload.appointment.start_time,
                end_time=payload.appointment.end_time,
                status=payload.appointment.status,
            )
            db.add(appointment)
        elif appointment.call_id is None:
            # Book-first path: tool created the appointment before call_ended.
            appointment.call_id = call.id
            call.appointment_booked = True
        elif appointment.call_id == call.id:
            call.appointment_booked = True
    db.commit()
    db.refresh(call)
    if appointment:
        db.refresh(appointment)
    return call, appointment


def sync_calcom_booking_status(db: Session, payload: dict) -> Appointment | None:
    booking_uid = payload.get("uid") or payload.get("bookingUid") or payload.get("id")
    if not booking_uid:
        return None
    appointment = db.scalar(select(Appointment).where(Appointment.cal_event_id == str(booking_uid)))
    if appointment is None:
        return None
    status_value = payload.get("status") or payload.get("bookingStatus")
    if status_value:
        appointment.status = str(status_value)
        db.commit()
        db.refresh(appointment)
    return appointment


def reject_webhook_audit(
    db: Session, *, business_id: str | None, provider: str, detail: str
) -> None:
    if not business_id:
        return
    record_audit(
        db,
        business_id=business_id,
        provider=provider,
        action="webhook_rejected",
        status="error",
        detail=detail,
    )
    db.commit()
