from datetime import datetime, timedelta, timezone


async def test_create_appointment_returns_201_and_correct_ends_at(
    client,
    appointment_data,
):
    test_client = appointment_data["client"]
    test_master = appointment_data["master"]
    test_service = appointment_data["service"]

    starts_at = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)

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

    starts_at = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)

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

    first_starts_at = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)
    second_starts_at = datetime(2026, 11, 10, 10, 30, tzinfo=timezone.utc)

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
