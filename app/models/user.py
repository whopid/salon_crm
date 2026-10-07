import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SAEnum


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"

class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: EmailStr
    password_hash: str
    full_name: str
    role: UserRole = Field(
        default=UserRole.ADMIN,
        sa_column=Column(
            SAEnum(
                UserRole,
                values_callable=lambda enum: [item.value for item in enum],
                name="userrole",
            ),
            nullable=False,
        ),
    )
    is_active: bool = True
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
