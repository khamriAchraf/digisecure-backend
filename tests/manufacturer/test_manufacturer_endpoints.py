import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN, TEST_USERS

MANUFACTURER_BASE = {
    "name": "test_manufacturer",
}


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_manufacturer_crud_as_super_admin():
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

        # Create manufacturer
        resp = await ac.post(
            "/reference_data/manufacturers/", json=MANUFACTURER_BASE, headers=headers
        )
        assert resp.status_code == 201, f"Failed to create manufacturer: {resp.text}"
        manufacturer = resp.json()
        manufacturer_id = manufacturer["id"]
        assert manufacturer["name"] == MANUFACTURER_BASE["name"]

        # Duplicate manufacturer name
        resp = await ac.post(
            "/reference_data/manufacturers/", json=MANUFACTURER_BASE, headers=headers
        )
        assert resp.status_code == 409, "Should not allow duplicate manufacturer name"

        # Missing required field
        bad_manufacturer = {}
        resp = await ac.post(
            "/reference_data/manufacturers/", json=bad_manufacturer, headers=headers
        )
        assert resp.status_code == 422

        # List manufacturers
        resp = await ac.get("/reference_data/manufacturers/", headers=headers)
        assert resp.status_code == 200
        assert any(m["id"] == manufacturer_id for m in resp.json()["data"])

        # Get manufacturer by id
        resp = await ac.get(
            f"/reference_data/manufacturers/{manufacturer_id}", headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == manufacturer_id

        # Update manufacturer
        update_data = {"name": "updated_manufacturer_name"}
        resp = await ac.put(
            f"/reference_data/manufacturers/{manufacturer_id}",
            json=update_data,
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "updated_manufacturer_name"

        # Delete manufacturer
        resp = await ac.delete(
            f"/reference_data/manufacturers/{manufacturer_id}", headers=headers
        )
        assert resp.status_code == 200 or resp.status_code == 204
        # Confirm deletion
        resp = await ac.get(
            f"/reference_data/manufacturers/{manufacturer_id}", headers=headers
        )
        assert resp.status_code == 404


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_manufacturer_permissions_for_non_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        login_data = {
            "username": TEST_USERS["observer"]["email"],
            "password": TEST_USERS["observer"]["password"],
        }
        login_resp = await ac.post("/auth/login", data=login_data)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to create manufacturer
        resp = await ac.post(
            "/reference_data/manufacturers/", json=MANUFACTURER_BASE, headers=headers
        )
        assert resp.status_code == 403

        # Try to update manufacturer (id 1)
        resp = await ac.put(
            "/reference_data/manufacturers/1",
            json={"name": "updated_name"},
            headers=headers,
        )
        assert resp.status_code == 403 or resp.status_code == 404

        # Try to delete manufacturer (id 1)
        resp = await ac.delete("/reference_data/manufacturers/1", headers=headers)
        assert resp.status_code == 403 or resp.status_code == 404

        # Try to list and get manufacturers
        resp = await ac.get("/reference_data/manufacturers/", headers=headers)
        assert resp.status_code == 200
        resp = await ac.get("/reference_data/manufacturers/1", headers=headers)
        assert resp.status_code in (200, 404)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_manufacturer_pagination():
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

        # Create multiple manufacturers
        manufacturer_ids = []
        for i in range(5):
            manufacturer_data = {"name": f"test_manufacturer_{i}"}
            resp = await ac.post(
                "/reference_data/manufacturers/",
                json=manufacturer_data,
                headers=headers,
            )
            assert resp.status_code == 201
            manufacturer_ids.append(resp.json()["id"])

        # Test pagination with limit
        resp = await ac.get(
            "/reference_data/manufacturers/?per_page=3", headers=headers
        )
        assert resp.status_code == 200
        manufacturers = resp.json()["data"]
        assert len(manufacturers) <= 3

        # Clean up - delete created manufacturers
        for manufacturer_id in manufacturer_ids:
            resp = await ac.delete(
                f"/reference_data/manufacturers/{manufacturer_id}", headers=headers
            )
            assert resp.status_code in (200, 204)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_manufacturer_not_found():
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

        # Try to get non-existent manufacturer
        resp = await ac.get("/reference_data/manufacturers/99999", headers=headers)
        assert resp.status_code == 404

        # Try to update non-existent manufacturer
        resp = await ac.put(
            "/reference_data/manufacturers/99999",
            json={"name": "new_name"},
            headers=headers,
        )
        assert resp.status_code == 404

        # Try to delete non-existent manufacturer
        resp = await ac.delete("/reference_data/manufacturers/99999", headers=headers)
        assert resp.status_code == 404
