from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import request_id_ctx
from app.db.session import get_db
from app.schemas.integration import (
    AvailabilityRequest,
    BookingRequest,
    RetellToolAvailabilityRequest,
    RetellToolAvailabilityResponse,
    RetellToolBookingRequest,
    RetellToolBookingResponse,
    VoiceFriendlySlot,
)
from app.services.appointments import book_appointment_transactional
from app.services.integrations import (
    get_scheduling_for_business,
    load_calcom_credentials,
    resolve_business_for_retell_agent,
)

router = APIRouter(prefix="/api/retell/tools", tags=["retell-tools"])
settings = get_settings()
booking_log = logging.getLogger("signalflow.booking")


def _business_from_agent(db: Session, retell_agent_id: str) -> str:
    try:
        return resolve_business_for_retell_agent(db, retell_agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _zone(name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(name or "America/Chicago")
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Invalid timezone") from exc


def _option_id(start: datetime) -> str:
    return f"slot_{int(start.astimezone(UTC).timestamp())}"


def _voice_label(start: datetime, timezone: str) -> str:
    local = start.astimezone(_zone(timezone))
    hour = local.hour % 12 or 12
    return f"{local.strftime('%A')} at {hour}:{local.strftime('%M')} {local.strftime('%p')}"


def _parse_option_id(option_id: str) -> datetime | None:
    if not option_id.startswith("slot_"):
        return None
    try:
        return datetime.fromtimestamp(int(option_id.removeprefix("slot_")), tz=UTC)
    except ValueError:
        return None


@router.post("/check_availability", response_model=RetellToolAvailabilityResponse)
def check_availability(payload: RetellToolAvailabilityRequest, db: Session = Depends(get_db)):
    business_id = _business_from_agent(db, payload.retell_agent_id)
    creds = load_calcom_credentials(db, business_id)
    provider = get_scheduling_for_business(db, business_id)
    timezone = payload.timezone or "America/Chicago"
    request = AvailabilityRequest(
        business_id=business_id,
        event_type_id=creds.get("event_type_id"),
        start=payload.start,
        end=payload.end,
        timezone=timezone,
    )
    slots = provider.availability(request)[: payload.max_options]
    options = [
        VoiceFriendlySlot(
            option_id=_option_id(slot),
            start=slot,
            label=_voice_label(slot, timezone),
            timezone=timezone,
        )
        for slot in slots
    ]
    if not options:
        return RetellToolAvailabilityResponse(
            available=False,
            timezone=timezone,
            options=[],
            spoken_summary="There are no openings in that time window.",
            message="no_slots",
        )
    spoken = "Available times: " + "; ".join(option.label for option in options) + "."
    return RetellToolAvailabilityResponse(
        available=True,
        timezone=timezone,
        options=options,
        spoken_summary=spoken,
        message="ok",
    )


@router.post("/book_appointment", response_model=RetellToolBookingResponse)
def book_appointment(payload: RetellToolBookingRequest, db: Session = Depends(get_db)):
    if not payload.caller_confirmed:
        return RetellToolBookingResponse(
            booked=False,
            status="confirmation_required",
            spoken_summary="Please confirm the selected time with the caller before booking.",
            message="caller_confirmed must be true",
            requires_confirmation=True,
        )

    business_id = _business_from_agent(db, payload.retell_agent_id)
    creds = load_calcom_credentials(db, business_id)
    start = payload.start
    if payload.option_id:
        parsed = _parse_option_id(payload.option_id)
        if parsed is None:
            raise HTTPException(status_code=422, detail="Invalid option_id")
        # Prefer explicit option_id over free-form start to avoid agent drift.
        start = parsed

    booking_log.info(
        "retell_book_tool correlation_id=%s business_id=%s retell_agent_id=%s retell_call_id=%s "
        "event_type_id=%s start_utc=%s option_id=%s",
        request_id_ctx.get("-"),
        business_id,
        payload.retell_agent_id,
        payload.retell_call_id or "-",
        creds.get("event_type_id") or "-",
        start.astimezone(UTC).isoformat(),
        payload.option_id or "-",
    )

    request = BookingRequest(
        business_id=business_id,
        event_type_id=creds.get("event_type_id"),
        start=start,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        service=payload.service,
        timezone=payload.timezone,
        retell_call_id=payload.retell_call_id,
    )
    appointment, result = book_appointment_transactional(db, request)
    label = _voice_label(result["start_time"], payload.timezone or "America/Chicago")
    duplicate = bool(result.get("duplicate"))
    return RetellToolBookingResponse(
        booked=True,
        cal_event_id=result["cal_event_id"],
        start_time=result["start_time"],
        end_time=result["end_time"],
        status=result.get("status", "booked"),
        appointment_id=appointment.id,
        spoken_summary=(
            f"Your appointment is already booked for {label}."
            if duplicate
            else f"You're booked for {label}."
        ),
        message="duplicate" if duplicate else "booked",
        duplicate=duplicate,
    )
