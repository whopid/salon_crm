import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SAEnum


class AppointmentStatus(str, Enum):
    SCHEDULED = 'scheduled'
    CONFIRMED = 'confirmed'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class Appointment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    client_id: UUID = Field(foreign_key="client.id")
    master_id: UUID = Field(foreign_key="master.id")
    service_id: UUID = Field(foreign_key="service.id")
    starts_at: datetime.datetime
    ends_at: datetime.datetime
    status: AppointmentStatus = Field(
        default=AppointmentStatus.SCHEDULED,
        sa_column=Column(
            SAEnum(
                AppointmentStatus,
                values_callable=lambda enum: [item.value for item in enum],
                name="appointmentstatus",
            ),
            nullable=False,
        ),
    )
    price: Decimal = Field(max_digits=10, decimal_places=2)
    notes: str | None = None
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )

class AppointmentCreate(SQLModel):
    client_id: UUID
    master_id: UUID
    service_id: UUID
    starts_at: datetime.datetime
