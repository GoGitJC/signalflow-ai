from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.integration import (
    AvailabilityRequest,
    RetellToolAvailabilityRequest,
    RetellToolAvailabilityResponse,
    RetellToolBookingRequest,
    RetellToolBookingResponse,
)
from app.services.appointments import book_appointment_transactional
from app.services.integrations import (
    get_scheduling_for_business,
    load_calcom_credentials,
    resolve_business_for_retell_agent,
)

router = APIRouter(prefix="/api/retell/tools", tags=["retell-tools"])
settings = get_settings()


def _business_from_agent(db: Session, retell_agent_id: str) -> str:
    try:
        return resolve_business_for_retell_agent(db, retell_agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/check_availability", response_model=RetellToolAvailabilityResponse)
def check_availability(payload: RetellToolAvailabilityRequest, db: Session = Depends(get_db)):
    business_id = _business_from_agent(db, payload.retell_agent_id)
    creds = load_calcom_credentials(db, business_id)
    provider = get_scheduling_for_business(db, business_id)
    request = AvailabilityRequest(
        business_id=business_id,
        event_type_id=creds.get("event_type_id"),
        start=payload.start,
        end=payload.end,
        timezone=payload.timezone,
    )
    slots = provider.availability(request)
    return RetellToolAvailabilityResponse(slots=slots)


@router.post("/book_appointment", response_model=RetellToolBookingResponse)
def book_appointment(payload: RetellToolBookingRequest, db: Session = Depends(get_db)):
    business_id = _business_from_agent(db, payload.retell_agent_id)
    creds = load_calcom_credentials(db, business_id)
    from app.schemas.integration import BookingRequest

    request = BookingRequest(
        business_id=business_id,
        event_type_id=creds.get("event_type_id"),
        start=payload.start,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        service=payload.service,
        timezone=payload.timezone,
    )
    appointment, result = book_appointment_transactional(db, request)
    return RetellToolBookingResponse(
        cal_event_id=result["cal_event_id"],
        start_time=result["start_time"],
        end_time=result["end_time"],
        status=result.get("status", "booked"),
        appointment_id=appointment.id,
    )
