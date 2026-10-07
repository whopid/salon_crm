import datetime
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import SQLModel, Field


class Client(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    full_name: str
    phone_number: str
    email: EmailStr
    notes: str | None = None
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
