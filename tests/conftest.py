from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlmodel import Session

from app.db import get_session
from app.main import app
from app.models.client import Client
from app.models.master import Master
from app.models.master_service import MasterService
from app.models.service import Service
from env import TEST_DATABASE_URL


test_engine = create_engine(TEST_DATABASE_URL)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest_asyncio.fixture
async def client(db_session):
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def appointment_data(db_session):
    test_client = Client(
        full_name="Test Client",
        phone_number="+79990000001",
        email="test@example.com",
    )

    test_master = Master(
        full_name="Test Master",
        phone_number="+79990000002",
    )

    test_service = Service(
        name="Test Service",
        duration_minutes=60,
        price=Decimal("2500.00"),
    )

    db_session.add(test_client)
    db_session.add(test_master)
    db_session.add(test_service)
    db_session.flush()

    test_master_service = MasterService(
        master_id=test_master.id,
        service_id=test_service.id,
    )
    db_session.add(test_master_service)
    db_session.flush()

    return {
        "client": test_client,
        "master": test_master,
        "service": test_service,
    }
