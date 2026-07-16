"""Final acceptance / readiness snapshot for closed beta."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import assert_tenant_access, require_business_admin
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Appointment, Call, Caller, KnowledgeBaseEntry
from app.services.integrations import calcom_status_view, retell_status_view

router = APIRouter(tags=["readiness"])


class ReadinessCheck(BaseModel):
    id: str
    label: str
    status: str  # ok | warn | fail
    detail: str


class ReadinessResponse(BaseModel):
    score: int
    checks: list[ReadinessCheck]
    environment: str
    integration_mode: str
    allow_live_booking: bool
    retell_connected: bool
    calcom_connected: bool
    twilio_configured: bool
    knowledge_count: int
    callers_count: int
    calls_count: int
    appointments_count: int


@router.get("/api/businesses/{business_id}/readiness", response_model=ReadinessResponse)
def business_readiness(
    business_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_admin),
):
    assert_tenant_access(tenant_id, business_id)
    settings = get_settings()
    retell = retell_status_view(db, business_id)
    calcom = calcom_status_view(db, business_id)
    twilio_configured = bool(settings.twilio_account_sid and settings.twilio_auth_token)

    knowledge_count = (
        db.scalar(
            select(func.count())
            .select_from(KnowledgeBaseEntry)
            .where(KnowledgeBaseEntry.business_id == business_id)
        )
        or 0
    )
    callers_count = (
        db.scalar(select(func.count()).select_from(Caller).where(Caller.business_id == business_id))
        or 0
    )
    calls_count = (
        db.scalar(select(func.count()).select_from(Call).where(Call.business_id == business_id))
        or 0
    )
    appointments_count = (
        db.scalar(
            select(func.count())
            .select_from(Appointment)
            .where(Appointment.business_id == business_id)
        )
        or 0
    )

    is_prod = settings.environment.lower() in {"production", "prod"}
    checks: list[ReadinessCheck] = [
        ReadinessCheck(
            id="retell",
            label="Retell connected",
            status="ok" if retell.get("connected") else "warn",
            detail="Connected"
            if retell.get("connected")
            else "Connect Retell in Settings or Onboarding",
        ),
        ReadinessCheck(
            id="calcom",
            label="Cal.com connected",
            status="ok" if calcom.get("connected") else "warn",
            detail="Connected"
            if calcom.get("connected")
            else "Connect Cal.com in Settings or Onboarding",
        ),
        ReadinessCheck(
            id="twilio",
            label="Twilio configured",
            status="ok" if twilio_configured else "warn",
            detail="SID/token present"
            if twilio_configured
            else "Placeholder — SMS on Final Acceptance",
        ),
        ReadinessCheck(
            id="booking_gate",
            label="Live booking gate",
            status="ok" if not settings.allow_live_booking else "warn",
            detail=(
                "ALLOW_LIVE_BOOKING=false (safe for beta)"
                if not settings.allow_live_booking
                else "Live booking enabled — confirm Final Acceptance first"
            ),
        ),
        ReadinessCheck(
            id="webhooks",
            label="Webhook readiness",
            status="ok"
            if retell.get("webhook_configured") or not settings.is_live_mode
            else "warn",
            detail=(f"Webhook URL: {retell.get('webhook_url') or settings.retell_webhook_url}"),
        ),
        ReadinessCheck(
            id="knowledge",
            label="Knowledge base",
            status="ok" if knowledge_count > 0 else "fail",
            detail=f"{knowledge_count} entries",
        ),
        ReadinessCheck(
            id="demo_data",
            label="CRM activity",
            status="ok" if callers_count and calls_count else "warn",
            detail=f"{callers_count} customers, {calls_count} calls, {appointments_count} appointments",
        ),
        ReadinessCheck(
            id="cookies",
            label="Secure cookies",
            status="ok" if (settings.auth_cookie_secure or not is_prod) else "fail",
            detail=(
                "AUTH_COOKIE_SECURE=true"
                if settings.auth_cookie_secure
                else "Set AUTH_COOKIE_SECURE=true for production HTTPS"
            ),
        ),
        ReadinessCheck(
            id="cors",
            label="Frontend origin",
            status=(
                "ok" if (not is_prod or "localhost" not in settings.frontend_origin) else "fail"
            ),
            detail=settings.frontend_origin,
        ),
        ReadinessCheck(
            id="rate_limit",
            label="Rate limiting",
            status="ok" if settings.rate_limit_enabled else "warn",
            detail="Enabled" if settings.rate_limit_enabled else "RATE_LIMIT_ENABLED=false",
        ),
        ReadinessCheck(
            id="logging",
            label="JSON logging",
            status="ok" if settings.log_json or not is_prod else "warn",
            detail="LOG_JSON=" + ("true" if settings.log_json else "false"),
        ),
        ReadinessCheck(
            id="environment",
            label="Environment",
            status="ok",
            detail=f"{settings.environment} / INTEGRATION_MODE={settings.integration_mode}",
        ),
    ]

    ok = sum(1 for c in checks if c.status == "ok")
    score = int(round(100 * ok / len(checks))) if checks else 0

    return ReadinessResponse(
        score=score,
        checks=checks,
        environment=settings.environment,
        integration_mode=settings.integration_mode,
        allow_live_booking=settings.allow_live_booking,
        retell_connected=bool(retell.get("connected")),
        calcom_connected=bool(calcom.get("connected")),
        twilio_configured=twilio_configured,
        knowledge_count=int(knowledge_count),
        callers_count=int(callers_count),
        calls_count=int(calls_count),
        appointments_count=int(appointments_count),
    )
