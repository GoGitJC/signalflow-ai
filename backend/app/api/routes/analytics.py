from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import assert_tenant_access, require_business_member
from app.db.session import get_db
from app.models import Appointment, Business, Call
from app.schemas.analytics import AnalyticsFunnel, AnalyticsSeriesPoint, AnalyticsSummary

router = APIRouter(tags=["analytics"])


def _range_window(range_key: str) -> tuple[datetime, datetime, datetime, int]:
    now = datetime.now(UTC)
    key = range_key.lower()
    if key in {"7d", "7", "last_7_days"}:
        days = 7
    elif key in {"30d", "30", "last_30_days"}:
        days = 30
    elif key in {"month", "monthly"}:
        days = max(now.day, 1)
    else:
        days = 7
    start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    # Calls use a trailing window; appointments also include upcoming slots in the same horizon.
    call_end = now
    appointment_end = (now + timedelta(days=days)).replace(
        hour=23, minute=59, second=59, microsecond=0
    )
    return start, call_end, appointment_end, days


@router.get("/api/businesses/{business_id}/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(
    business_id: str,
    range_key: str = Query(default="7d", alias="range"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    assert_tenant_access(tenant_id, business_id)
    if not db.get(Business, business_id):
        raise HTTPException(status_code=404, detail="Business not found")

    start, call_end, appointment_end, days = _range_window(range_key)
    today = datetime.now(UTC).date()

    calls = list(
        db.scalars(
            select(Call).where(
                Call.business_id == business_id,
                Call.started_at.is_not(None),
                Call.started_at >= start,
                Call.started_at <= call_end,
            )
        )
    )
    appointments = list(
        db.scalars(
            select(Appointment).where(
                Appointment.business_id == business_id,
                Appointment.start_time >= start,
                Appointment.start_time <= appointment_end,
            )
        )
    )

    calls_today = sum(1 for call in calls if call.started_at and call.started_at.date() == today)
    booked = sum(1 for appt in appointments if appt.status in {"booked", "confirmed", "completed"})
    durations = [call.duration_seconds or 0 for call in calls if call.duration_seconds is not None]
    avg_duration = (sum(durations) / len(durations)) if durations else 0.0
    missed = sum(
        1 for call in calls if (call.outcome or "").lower() in {"missed", "no_answer", "voicemail"}
    )
    transfers = sum(
        1
        for call in calls
        if (call.outcome or "").lower() in {"transferred", "transfer"}
        or (call.intent or "").lower() == "transfer"
    )
    resolved = sum(
        1
        for call in calls
        if call.appointment_booked
        or (call.outcome or "").lower()
        in {"completed", "appointment_booked", "resolved", "answered"}
    )
    interested = sum(
        1
        for call in calls
        if call.appointment_booked
        or (call.intent or "").lower() in {"book_appointment", "schedule", "pricing"}
    )
    completed = sum(1 for appt in appointments if appt.status == "completed")
    cancelled = sum(1 for appt in appointments if appt.status == "cancelled")
    conversion = (booked / len(calls)) if calls else 0.0
    ai_resolution = (resolved / len(calls)) if calls else 0.0

    lead_sources: dict[str, int] = {}
    for call in calls:
        source = call.intent or call.direction or "unknown"
        lead_sources[source] = lead_sources.get(source, 0) + 1

    series: list[AnalyticsSeriesPoint] = []
    for offset in range(days):
        day = (start + timedelta(days=offset)).date()
        day_calls = [c for c in calls if c.started_at and c.started_at.date() == day]
        day_bookings = [a for a in appointments if a.start_time.date() == day]
        series.append(
            AnalyticsSeriesPoint(
                label=day.strftime("%a"),
                date=day.isoformat(),
                calls=len(day_calls),
                bookings=len(day_bookings),
                leads=sum(1 for c in day_calls if c.appointment_booked),
            )
        )

    return AnalyticsSummary(
        range=range_key,
        from_at=start,
        to_at=appointment_end,
        calls_today=calls_today,
        calls_total=len(calls),
        bookings=booked,
        conversion_rate=round(conversion, 4),
        average_duration_seconds=round(avg_duration, 1),
        missed_calls=missed,
        transfers=transfers,
        ai_resolution_rate=round(ai_resolution, 4),
        booking_funnel=AnalyticsFunnel(
            calls=len(calls),
            interested=interested,
            booked=booked,
            completed=completed,
            cancelled=cancelled,
        ),
        lead_sources=lead_sources,
        series=series,
    )
