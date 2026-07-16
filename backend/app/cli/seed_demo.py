"""Seed a realistic demo tenant for dashboards and demos."""

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


def seed_demo(*, reset: bool = False) -> str:
    db = SessionLocal()
    try:
        business = db.scalar(select(Business).where(Business.name == "Alamo Dental Demo"))
        if business and reset:
            db.delete(business)
            db.commit()
            business = None
        if business is None:
            business = Business(
                name="Alamo Dental Demo",
                industry="dental",
                phone_number="+12105551000",
                forwarding_number="+12105551099",
                timezone="America/Chicago",
                business_hours={"mon_fri": "08:00-17:00"},
                service_area="San Antonio metro",
            )
            db.add(business)
            db.flush()

        owner = db.scalar(select(User).where(User.email == "owner@alamodental-demo.example"))
        if owner is None:
            owner = User(
                business_id=business.id,
                name="Jordan Owner",
                email="owner@alamodental-demo.example",
                password_hash=hash_password("DemoPass123!"),
                role=UserRole.owner,
                email_verified_at=datetime.now(UTC),
            )
            db.add(owner)

        agent = db.scalar(
            select(VoiceAgent).where(
                VoiceAgent.business_id == business.id,
                VoiceAgent.retell_agent_id == "agent-alamo-demo",
            )
        )
        if agent is None:
            db.add(
                VoiceAgent(
                    business_id=business.id,
                    retell_agent_id="agent-alamo-demo",
                    retell_agent_name="Alamo_Front_Desk",
                    name="Front Desk",
                    greeting="Thanks for calling Alamo Dental. How can I help you today?",
                    system_prompt=(
                        "You are a professional dental receptionist. Qualify callers, "
                        "answer FAQs, and book appointments when confirmed."
                    ),
                    voice="nova",
                    temperature=0.4,
                    transfer_number="+12105551099",
                    transfer_rules="Transfer emergencies and billing disputes to the front desk.",
                    active=True,
                )
            )

        kb_specs = [
            ("hours", "What are your hours?", "We are open Monday through Friday, 8am to 5pm."),
            ("insurance", "Do you accept insurance?", "Yes, we accept most major PPO plans."),
            ("parking", "Is parking available?", "Free parking is available behind the clinic."),
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
                "Maria Lopez",
                "+12105550101",
                "maria.lopez@example.com",
                "customer",
                ["cleaning", "vip"],
            ),
            ("Sam Patel", "+12105550102", "sam.patel@example.com", "lead", ["new-patient"]),
            ("Riley Chen", "+12105550103", "riley.chen@example.com", "customer", ["urgent"]),
        ]
        callers: list[Caller] = []
        for name, phone, email, status, tags in callers_spec:
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
                    notes="Seeded demo customer",
                )
                db.add(caller)
                db.flush()
            callers.append(caller)

        now = datetime.now(UTC).replace(microsecond=0)
        call_specs = [
            (
                callers[0],
                "demo-call-1",
                "book_appointment",
                "positive",
                "appointment_booked",
                True,
                "Caller requested a cleaning next week and confirmed Tuesday morning.",
                "Agent: Thanks for calling Alamo Dental.\nCaller: I need a cleaning next week.\nAgent: I can offer Tuesday at 10.\nCaller: That works.",
            ),
            (
                callers[1],
                "demo-call-2",
                "pricing",
                "neutral",
                "completed",
                False,
                "Caller asked about new-patient exam pricing and will call back.",
                "Agent: How can I help?\nCaller: What does a new patient exam cost?\nAgent: Exams start at $99.",
            ),
            (
                callers[2],
                "demo-call-3",
                "urgent",
                "negative",
                "transferred",
                False,
                "Caller reported tooth pain; transferred to the front desk.",
                "Caller: I have sharp pain on the lower left.\nAgent: I am transferring you to our front desk now.",
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
            started = now - timedelta(days=idx, hours=2)
            call = Call(
                business_id=business.id,
                caller_id=caller.id,
                retell_call_id=retell_id,
                direction="inbound",
                started_at=started,
                ended_at=started + timedelta(minutes=3 + idx),
                duration_seconds=180 + idx * 40,
                transcript=transcript,
                summary=summary,
                intent=intent,
                urgency="urgent" if intent == "urgent" else "normal",
                outcome=outcome,
                sentiment=sentiment,
                appointment_booked=booked,
            )
            db.add(call)
            db.flush()
            if booked:
                db.add(
                    Appointment(
                        business_id=business.id,
                        caller_id=caller.id,
                        call_id=call.id,
                        cal_event_id=f"demo-cal-{idx}",
                        service="Dental cleaning",
                        start_time=now + timedelta(days=2, hours=10),
                        end_time=now + timedelta(days=2, hours=11),
                        status="booked",
                    )
                )

        db.commit()
        return business.id
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed SignalFlow demo tenant")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate demo business")
    args = parser.parse_args()
    business_id = seed_demo(reset=args.reset)
    print(f"Demo business ready: {business_id}")
    print("Login: owner@alamodental-demo.example / DemoPass123!")


if __name__ == "__main__":
    main()
