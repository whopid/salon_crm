import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class Service(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    description: str | None = None
    duration_minutes: int
    price: Decimal = Field(max_digits=10, decimal_places=2)
    is_active: bool = True
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
