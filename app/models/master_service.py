from uuid import UUID

from sqlmodel import SQLModel, Field


class MasterService(SQLModel, table=True):
    __tablename__ = "master_service"

    master_id: UUID = Field(foreign_key="master.id", primary_key=True)
    service_id: UUID = Field(foreign_key="service.id", primary_key=True)
