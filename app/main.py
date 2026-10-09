from datetime import timedelta
from decimal import Decimal

from fastapi import FastAPI, Depends, HTTPException
from pydantic import EmailStr
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError

from app.db import get_session
from app.models.appointment import AppointmentCreate, Appointment
from app.models.client import Client
from app.models.master import Master
from app.models.service import Service

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/appointments", response_model=Appointment)
def create_appointment(data: AppointmentCreate, session: Session = Depends(get_session)):
    try:
        with session.begin():
            service = session.get(Service, data.service_id)

            if service is None:
                raise HTTPException(
                    status_code=404,
                    detail="Service not found",
                )

            client = session.get(Client, data.client_id)

            if client is None:
                raise HTTPException(
                    status_code=404,
                    detail="Client not found",
                )

            master = session.get(Master, data.master_id)

            if master is None:
                raise HTTPException(
                    status_code=404,
                    detail="Master not found",
                )

            ends_at = data.starts_at + timedelta(minutes=service.duration_minutes)

            appointment = Appointment(
                client_id=data.client_id,
                master_id=data.master_id,
                service_id=data.service_id,
                starts_at=data.starts_at,
                ends_at=ends_at,
                price=service.price
            )
            session.add(appointment)
        session.refresh(appointment)
        return appointment
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Appointment overlaps with existing appointment",
        )

@app.post("/services", response_model=Service)
def create_service(name: str, duration_minutes: int, price: Decimal, session: Session = Depends(get_session)):
    with session.begin():
        service = Service(name=name, duration_minutes=duration_minutes, price=price)
        session.add(service)
    session.refresh(service)
    return service

@app.post("/masters", response_model=Master)
def create_master(full_name: str, phone_number: str, session: Session = Depends(get_session)):
    with session.begin():
        master = Master(full_name=full_name, phone_number=phone_number)
        session.add(master)
    session.refresh(master)
    return master

@app.post("/clients", response_model=Client)
def create_client(full_name: str, phone_number: str, email: EmailStr, session: Session = Depends(get_session)):
    with session.begin():
        client = Client(full_name=full_name, phone_number=phone_number, email=email)
        session.add(client)
    session.refresh(client)
    return client
