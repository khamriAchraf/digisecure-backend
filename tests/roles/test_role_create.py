import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN, TEST_USERS


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_roles_as_super_admin():
    # 1. Login as super-admin
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        login_data = {
            "username": SUPER_ADMIN["email"],
            "password": SUPER_ADMIN["password"],
        }
        login_resp = await ac.post("/auth/login", data=login_data)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # attempt to create a role
        role_data = {
            "name": "test_role",
            "description": "test_description",
        }
        resp = await ac.post("/roles/", json=role_data, headers=headers)
        assert resp.status_code == 201, f"Failed to create role: {resp.text}"

        # attemt to create a role with a name that already exists
        role_data = {
            "name": "test_role",
            "description": "test_description",
        }
        resp = await ac.post("/roles/", json=role_data, headers=headers)
        assert resp.status_code == 409, f"Role with name 'test_role' already exists."

        # attempt to create a role with incomplete data
        role_data = {
            "description": "test_description",
        }
        resp = await ac.post("/roles/", json=role_data, headers=headers)
        assert resp.status_code == 422, f"Failed to create role: {resp.text}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_users_without_permission():
    # 1. Login as super-admin
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        login_data = {
            "username": TEST_USERS["observer"]["email"],
            "password": TEST_USERS["observer"]["password"],
        }
        login_resp = await ac.post("/auth/login", data=login_data)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # attempt to create a role
        role_data = {
            "name": "test_role",
            "description": "test_description",
        }
        resp = await ac.post("/roles/", json=role_data, headers=headers)
        assert (
            resp.status_code == 403
        ), f"Observer should not be able to create roles: {resp.text}"
