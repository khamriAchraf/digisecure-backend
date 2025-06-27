import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, TEST_USERS


@pytest.mark.integration
@pytest.mark.run(order=5)
@pytest.mark.asyncio
async def test_self_service_user_permissions():
    """Test that Self-Service users have no permissions for user management operations."""

    # Get self-service user data from shared test data
    self_service_user = TEST_USERS["self_service"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # 1. Login as the self-service user
        self_service_login_data = {
            "username": self_service_user["email"],
            "password": self_service_user["password"],
        }
        self_service_resp = await ac.post("/auth/login", data=self_service_login_data)
        assert (
            self_service_resp.status_code == 200
        ), f"Self-service login failed: {self_service_resp.text}"
        self_service_token = self_service_resp.json()["access_token"]
        self_service_headers = {"Authorization": f"Bearer {self_service_token}"}

        # 2. Test that self-service user can access their own data (GET /me)
        me_resp = await ac.get("/users/me", headers=self_service_headers)
        assert (
            me_resp.status_code == 200
        ), f"Self-service user should be able to access own data: {me_resp.text}"
        me_data = me_resp.json()
        assert me_data["username"] == self_service_user["username"]
        assert me_data["email"] == self_service_user["email"]

        # 3. Test that self-service user is denied access to list users
        list_resp = await ac.get("/users/", headers=self_service_headers)
        assert (
            list_resp.status_code == 403
        ), f"Self-service user should be denied access to list users: {list_resp.text}"
        assert "Not allowed to list users" in list_resp.json()["detail"]

        # 4. Test that self-service user is denied access to get specific user
        get_user_resp = await ac.get(
            f"/users/{me_data['id']}", headers=self_service_headers
        )
        assert (
            get_user_resp.status_code == 403
        ), f"Self-service user should be denied access to get user: {get_user_resp.text}"
        assert "Not allowed to read users" in get_user_resp.json()["detail"]

        # 5. Test that self-service user is denied access to create users
        new_user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "roles": [6],  # Observer role
        }
        create_user_resp = await ac.post(
            "/users/", json=new_user_data, headers=self_service_headers
        )
        assert (
            create_user_resp.status_code == 403
        ), f"Self-service user should be denied access to create users: {create_user_resp.text}"
        assert "Not allowed to create users" in create_user_resp.json()["detail"]

        update_data = {"full_name": "Updated Name"}
        update_resp = await ac.put(
            f"/users/{me_data['id']}", json=update_data, headers=self_service_headers
        )
        assert (
            update_resp.status_code == 403
        ), f"Self-service user should be denied access to update users: {update_resp.text}"
        assert "Not allowed to read users" in update_resp.json()["detail"]

        # 7. Test that self-service user is denied access to delete users
        delete_resp = await ac.delete(
            f"/users/{me_data['id']}", headers=self_service_headers
        )
        assert (
            delete_resp.status_code == 403
        ), f"Self-service user should be denied access to delete users: {delete_resp.text}"
        assert "Not allowed to read users" in delete_resp.json()["detail"]

        # 8. Test that self-service user is denied access to search users
        search_resp = await ac.get(
            "/users/search/?query=test", headers=self_service_headers
        )
        assert (
            search_resp.status_code == 403
        ), f"Self-service user should be denied access to search users: {search_resp.text}"
        assert "Not allowed to search users" in search_resp.json()["detail"]
