from datetime import datetime, timedelta, timezone, UTC

from app.models.appointment import AppointmentStatus
from app.models.master import Master
from app.models.master_service import MasterService


async def test_create_appointment_returns_201_and_correct_ends_at(
    client,
    appointment_data,
):
    test_client = appointment_data["client"]
    test_master = appointment_data["master"]
    test_service = appointment_data["service"]

    starts_at = datetime.now(UTC) + timedelta(days=1)

    response = await client.post(
        "/appointments",
        json={
            "client_id": str(test_client.id),
            "master_id": str(test_master.id),
            "service_id": str(test_service.id),
            "starts_at": starts_at.isoformat(),
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["client_id"] == str(test_client.id)
    assert data["master_id"] == str(test_master.id)
    assert data["service_id"] == str(test_service.id)

    expected_ends_at = starts_at + timedelta(minutes=test_service.duration_minutes)
    actual_ends_at = datetime.fromisoformat(data["ends_at"])

    assert actual_ends_at == expected_ends_at

async def test_create_same_time_appointment_returns_409(
        client,
        appointment_data,
):
    test_client = appointment_data["client"]
    test_master = appointment_data["master"]
    test_service = appointment_data["service"]

    starts_at = datetime.now(UTC) + timedelta(days=1)

    payload = {
        "client_id": str(test_client.id),
        "master_id": str(test_master.id),
        "service_id": str(test_service.id),
        "starts_at": starts_at.isoformat(),
    }

    first_response = await client.post(
        "/appointments",
        json=payload,
    )
    assert first_response.status_code == 201

    second_response = await client.post(
        "/appointments",
        json=payload,
    )
    assert second_response.status_code == 409

async def test_create_overlapping_appointment_returns_409(
        client,
        appointment_data,
):
    test_client = appointment_data["client"]
    test_master = appointment_data["master"]
    test_service = appointment_data["service"]

    first_starts_at = datetime.now(UTC) + timedelta(days=1)
    second_starts_at = datetime.now(UTC) + timedelta(days=1, minutes=30)

    payload = {
        "client_id": str(test_client.id),
        "master_id": str(test_master.id),
        "service_id": str(test_service.id),
        "starts_at": first_starts_at.isoformat(),
    }

    first_response = await client.post(
        "/appointments",
        json=payload,
    )
    assert first_response.status_code == 201

    payload.update({"starts_at": second_starts_at.isoformat()})

    second_response = await client.post(
        "/appointments",
        json=payload,
    )
    assert second_response.status_code == 409

async def test_same_time_appointment_after_cancelling_previous_appointment(
        client,
        appointment_data,
):
    starts_at = datetime.now(UTC) + timedelta(days=1)
    payload = {
        "client_id": str(appointment_data["client"].id),
        "master_id": str(appointment_data["master"].id),
        "service_id": str(appointment_data["service"].id),
        "starts_at": starts_at.isoformat(),
    }

    response = await client.post(
        "/appointments",
        json=payload,
    )
    assert response.status_code == 201

    appointment_id = response.json()["id"]

    response = await client.post(f"/appointments/{appointment_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    response = await client.post(
        "/appointments",
        json=payload,
    )
    assert response.status_code == 201

async def test_return_409_after_trying_to_cancel_cancelled_appointment(
        client,
        appointment_data,
):
    starts_at = datetime.now(UTC) + timedelta(days=1)
    response = await client.post(
        "/appointments",
        json={
            "client_id": str(appointment_data["client"].id),
            "master_id": str(appointment_data["master"].id),
            "service_id": str(appointment_data["service"].id),
            "starts_at": starts_at.isoformat(),
        },
    )
    assert response.status_code == 201

    appointment_id = response.json()["id"]

    response = await client.post(f"/appointments/{appointment_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    response = await client.post(f"/appointments/{appointment_id}/cancel")
    assert response.status_code == 409

async def test_get_appointments_returns_empty_list(client):
    response = await client.get("/appointments")
    assert response.status_code == 200
    assert response.json() == []

async def test_get_appointments_filters_by_master(
        client,
        appointment_data,
        db_session,
):
    second_master = Master(
        full_name="Second Master",
        phone_number="+79990000010",
    )
    db_session.add(second_master)
    db_session.flush()

    second_master_service = MasterService(
        master_id=second_master.id,
        service_id=appointment_data["service"].id,
    )
    db_session.add(second_master_service)
    db_session.flush()

    starts_at = datetime.now(UTC) + timedelta(days=1)
    response = await client.post(
        "/appointments",
        json={
            "client_id": str(appointment_data["client"].id),
            "master_id": str(appointment_data["master"].id),
            "service_id": str(appointment_data["service"].id),
            "starts_at": starts_at.isoformat(),
        },
    )
    assert response.status_code == 201

    response = await client.post(
        "/appointments",
        json={
            "client_id": str(appointment_data["client"].id),
            "master_id": str(second_master.id),
            "service_id": str(appointment_data["service"].id),
            "starts_at": starts_at.isoformat(),
        },
    )
    assert response.status_code == 201

    response = await client.get(
        "/appointments",
        params={"master_id": str(appointment_data["master"].id)},
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["master_id"] == str(appointment_data["master"].id)

async def test_get_appointments_filters_by_status_and_date(
        client,
        appointment_data,
):
    first_starts_at = datetime.now(UTC) + timedelta(days=1)
    response = await client.post(
        "/appointments",
        json={
            "client_id": str(appointment_data["client"].id),
            "master_id": str(appointment_data["master"].id),
            "service_id": str(appointment_data["service"].id),
            "starts_at": first_starts_at.isoformat(),
            "status": AppointmentStatus.CONFIRMED,
        },
    )
    assert response.status_code == 201

    second_starts_at = datetime.now(UTC) + timedelta(days=2)
    response = await client.post(
        "/appointments",
        json={
            "client_id": str(appointment_data["client"].id),
            "master_id": str(appointment_data["master"].id),
            "service_id": str(appointment_data["service"].id),
            "starts_at": second_starts_at.isoformat(),
        },
    )
    assert response.status_code == 201
    second_appointment_id = response.json()["id"]

    response = await client.get(
        "/appointments",
        params={
            "status": "scheduled",
            "date_from": second_starts_at.isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == second_appointment_id

async def test_starts_at_in_past_returns_422(
        client,
        appointment_data,
):
    past_date = datetime.now(UTC) - timedelta(days=1)

    response = await client.post(
        "/appointments",
        json={
            "client_id": str(appointment_data["client"].id),
            "master_id": str(appointment_data["master"].id),
            "service_id": str(appointment_data["service"].id),
            "starts_at": past_date.isoformat(),
        }
    )
    assert response.status_code == 422

async def test_appointment_to_service_that_master_dont_provide_returns_409(
        client,
        appointment_data,
        db_session,
):
    test_client = appointment_data["client"]
    test_master = Master(
        full_name="Second Master",
        phone_number="+79990000010",
    )
    db_session.add(test_master)
    db_session.flush()
    test_service = appointment_data["service"]

    starts_at = datetime.now(UTC) + timedelta(days=1)


    response = await client.post(
        "/appointments",
        json={
            "client_id": str(test_client.id),
            "master_id": str(test_master.id),
            "service_id": str(test_service.id),
            "starts_at": starts_at.isoformat(),
        },
    )

    assert response.status_code == 409
