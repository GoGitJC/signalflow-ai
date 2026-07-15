from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Appointment, Business, Call, Caller
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentUpdate

router = APIRouter(tags=["appointments"])


@router.get("/api/businesses/{business_id}/appointments", response_model=list[AppointmentRead])
def list_appointments(business_id: str, db: Session = Depends(get_db)):
    if not db.get(Business, business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    stmt = (
        select(Appointment)
        .where(Appointment.business_id == business_id)
        .order_by(desc(Appointment.start_time))
    )
    return list(db.scalars(stmt))


@router.post("/api/appointments", response_model=AppointmentRead, status_code=201)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    if not db.get(Business, payload.business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    caller = db.scalar(
        select(Caller).where(
            Caller.id == payload.caller_id, Caller.business_id == payload.business_id
        )
    )
    if not caller:
        raise HTTPException(status_code=404, detail="Caller not found for business")
    if payload.call_id:
        call = db.scalar(
            select(Call).where(Call.id == payload.call_id, Call.business_id == payload.business_id)
        )
        if not call:
            raise HTTPException(status_code=404, detail="Call not found for business")
    appointment = Appointment(**payload.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.patch("/api/appointments/{appointment_id}", response_model=AppointmentRead)
def update_appointment(
    appointment_id: str,
    business_id: str,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
):
    appointment = db.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id, Appointment.business_id == business_id
        )
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)
    db.commit()
    db.refresh(appointment)
    return appointment
