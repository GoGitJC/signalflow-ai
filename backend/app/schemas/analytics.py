from datetime import datetime

from pydantic import BaseModel, Field


class AnalyticsSeriesPoint(BaseModel):
    label: str
    date: str
    calls: int
    bookings: int
    leads: int


class AnalyticsFunnel(BaseModel):
    calls: int
    interested: int
    booked: int
    completed: int
    cancelled: int


class AnalyticsSummary(BaseModel):
    range: str
    from_at: datetime
    to_at: datetime
    calls_today: int
    calls_total: int
    bookings: int
    conversion_rate: float
    average_duration_seconds: float
    missed_calls: int
    transfers: int
    ai_resolution_rate: float
    booking_funnel: AnalyticsFunnel
    lead_sources: dict[str, int] = Field(default_factory=dict)
    series: list[AnalyticsSeriesPoint] = Field(default_factory=list)
