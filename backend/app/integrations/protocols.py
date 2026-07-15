from datetime import datetime
from typing import Protocol

from app.schemas.integration import AvailabilityRequest, BookingRequest


class SchedulingProvider(Protocol):
    def availability(self, request: AvailabilityRequest) -> list[datetime]: ...

    def book(self, request: BookingRequest, *, idempotency_key: str | None = None) -> dict: ...


class RetellManagementProvider(Protocol):
    def test_connection(self) -> dict: ...

    def resolve_agent(self, *, agent_id: str | None, agent_name: str) -> dict: ...
