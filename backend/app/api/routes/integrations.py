from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.integrations.mock_clients import MockCalComClient, MockTwilioClient
from app.schemas.integration import (
    AvailabilityRequest,
    AvailabilityResponse,
    BookingRequest,
    BookingResponse,
    SmsSummaryRequest,
    SmsSummaryResponse,
)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
settings = get_settings()


def require_mock_mode() -> None:
    if not settings.mock_external_services:
        raise HTTPException(
            status_code=501, detail="Live provider clients are not configured in this phase"
        )


@router.post("/calcom/availability", response_model=AvailabilityResponse)
def availability(payload: AvailabilityRequest):
    require_mock_mode()
    slots = MockCalComClient().availability(payload)
    return AvailabilityResponse(slots=slots, mocked=True)


@router.post("/calcom/book", response_model=BookingResponse)
def book(payload: BookingRequest):
    require_mock_mode()
    result = MockCalComClient().book(payload)
    return BookingResponse(**result, mocked=True)


@router.post("/twilio/send-summary", response_model=SmsSummaryResponse)
def send_summary(payload: SmsSummaryRequest):
    require_mock_mode()
    result = MockTwilioClient().send_sms(payload.to, payload.message)
    return SmsSummaryResponse(**result, mocked=True)
