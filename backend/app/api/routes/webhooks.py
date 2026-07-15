import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Business, Call
from app.schemas.call import (
    CallRead,
    CallWebhookResponse,
    RetellCallEndedPayload,
    RetellCallStartedPayload,
)
from app.services.webhooks import (
    claim_event,
    event_key,
    process_completed_call,
    verify_hmac_signature,
)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
settings = get_settings()


@router.post("/retell/call-started", response_model=CallWebhookResponse)
async def call_started(
    request: Request,
    db: Session = Depends(get_db),
    x_retell_signature: str | None = Header(default=None),
):
    raw = await request.body()
    verify_hmac_signature(raw, x_retell_signature, settings.retell_webhook_secret)
    payload = RetellCallStartedPayload.model_validate_json(raw)
    if not db.get(Business, payload.business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    key = event_key(json.loads(raw), payload.event_id)
    if not claim_event(db, "retell", key, "call_started"):
        return CallWebhookResponse(status="already_processed", duplicate=True)
    call = db.scalar(select(Call).where(Call.retell_call_id == payload.retell_call_id))
    if call is None:
        call = Call(
            business_id=payload.business_id,
            retell_call_id=payload.retell_call_id,
            direction=payload.direction,
            started_at=payload.started_at,
        )
        db.add(call)
    db.commit()
    db.refresh(call)
    return CallWebhookResponse(status="processed", call=CallRead.model_validate(call))


@router.post("/retell/call-ended", response_model=CallWebhookResponse)
async def call_ended(
    request: Request,
    db: Session = Depends(get_db),
    x_retell_signature: str | None = Header(default=None),
):
    raw = await request.body()
    verify_hmac_signature(raw, x_retell_signature, settings.retell_webhook_secret)
    payload = RetellCallEndedPayload.model_validate_json(raw)
    key = event_key(json.loads(raw), payload.event_id)
    if not claim_event(db, "retell", key, "call_ended"):
        existing = db.scalar(select(Call).where(Call.retell_call_id == payload.retell_call_id))
        return CallWebhookResponse(
            status="already_processed",
            duplicate=True,
            call=CallRead.model_validate(existing) if existing else None,
        )
    call, appointment = process_completed_call(db, payload)
    return CallWebhookResponse(
        status="processed",
        call=CallRead.model_validate(call),
        appointment_id=appointment.id if appointment else None,
    )


@router.post("/calcom")
async def calcom_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_cal_signature: str | None = Header(default=None),
):
    raw = await request.body()
    verify_hmac_signature(raw, x_cal_signature, settings.calcom_webhook_secret)
    payload = json.loads(raw)
    key = event_key(payload, payload.get("event_id") or payload.get("id"))
    if not claim_event(db, "calcom", key, payload.get("triggerEvent", "unknown")):
        return {"status": "already_processed", "duplicate": True}
    db.commit()
    return {"status": "accepted", "duplicate": False}
