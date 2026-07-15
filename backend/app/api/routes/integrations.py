from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_owner_token
from app.core.config import get_settings
from app.db.session import get_db
from app.integrations.errors import ProviderError
from app.integrations.factory import get_scheduling_provider, get_twilio_provider
from app.models import IntegrationProvider
from app.schemas.integration import (
    AvailabilityRequest,
    AvailabilityResponse,
    BookingRequest,
    BookingResponse,
    CalComIntegrationUpsert,
    CalComStatusResponse,
    ConnectionTestResponse,
    RetellIntegrationUpsert,
    RetellStatusResponse,
    SmsSummaryRequest,
    SmsSummaryResponse,
)
from app.services.appointments import book_appointment_transactional
from app.services.integrations import (
    calcom_status_view,
    load_calcom_credentials,
    load_retell_credentials,
    retell_status_view,
    test_calcom_connection,
    test_retell_connection,
    upsert_integration,
)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
settings = get_settings()


@router.get("/retell/status", response_model=RetellStatusResponse)
def retell_status(
    business_id: str = Depends(require_owner_token),
    db: Session = Depends(get_db),
):
    return RetellStatusResponse(**retell_status_view(db, business_id))


@router.put("/retell", response_model=RetellStatusResponse)
def upsert_retell(
    payload: RetellIntegrationUpsert,
    business_id: str = Depends(require_owner_token),
    db: Session = Depends(get_db),
):
    existing = load_retell_credentials(db, business_id)
    if existing.get("api_key") and not payload.confirm_replace:
        raise HTTPException(status_code=409, detail="Confirm credential replacement")
    upsert_integration(
        db,
        business_id=business_id,
        provider=IntegrationProvider.retell,
        credentials={
            "api_key": payload.api_key,
            "agent_id": payload.agent_id,
            "agent_name": payload.agent_name,
        },
        metadata={"agent_id": payload.agent_id, "agent_name": payload.agent_name},
    )
    db.commit()
    return RetellStatusResponse(**retell_status_view(db, business_id))


@router.post("/retell/test", response_model=ConnectionTestResponse)
def retell_test(
    business_id: str = Depends(require_owner_token),
    db: Session = Depends(get_db),
):
    try:
        result = test_retell_connection(db, business_id)
    except ProviderError as exc:
        raise HTTPException(status_code=exc.status_code or 502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ConnectionTestResponse(
        ok=result.get("ok", True),
        mocked=result.get("mocked", False),
        message=f"Retell agent {result.get('agent_name')} resolved",
    )


@router.get("/calcom/status", response_model=CalComStatusResponse)
def calcom_status(
    business_id: str = Depends(require_owner_token),
    db: Session = Depends(get_db),
):
    return CalComStatusResponse(**calcom_status_view(db, business_id))


@router.put("/calcom", response_model=CalComStatusResponse)
def upsert_calcom(
    payload: CalComIntegrationUpsert,
    business_id: str = Depends(require_owner_token),
    db: Session = Depends(get_db),
):
    existing = load_calcom_credentials(db, business_id)
    if existing.get("api_key") and not payload.confirm_replace:
        raise HTTPException(status_code=409, detail="Confirm credential replacement")
    upsert_integration(
        db,
        business_id=business_id,
        provider=IntegrationProvider.calcom,
        credentials={
            "api_key": payload.api_key,
            "event_type_id": payload.event_type_id,
            "event_type_slug": payload.event_type_slug,
            "username": payload.username,
        },
        metadata={
            "event_type_id": payload.event_type_id,
            "event_type_slug": payload.event_type_slug,
            "username": payload.username,
        },
    )
    db.commit()
    return CalComStatusResponse(**calcom_status_view(db, business_id))


@router.post("/calcom/test", response_model=ConnectionTestResponse)
def calcom_test(
    business_id: str = Depends(require_owner_token),
    db: Session = Depends(get_db),
):
    try:
        result = test_calcom_connection(db, business_id)
    except ProviderError as exc:
        raise HTTPException(status_code=exc.status_code or 502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ConnectionTestResponse(
        ok=result.get("ok", True),
        mocked=result.get("mocked", False),
        message=f"Cal.com event type {result.get('title') or result.get('slug')} resolved",
    )


@router.post("/calcom/availability", response_model=AvailabilityResponse)
def availability(payload: AvailabilityRequest, db: Session = Depends(get_db)):
    creds = load_calcom_credentials(db, payload.business_id)
    provider = get_scheduling_provider(
        api_key=creds.get("api_key"),
        event_type_id=creds.get("event_type_id") or payload.event_type_id,
        event_type_slug=creds.get("event_type_slug"),
        username=creds.get("username"),
    )
    slots = provider.availability(payload)
    return AvailabilityResponse(slots=slots, mocked=settings.mock_external_services)


@router.post("/calcom/book", response_model=BookingResponse)
def book(payload: BookingRequest, db: Session = Depends(get_db)):
    creds = load_calcom_credentials(db, payload.business_id)
    if not payload.event_type_id:
        payload = payload.model_copy(update={"event_type_id": creds.get("event_type_id")})
    appointment, result = book_appointment_transactional(db, payload)
    return BookingResponse(
        cal_event_id=result["cal_event_id"],
        start_time=result["start_time"],
        end_time=result["end_time"],
        status=result.get("status", "booked"),
        mocked=settings.mock_external_services,
        duplicate=bool(result.get("duplicate")),
        appointment_id=appointment.id,
    )


@router.post("/twilio/send-summary", response_model=SmsSummaryResponse)
def send_summary(payload: SmsSummaryRequest):
    result = get_twilio_provider().send_sms(payload.to, payload.message)
    return SmsSummaryResponse(**result, mocked=settings.mock_external_services)
