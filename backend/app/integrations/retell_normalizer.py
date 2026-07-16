from datetime import UTC, datetime

from app.schemas.call import (
    AppointmentPayload,
    CallerPayload,
    RetellCallEndedPayload,
    RetellCallStartedPayload,
)


def _ms_to_dt(value: int | float | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=UTC)


def normalize_retell_webhook(payload: dict) -> tuple[str, dict]:
    event = payload.get("event", "")
    call = payload.get("call") or {}
    return event, call


def to_call_started(call: dict, business_id: str) -> RetellCallStartedPayload:
    return RetellCallStartedPayload(
        event_id=f"{call.get('call_id')}:call_started",
        business_id=business_id,
        retell_call_id=call["call_id"],
        direction=call.get("direction", "inbound"),
        started_at=_ms_to_dt(call.get("start_timestamp")) or datetime.now(UTC),
        caller_phone=call.get("from_number"),
    )


def to_call_ended(call: dict, business_id: str) -> RetellCallEndedPayload:
    analysis = call.get("call_analysis") or {}
    dynamic = call.get("retell_llm_dynamic_variables") or {}
    custom = call.get("custom_analysis_data") or {}
    appointment_payload = None
    appointment_data = custom.get("appointment") or dynamic.get("appointment")
    if isinstance(appointment_data, dict):
        appointment_payload = AppointmentPayload(
            cal_event_id=appointment_data.get("cal_event_id"),
            service=appointment_data.get("service") or "Appointment",
            start_time=datetime.fromisoformat(
                str(appointment_data["start_time"]).replace("Z", "+00:00")
            ),
            end_time=datetime.fromisoformat(
                str(appointment_data.get("end_time", appointment_data["start_time"])).replace(
                    "Z", "+00:00"
                )
            ),
            status=appointment_data.get("status", "booked"),
        )

    return RetellCallEndedPayload(
        event_id=f"{call.get('call_id')}:{call.get('disconnection_reason', 'ended')}",
        business_id=business_id,
        retell_call_id=call["call_id"],
        direction=call.get("direction", "inbound"),
        started_at=_ms_to_dt(call.get("start_timestamp")) or datetime.now(UTC),
        ended_at=_ms_to_dt(call.get("end_timestamp")) or datetime.now(UTC),
        transcript=call.get("transcript") or "",
        recording_url=call.get("recording_url"),
        caller=CallerPayload(
            name=dynamic.get("customer_name") or dynamic.get("name"),
            phone=call.get("from_number") or "unknown",
            email=dynamic.get("email"),
        ),
        intent=analysis.get("user_intent") or custom.get("intent"),
        urgency=custom.get("urgency") or analysis.get("urgency") or "normal",
        outcome=custom.get("outcome") or call.get("disconnection_reason") or "completed",
        summary=analysis.get("call_summary"),
        requested_service=custom.get("requested_service") or dynamic.get("service"),
        appointment=appointment_payload,
    )
