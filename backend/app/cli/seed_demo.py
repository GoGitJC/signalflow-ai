"""Seed a realistic HVAC demo tenant for closed-beta demos."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    Appointment,
    Business,
    Call,
    Caller,
    KnowledgeBaseEntry,
    User,
    UserRole,
    VoiceAgent,
)

DEMO_NAME = "Summit HVAC Pros"
DEMO_EMAIL = "owner@summithvac-demo.example"
DEMO_PASSWORD = "DemoPass123!"


def seed_demo(*, reset: bool = False) -> str:
    db = SessionLocal()
    try:
        business = db.scalar(select(Business).where(Business.name == DEMO_NAME))
        if business and reset:
            db.delete(business)
            db.commit()
            business = None
        if business is None:
            business = Business(
                name=DEMO_NAME,
                industry="hvac",
                phone_number="+15125552000",
                forwarding_number="+15125552099",
                timezone="America/Chicago",
                business_hours={"mon_fri": "07:00-18:00", "sat": "08:00-14:00"},
                service_area="Austin metro — HVAC repair, install, and maintenance",
            )
            db.add(business)
            db.flush()

        owner = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if owner is None:
            owner = User(
                business_id=business.id,
                name="Alex Rivera",
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                role=UserRole.owner,
                email_verified_at=datetime.now(UTC),
            )
            db.add(owner)

        agent = db.scalar(
            select(VoiceAgent).where(
                VoiceAgent.business_id == business.id,
                VoiceAgent.retell_agent_id == "agent-summit-hvac-demo",
            )
        )
        if agent is None:
            db.add(
                VoiceAgent(
                    business_id=business.id,
                    retell_agent_id="agent-summit-hvac-demo",
                    retell_agent_name="Summit_Front_Desk",
                    name="Front Desk",
                    greeting=(
                        "Thanks for calling Summit HVAC Pros. "
                        "Are you calling about a repair, maintenance, or a new install?"
                    ),
                    system_prompt=(
                        "You are a professional HVAC receptionist for Summit HVAC Pros. "
                        "Qualify emergency vs routine, capture address and preferred window, "
                        "answer FAQs, and book appointments when confirmed."
                    ),
                    voice="nova",
                    temperature=0.35,
                    transfer_number="+15125552099",
                    transfer_rules="Transfer gas smell, no-heat below freezing, and billing disputes.",
                    active=True,
                )
            )

        kb_specs = [
            (
                "hours",
                "What are your service hours?",
                "Monday–Friday 7am–6pm, Saturday 8am–2pm. Emergency dispatch is available after hours.",
            ),
            (
                "service_area",
                "Do you cover Round Rock?",
                "Yes — Austin, Round Rock, Cedar Park, and Pflugerville.",
            ),
            (
                "pricing",
                "How much is a diagnostic visit?",
                "Diagnostic visits start at $89 and are credited toward repair if you book the same day.",
            ),
            (
                "brands",
                "Which brands do you service?",
                "Carrier, Trane, Lennox, Goodman, Rheem, and most major residential brands.",
            ),
            (
                "maintenance",
                "Do you offer maintenance plans?",
                "Yes — Summit Care includes two seasonal tune-ups and priority scheduling.",
            ),
        ]
        for category, question, answer in kb_specs:
            exists = db.scalar(
                select(KnowledgeBaseEntry).where(
                    KnowledgeBaseEntry.business_id == business.id,
                    KnowledgeBaseEntry.question == question,
                )
            )
            if exists is None:
                db.add(
                    KnowledgeBaseEntry(
                        business_id=business.id,
                        category=category,
                        question=question,
                        answer=answer,
                        active=True,
                    )
                )

        callers_spec = [
            (
                "Jordan Blake",
                "+15125550111",
                "jordan.blake@example.com",
                "customer",
                ["ac-repair", "vip"],
                "Two-story home in South Austin; prefers morning windows.",
            ),
            (
                "Priya Nair",
                "+15125550112",
                "priya.nair@example.com",
                "lead",
                ["new-install"],
                "Interested in heat pump quote for 2020 build.",
            ),
            (
                "Marcus Webb",
                "+15125550113",
                "marcus.webb@example.com",
                "customer",
                ["emergency", "no-cool"],
                "Condo downtown; after-hours contact preferred.",
            ),
            (
                "Elena Soto",
                "+15125550114",
                "elena.soto@example.com",
                "customer",
                ["maintenance"],
                "Summit Care member since 2024.",
            ),
            (
                "Chris Nguyen",
                "+15125550115",
                "chris.nguyen@example.com",
                "lead",
                ["furnace"],
                "Asked about furnace inspection before winter.",
            ),
        ]
        callers: list[Caller] = []
        for name, phone, email, status, tags, notes in callers_spec:
            caller = db.scalar(
                select(Caller).where(Caller.business_id == business.id, Caller.phone == phone)
            )
            if caller is None:
                caller = Caller(
                    business_id=business.id,
                    name=name,
                    phone=phone,
                    email=email,
                    status=status,
                    tags=tags,
                    notes=notes,
                )
                db.add(caller)
                db.flush()
            callers.append(caller)

        now = datetime.now(UTC).replace(microsecond=0)
        call_specs = [
            (
                callers[0],
                "demo-hvac-call-1",
                "book_appointment",
                "positive",
                "appointment_booked",
                True,
                "Caller booked AC diagnostic for Thursday morning; confirmed South Austin address.",
                "Agent: Thanks for calling Summit HVAC Pros.\n"
                "Caller: My upstairs AC stopped cooling yesterday.\n"
                "Agent: I can schedule a diagnostic Thursday at 9am.\n"
                "Caller: Perfect, that works.",
            ),
            (
                callers[1],
                "demo-hvac-call-2",
                "new_install",
                "positive",
                "completed",
                False,
                "Lead requested heat pump install quote; sent to sales follow-up queue.",
                "Caller: We need a whole-home heat pump quote.\n"
                "Agent: I can have an estimator call you back today.\n"
                "Caller: Afternoons are best.",
            ),
            (
                callers[2],
                "demo-hvac-call-3",
                "emergency",
                "negative",
                "transferred",
                False,
                "No-cool emergency above 95°F; transferred to dispatch for same-day tech.",
                "Caller: It's 98 degrees and nothing is blowing cold.\n"
                "Agent: I'm transferring you to emergency dispatch now.",
            ),
            (
                callers[3],
                "demo-hvac-call-4",
                "maintenance",
                "positive",
                "appointment_booked",
                True,
                "Summit Care member booked fall furnace tune-up for next Tuesday.",
                "Caller: I'd like my fall maintenance visit.\n"
                "Agent: Tuesday at 1pm is open for furnace tune-up.\n"
                "Caller: Book it.",
            ),
            (
                callers[4],
                "demo-hvac-call-5",
                "pricing",
                "neutral",
                "completed",
                False,
                "Caller asked furnace inspection pricing; will decide after weekend.",
                "Caller: What does a furnace inspection cost?\n"
                "Agent: Inspections start at $129 before the heating season.",
            ),
        ]
        for idx, (
            caller,
            retell_id,
            intent,
            sentiment,
            outcome,
            booked,
            summary,
            transcript,
        ) in enumerate(call_specs):
            existing = db.scalar(select(Call).where(Call.retell_call_id == retell_id))
            if existing:
                continue
            started = now - timedelta(days=idx + 1, hours=3)
            call = Call(
                business_id=business.id,
                caller_id=caller.id,
                retell_call_id=retell_id,
                direction="inbound",
                started_at=started,
                ended_at=started + timedelta(minutes=4 + idx),
                duration_seconds=240 + idx * 35,
                transcript=transcript,
                summary=summary,
                intent=intent,
                urgency="urgent" if intent == "emergency" else "normal",
                outcome=outcome,
                sentiment=sentiment,
                appointment_booked=booked,
            )
            db.add(call)
            db.flush()
            if booked and idx == 0:
                db.add(
                    Appointment(
                        business_id=business.id,
                        caller_id=caller.id,
                        call_id=call.id,
                        cal_event_id=f"demo-hvac-cal-{idx}",
                        service="AC diagnostic visit",
                        start_time=now + timedelta(days=2, hours=9),
                        end_time=now + timedelta(days=2, hours=10),
                        status="booked",
                    )
                )
            if booked and idx == 3:
                db.add(
                    Appointment(
                        business_id=business.id,
                        caller_id=caller.id,
                        call_id=call.id,
                        cal_event_id=f"demo-hvac-cal-{idx}",
                        service="Furnace seasonal tune-up",
                        start_time=now + timedelta(days=5, hours=13),
                        end_time=now + timedelta(days=5, hours=14),
                        status="booked",
                    )
                )

        # Extra upcoming appointment without linked call for calendar density
        if not db.scalar(
            select(Appointment).where(Appointment.cal_event_id == "demo-hvac-cal-extra")
        ):
            db.add(
                Appointment(
                    business_id=business.id,
                    caller_id=callers[1].id,
                    call_id=None,
                    cal_event_id="demo-hvac-cal-extra",
                    service="Heat pump estimate",
                    start_time=now + timedelta(days=3, hours=15),
                    end_time=now + timedelta(days=3, hours=16),
                    status="booked",
                )
            )

        db.commit()
        return business.id
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Verideum HVAC demo tenant")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate demo business")
    args = parser.parse_args()
    business_id = seed_demo(reset=args.reset)
    print(f"Demo business ready: {business_id}")
    print(f"Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
