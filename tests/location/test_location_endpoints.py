import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN, TEST_USERS

LOCATION_BASE = {
    "name": "test_location",
    "postal_code": "12345",
    "building_number": "10A",
    "latitude": 40.7128,
    "altitude": 15.0,
    "comment": "Test location comment",
    "address": "123 Main St",
    "town": "Testville",
    "country": "Testland",
    "state": "Teststate",
    "room_number": "101",
    "longitude": -74.0060,
    "floor_number": "1",
}


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_location_crud_as_super_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # Login as super-admin
        login_data = {
            "username": SUPER_ADMIN["email"],
            "password": SUPER_ADMIN["password"],
        }
        login_resp = await ac.post("/auth/login", data=login_data)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create location
        resp = await ac.post(
            "/reference_data/locations/", json=LOCATION_BASE, headers=headers
        )
        assert resp.status_code == 201, f"Failed to create location: {resp.text}"
        location = resp.json()
        location_id = location["id"]
        assert location["name"] == LOCATION_BASE["name"]

        # Duplicate location name
        resp = await ac.post(
            "/reference_data/locations/", json=LOCATION_BASE, headers=headers
        )
        assert resp.status_code == 409, "Should not allow duplicate location name"

        # Missing required field
        bad_location = {"postal_code": "00000"}
        resp = await ac.post(
            "/reference_data/locations/", json=bad_location, headers=headers
        )
        assert resp.status_code == 422

        # List locations
        resp = await ac.get("/reference_data/locations/", headers=headers)
        assert resp.status_code == 200
        assert any(l["id"] == location_id for l in resp.json())

        # Get location by id
        resp = await ac.get(f"/reference_data/locations/{location_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == location_id

        # Update location
        update_data = {"comment": "Updated comment"}
        resp = await ac.put(
            f"/reference_data/locations/{location_id}",
            json=update_data,
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["comment"] == "Updated comment"

        # Delete location
        resp = await ac.delete(
            f"/reference_data/locations/{location_id}", headers=headers
        )
        assert resp.status_code == 200 or resp.status_code == 204
        # Confirm deletion
        resp = await ac.get(f"/reference_data/locations/{location_id}", headers=headers)
        assert resp.status_code == 404


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_location_permissions_for_non_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        login_data = {
            "username": TEST_USERS["observer"]["email"],
            "password": TEST_USERS["observer"]["password"],
        }
        login_resp = await ac.post("/auth/login", data=login_data)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to create location
        resp = await ac.post(
            "/reference_data/locations/", json=LOCATION_BASE, headers=headers
        )
        assert resp.status_code == 403

        # Try to update location (id 1)
        resp = await ac.put(
            "/reference_data/locations/1", json={"comment": "desc"}, headers=headers
        )
        assert resp.status_code == 403 or resp.status_code == 404

        # Try to delete location (id 1)
        resp = await ac.delete("/reference_data/locations/1", headers=headers)
        assert resp.status_code == 403 or resp.status_code == 404

        # Try to list and get locations
        resp = await ac.get("/reference_data/locations/", headers=headers)
        assert resp.status_code == 200
        resp = await ac.get("/reference_data/locations/1", headers=headers)
        assert resp.status_code in (200, 404)
