import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.integrations.retell_normalizer import (
    normalize_retell_webhook,
    to_call_ended,
    to_call_started,
)
from app.models import Business, Call
from app.schemas.call import (
    CallRead,
    CallWebhookResponse,
    RetellCallEndedPayload,
    RetellCallStartedPayload,
)
from app.services.integrations import load_retell_credentials, resolve_business_for_retell_agent
from app.services.webhooks import (
    claim_event,
    event_key,
    process_completed_call,
    reject_webhook_audit,
    sync_calcom_booking_status,
    verify_hmac_signature,
    verify_retell_webhook,
)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
settings = get_settings()


def _resolve_business_id(db: Session, payload: dict, explicit_business_id: str | None) -> str:
    if explicit_business_id:
        return explicit_business_id
    call = payload.get("call") or {}
    agent_id = call.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=422, detail="Retell agent_id is required")
    try:
        return resolve_business_for_retell_agent(db, agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/retell", response_model=CallWebhookResponse)
async def retell_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_retell_signature: str | None = Header(default=None),
):
    raw = await request.body()
    business_id: str | None = None
    try:
        payload = json.loads(raw)
        business_id = _resolve_business_id(db, payload, payload.get("business_id"))
        creds = load_retell_credentials(db, business_id)
        verify_retell_webhook(
            raw,
            x_retell_signature,
            settings=settings,
            api_key=creds.get("api_key"),
            allow_bypass=settings.mock_external_services,
        )
    except HTTPException as exc:
        reject_webhook_audit(db, business_id=business_id, provider="retell", detail=exc.detail)
        raise

    event, call = normalize_retell_webhook(payload)
    key = event_key(payload, f"{call.get('call_id')}:{event}")
    if not claim_event(db, "retell", key, event):
        existing = db.scalar(select(Call).where(Call.retell_call_id == call.get("call_id")))
        return CallWebhookResponse(
            status="already_processed",
            duplicate=True,
            call=CallRead.model_validate(existing) if existing else None,
        )

    if event == "call_started":
        started = to_call_started(call, business_id)
        if not db.get(Business, started.business_id):
            raise HTTPException(status_code=404, detail="Business not found")
        existing_call = db.scalar(select(Call).where(Call.retell_call_id == started.retell_call_id))
        if existing_call is None:
            db.add(
                Call(
                    business_id=started.business_id,
                    retell_call_id=started.retell_call_id,
                    direction=started.direction,
                    started_at=started.started_at,
                )
            )
        db.commit()
        call_row = db.scalar(select(Call).where(Call.retell_call_id == started.retell_call_id))
        return CallWebhookResponse(status="processed", call=CallRead.model_validate(call_row))

    if event in {"call_ended", "call_analyzed"}:
        ended = to_call_ended(call, business_id)
        call_row, appointment = process_completed_call(db, ended)
        return CallWebhookResponse(
            status="processed",
            call=CallRead.model_validate(call_row),
            appointment_id=appointment.id if appointment else None,
        )

    db.commit()
    return CallWebhookResponse(status="ignored", duplicate=False)


@router.post("/retell/call-started", response_model=CallWebhookResponse)
async def call_started(
    request: Request,
    db: Session = Depends(get_db),
    x_retell_signature: str | None = Header(default=None),
):
    raw = await request.body()
    verify_retell_webhook(
        raw,
        x_retell_signature,
        settings=settings,
        allow_bypass=settings.mock_external_services,
    )
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
    verify_retell_webhook(
        raw,
        x_retell_signature,
        settings=settings,
        allow_bypass=settings.mock_external_services,
    )
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
    booking = payload.get("payload") or payload.get("booking") or payload
    appointment = sync_calcom_booking_status(db, booking)
    db.commit()
    return {
        "status": "accepted",
        "duplicate": False,
        "appointment_id": appointment.id if appointment else None,
    }
