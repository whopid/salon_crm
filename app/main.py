from datetime import timedelta, datetime, UTC
from decimal import Decimal
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import EmailStr
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.db import get_session
from app.models.appointment import AppointmentCreate, Appointment, AppointmentStatus
from app.models.client import Client
from app.models.master import Master
from app.models.master_service import MasterService
from app.models.service import Service

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/appointments", response_model=Appointment, status_code=201)
def create_appointment(data: AppointmentCreate, session: Session = Depends(get_session)):
    service = session.get(Service, data.service_id)

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )
    if not service.is_active:
        raise HTTPException(
            status_code=409,
            detail="Service is not active",
        )

    if data.starts_at < datetime.now(UTC):
        raise HTTPException(
            status_code=422,
            detail="starts_at cannot be in the past")

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

    if not master.is_active:
        raise HTTPException(
            status_code=409,
            detail="Master is not active",
        )

    master_service = session.get(MasterService, (master.id, service.id))
    if master_service is None:
        raise HTTPException(
            status_code=409,
            detail="Master does not provide this service",
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
    try:
        session.add(appointment)
        session.commit()
        session.refresh(appointment)
    except IntegrityError as e:
        session.rollback()
        if "appointments_no_overlap" in str(e.orig):
            raise HTTPException(409, "Appointment overlaps")
        raise HTTPException(409, "Integrity error")
    return appointment

@app.post("/services", response_model=Service, status_code=201)
def create_service(name: str, duration_minutes: int, price: Decimal, session: Session = Depends(get_session)):
    service = Service(name=name, duration_minutes=duration_minutes, price=price)
    session.add(service)
    session.commit()
    session.refresh(service)
    return service

@app.post("/masters", response_model=Master, status_code=201)
def create_master(full_name: str, phone_number: str, session: Session = Depends(get_session)):
    master = Master(full_name=full_name, phone_number=phone_number)
    session.add(master)
    session.commit()
    session.refresh(master)
    return master

@app.post("/clients", response_model=Client, status_code=201)
def create_client(full_name: str, phone_number: str, email: EmailStr, session: Session = Depends(get_session)):
    client = Client(full_name=full_name, phone_number=phone_number, email=email)
    session.add(client)
    session.commit()
    session.refresh(client)
    return client

@app.post("/appointments/{appointment_id}/cancel", response_model=Appointment)
def cancel_appointment(appointment_id: UUID, session: Session = Depends(get_session)):
    appointment = session.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )
    if appointment.status == AppointmentStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail="Appointment already completed",
        )
    if appointment.status == AppointmentStatus.CANCELLED:
        raise HTTPException(
            status_code=409,
            detail="Appointment already cancelled",
        )
    appointment.status = AppointmentStatus.CANCELLED
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return appointment

@app.get("/appointments", response_model=list[Appointment])
def list_appointments(
        master_id: UUID | None = None,
        client_id: UUID | None = None,
        status: AppointmentStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        session: Session = Depends(get_session)
):
    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise HTTPException(
            status_code=422,
            detail="date_from must be earlier than or equal to date_to",
        )

    statement = select(Appointment)
    if master_id is not None:
        statement = statement.where(Appointment.master_id == master_id)

    if client_id is not None:
        statement = statement.where(Appointment.client_id == client_id)

    if status is not None:
        statement = statement.where(Appointment.status == status)

    if date_from is not None:
        statement = statement.where(Appointment.starts_at >= date_from)

    if date_to is not None:
        statement = statement.where(Appointment.starts_at <= date_to)

    statement = (
        statement
        .order_by(Appointment.starts_at, Appointment.id)
        .offset(offset)
        .limit(limit)
    )

    appointments = session.exec(statement).all()

    return appointments

@app.get("/appointments/{appointment_id}", response_model=Appointment)
def read_appointment(appointment_id: UUID, session: Session = Depends(get_session)):
    appointment = session.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )
    return appointment

@app.get("/masters", response_model=list[Master])
def read_masters(is_active: bool | None = None, session: Session = Depends(get_session)):
    statement = select(Master)
    if is_active:
        statement = statement.where(Master.is_active)
    masters = session.exec(statement).all()
    return masters

@app.get("/services", response_model=list[Service])
def read_services(is_active: bool | None = None, session: Session = Depends(get_session)):
    statement = select(Service)
    if is_active:
        statement = statement.where(Service.is_active)
    services = session.exec(statement).all()
    return services

@app.get("/clients", response_model=list[Client])
def read_clients(session: Session = Depends(get_session)):
    statement = select(Client)
    clients = session.exec(statement).all()
    return clients

@app.post("/masters/{master_id}/services/{service_id}", response_model=MasterService, status_code=201)
def assign_service_to_master(
        master_id: UUID,
        service_id: UUID,
        session: Session = Depends(get_session),
):
    master = session.get(Master, master_id)
    if master is None:
        raise HTTPException(
            status_code=404,
            detail="Master not found",
        )
    if not master.is_active:
        raise HTTPException(
            status_code=409,
            detail="Master is not active",
        )

    service = session.get(Service, service_id)
    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )
    if not service.is_active:
        raise HTTPException(
            status_code=409,
            detail="Service is not active",
        )

    master_service = MasterService(master_id=master.id, service_id=service.id)
    try:
        session.add(master_service)
        session.commit()
        session.refresh(master_service)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not assign service to master",
        )
    return master_service

@app.delete("/masters/{master_id}/services/{service_id}", response_model=MasterService)
def unassign_service_from_master(
        master_id: UUID,
        service_id: UUID,
        session: Session = Depends(get_session),
):
    service = session.get(Service, service_id)
    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )
    master = session.get(Master, master_id)
    if master is None:
        raise HTTPException(
            status_code=404,
            detail="Master not found",
        )

    master_service = session.get(MasterService, (master_id, service_id))
    if master_service is None:
        raise HTTPException(
            status_code=404,
            detail="Service is not assigned to master",
        )
    session.delete(master_service)
    session.commit()
    return master_service

@app.get("/masters/{master_id}/services", response_model=list[Service])
def list_masters_services(master_id: UUID, session: Session = Depends(get_session)):
    master = session.get(Master, master_id)
    if master is None:
        raise HTTPException(
            status_code=404,
            detail="Master not found",
        )

    statement = (
        select(Service)
        .join(
            MasterService,
            MasterService.service_id == Service.id,
        )
        .where(MasterService.master_id == master_id)
    )

    services = session.exec(statement).all()
    return services
