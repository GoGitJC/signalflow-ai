import uuid
from datetime import datetime, timedelta

from app.schemas.integration import AvailabilityRequest, BookingRequest


class MockCalComClient:
    def availability(self, request: AvailabilityRequest) -> list[datetime]:
        cursor = request.start
        slots: list[datetime] = []
        while cursor < request.end and len(slots) < 8:
            slots.append(cursor)
            cursor += timedelta(hours=1)
        return slots

    def book(self, request: BookingRequest, *, idempotency_key: str | None = None) -> dict:
        return {
            "cal_event_id": f"mock-cal-{uuid.uuid4()}",
            "start_time": request.start,
            "end_time": request.start + timedelta(minutes=30),
            "status": "booked",
        }


class MockTwilioClient:
    def send_sms(self, to: str, message: str) -> dict:
        if not to or not message:
            raise ValueError("SMS destination and message are required")
        return {"message_id": f"SM{uuid.uuid4().hex}", "status": "queued"}
