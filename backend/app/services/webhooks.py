import hashlib
import hmac
import json
from datetime import UTC

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Appointment, Business, Call, Caller, WebhookEvent
from app.schemas.call import RetellCallEndedPayload


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
        appointment = None
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
    db.commit()
    db.refresh(call)
    if appointment:
        db.refresh(appointment)
    return call, appointment
