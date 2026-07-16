"""CSV export endpoints for closed-beta admin tools."""

from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import assert_tenant_access, require_business_admin
from app.db.session import get_db
from app.models import Appointment, Call, Caller

router = APIRouter(tags=["exports"])


def _csv_response(filename: str, rows: list[list[str]]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    payload = buffer.getvalue()
    return StreamingResponse(
        iter([payload]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _iso(value: datetime | None) -> str:
    return value.isoformat() if value else ""


@router.get("/api/businesses/{business_id}/exports/customers.csv")
def export_customers(
    business_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_admin),
):
    assert_tenant_access(tenant_id, business_id)
    callers = list(
        db.scalars(
            select(Caller).where(Caller.business_id == business_id).order_by(Caller.created_at)
        )
    )
    rows = [["id", "name", "phone", "email", "status", "tags", "notes", "created_at"]]
    for caller in callers:
        tags = ",".join(caller.tags or [])
        rows.append(
            [
                caller.id,
                caller.name or "",
                caller.phone,
                caller.email or "",
                caller.status,
                tags,
                (caller.notes or "").replace("\n", " "),
                _iso(caller.created_at),
            ]
        )
    return _csv_response("customers.csv", rows)


@router.get("/api/businesses/{business_id}/exports/appointments.csv")
def export_appointments(
    business_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_admin),
):
    assert_tenant_access(tenant_id, business_id)
    appointments = list(
        db.scalars(
            select(Appointment)
            .where(Appointment.business_id == business_id)
            .order_by(Appointment.start_time)
        )
    )
    rows = [
        [
            "id",
            "caller_id",
            "call_id",
            "cal_event_id",
            "service",
            "start_time",
            "end_time",
            "status",
            "created_at",
        ]
    ]
    for item in appointments:
        rows.append(
            [
                item.id,
                item.caller_id,
                item.call_id or "",
                item.cal_event_id or "",
                item.service,
                _iso(item.start_time),
                _iso(item.end_time),
                item.status,
                _iso(item.created_at),
            ]
        )
    return _csv_response("appointments.csv", rows)


@router.get("/api/businesses/{business_id}/exports/calls.csv")
def export_calls(
    business_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_admin),
):
    assert_tenant_access(tenant_id, business_id)
    calls = list(
        db.scalars(
            select(Call).where(Call.business_id == business_id).order_by(Call.started_at.desc())
        )
    )
    rows = [
        [
            "id",
            "caller_id",
            "retell_call_id",
            "direction",
            "started_at",
            "ended_at",
            "duration_seconds",
            "intent",
            "urgency",
            "outcome",
            "sentiment",
            "appointment_booked",
            "summary",
        ]
    ]
    for call in calls:
        rows.append(
            [
                call.id,
                call.caller_id or "",
                call.retell_call_id,
                call.direction,
                _iso(call.started_at),
                _iso(call.ended_at),
                str(call.duration_seconds or ""),
                call.intent or "",
                call.urgency or "",
                call.outcome or "",
                call.sentiment or "",
                "true" if call.appointment_booked else "false",
                (call.summary or "").replace("\n", " "),
            ]
        )
    return _csv_response("calls.csv", rows)
