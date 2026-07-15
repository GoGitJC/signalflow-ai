from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import Settings, get_settings
from app.integrations.errors import (
    ProviderConflictError,
    ProviderNotFoundError,
    ProviderValidationError,
)
from app.integrations.http_utils import request_json
from app.schemas.integration import AvailabilityRequest, BookingRequest


class CalComClient:
    def __init__(
        self,
        api_key: str,
        *,
        settings: Settings | None = None,
        event_type_id: str | None = None,
        event_type_slug: str | None = None,
        username: str | None = None,
    ):
        self.api_key = api_key
        self.settings = settings or get_settings()
        self.event_type_id = event_type_id or self.settings.calcom_event_type_id
        self.event_type_slug = event_type_slug or self.settings.calcom_event_type_slug
        self.username = username or self.settings.calcom_username
        self.base_url = self.settings.calcom_api_base_url.rstrip("/")

    def _headers(self, *, api_version: str | None = None) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "cal-api-version": api_version or self.settings.calcom_api_version,
            "Content-Type": "application/json",
        }

    def resolve_event_type(self) -> dict[str, Any]:
        if self.event_type_id:
            payload = request_json(
                self.settings,
                method="GET",
                url=f"{self.base_url}/event-types/{self.event_type_id}",
                headers=self._headers(),
                retryable=True,
            )
            data = payload.get("data", payload)
            if isinstance(data, list):
                if len(data) != 1:
                    raise ProviderNotFoundError("Cal.com event type ID did not resolve uniquely")
                data = data[0]
            return {
                "event_type_id": str(data.get("id") or self.event_type_id),
                "slug": data.get("slug"),
                "title": data.get("title") or data.get("name"),
                "username": data.get("owner", {}).get("username") if isinstance(data.get("owner"), dict) else self.username,
            }

        if not self.event_type_slug or not self.username:
            raise ProviderValidationError(
                "Cal.com event type requires CALCOM_EVENT_TYPE_ID or CALCOM_EVENT_TYPE_SLUG+CALCOM_USERNAME"
            )
        payload = request_json(
            self.settings,
            method="GET",
            url=f"{self.base_url}/event-types",
            headers=self._headers(),
            params={"username": self.username},
            retryable=True,
        )
        items = payload.get("data", payload)
        if isinstance(items, dict):
            items = items.get("event_types") or items.get("items") or []
        matches = [item for item in items if item.get("slug") == self.event_type_slug]
        if not matches:
            raise ProviderNotFoundError(
                f"No Cal.com event type slug '{self.event_type_slug}' for user '{self.username}'"
            )
        if len(matches) > 1:
            raise ProviderConflictError(
                f"Multiple Cal.com event types named '{self.event_type_slug}' for user '{self.username}'"
            )
        item = matches[0]
        return {
            "event_type_id": str(item.get("id")),
            "slug": item.get("slug"),
            "title": item.get("title") or item.get("name"),
            "username": self.username,
        }

    def test_connection(self) -> dict[str, Any]:
        resolved = self.resolve_event_type()
        return {"ok": True, **resolved}

    def availability(self, request: AvailabilityRequest) -> list[datetime]:
        resolved = self.resolve_event_type()
        event_type_id = request.event_type_id or resolved["event_type_id"]
        params: dict[str, str] = {
            "start": request.start.astimezone(UTC).strftime("%Y-%m-%d"),
            "end": request.end.astimezone(UTC).strftime("%Y-%m-%d"),
        }
        if event_type_id:
            params["eventTypeId"] = event_type_id
        else:
            params["username"] = resolved["username"] or self.username or ""
            params["eventTypeSlug"] = resolved["slug"] or self.event_type_slug or ""

        payload = request_json(
            self.settings,
            method="GET",
            url=f"{self.base_url}/slots",
            headers=self._headers(api_version="2024-09-04"),
            params=params,
            retryable=True,
        )
        data = payload.get("data", payload)
        slots: list[datetime] = []
        if isinstance(data, dict):
            for day_slots in data.values():
                if isinstance(day_slots, list):
                    for slot in day_slots:
                        if isinstance(slot, str):
                            slots.append(datetime.fromisoformat(slot.replace("Z", "+00:00")))
                        elif isinstance(slot, dict) and slot.get("start"):
                            slots.append(
                                datetime.fromisoformat(str(slot["start"]).replace("Z", "+00:00"))
                            )
        return sorted(slots)

    def book(self, request: BookingRequest, *, idempotency_key: str | None = None) -> dict:
        resolved = self.resolve_event_type()
        body: dict[str, Any] = {
            "start": request.start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "attendee": {
                "name": request.name,
                "email": request.email,
                "timeZone": request.timezone or "UTC",
            },
            "metadata": {"service": request.service, "business_id": request.business_id},
        }
        event_type_id = request.event_type_id or resolved["event_type_id"]
        if event_type_id:
            body["eventTypeId"] = int(event_type_id) if str(event_type_id).isdigit() else event_type_id
        else:
            body["eventTypeSlug"] = resolved["slug"]
            body["username"] = resolved["username"]

        if request.phone:
            body["attendee"]["phoneNumber"] = request.phone

        headers = self._headers(api_version="2024-08-13")
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        payload = request_json(
            self.settings,
            method="POST",
            url=f"{self.base_url}/bookings",
            headers=headers,
            json_body=body,
        )
        data = payload.get("data", payload)
        booking_uid = data.get("uid") or data.get("bookingUid") or data.get("id")
        if not booking_uid:
            raise ProviderValidationError("Cal.com booking response missing UID")
        start = request.start
        return {
            "cal_event_id": str(booking_uid),
            "start_time": start,
            "end_time": start + timedelta(minutes=int(data.get("lengthInMinutes") or 30)),
            "status": data.get("status") or "booked",
        }
