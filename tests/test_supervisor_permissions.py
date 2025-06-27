import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, TEST_USERS


@pytest.mark.integration
@pytest.mark.run(order=9)
@pytest.mark.asyncio
async def test_supervisor_user_permissions():
    """Test that Supervisor users have read, create, and update permissions for user management operations."""

    supervisor_user = TEST_USERS["supervisor"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        supervisor_login_data = {
            "username": supervisor_user["email"],
            "password": supervisor_user["password"],
        }
        supervisor_resp = await ac.post("/auth/login", data=supervisor_login_data)
        assert (
            supervisor_resp.status_code == 200
        ), f"Supervisor login failed: {supervisor_resp.text}"
        supervisor_token = supervisor_resp.json()["access_token"]
        supervisor_headers = {"Authorization": f"Bearer {supervisor_token}"}

        me_resp = await ac.get("/users/me", headers=supervisor_headers)
        assert (
            me_resp.status_code == 200
        ), f"Supervisor user should be able to access own data: {me_resp.text}"
        me_data = me_resp.json()
        assert me_data["username"] == supervisor_user["username"]
        assert me_data["email"] == supervisor_user["email"]

        list_resp = await ac.get("/users/", headers=supervisor_headers)
        assert (
            list_resp.status_code == 200
        ), f"Supervisor user should be able to list users: {list_resp.text}"
        users = list_resp.json()
        assert isinstance(users, list), "Response should be a list of users"

        other_user = None
        for user in users:
            if user["id"] != me_data["id"]:
                other_user = user
                break

        assert other_user is not None, "Should find another user to test with"
        get_user_resp = await ac.get(
            f"/users/{other_user['id']}", headers=supervisor_headers
        )
        assert (
            get_user_resp.status_code == 200
        ), f"Supervisor user should be able to read other users: {get_user_resp.text}"
        user_data = get_user_resp.json()
        assert user_data["id"] == other_user["id"]

        search_resp = await ac.get(
            "/users/search/?query=test", headers=supervisor_headers
        )
        assert (
            search_resp.status_code == 200
        ), f"Supervisor user should be able to search users: {search_resp.text}"
        search_results = search_resp.json()
        assert isinstance(search_results, list), "Search response should be a list"

        # Test that supervisor can create users (create permission)
        new_user_data = {
            "username": "new_supervisor_user",
            "email": "new_supervisor_user@example.com",
            "password": "password123",
            "roles": [6],  # Observer role
        }
        create_user_resp = await ac.post(
            "/users/", json=new_user_data, headers=supervisor_headers
        )
        assert (
            create_user_resp.status_code == 201
        ), f"Supervisor user should be able to create users: {create_user_resp.text}"
        created_user = create_user_resp.json()
        assert created_user["username"] == "new_supervisor_user"
        assert created_user["email"] == "new_supervisor_user@example.com"
        assert any(r["id"] == 6 for r in created_user["roles"])

        # Test that supervisor can update users (update permission)
        update_data = {"full_name": "Updated Supervisor Name"}
        update_resp = await ac.put(
            f"/users/{me_data['id']}", json=update_data, headers=supervisor_headers
        )
        assert (
            update_resp.status_code == 200
        ), f"Supervisor user should be able to update users: {update_resp.text}"
        updated_user = update_resp.json()
        assert updated_user["full_name"] == "Updated Supervisor Name"

        # Test that supervisor can update other users too
        other_user_update_data = {"full_name": "Updated Other User Name"}
        other_update_resp = await ac.put(
            f"/users/{other_user['id']}",
            json=other_user_update_data,
            headers=supervisor_headers,
        )
        assert (
            other_update_resp.status_code == 200
        ), f"Supervisor user should be able to update other users: {other_update_resp.text}"
        other_updated_user = other_update_resp.json()
        assert other_updated_user["full_name"] == "Updated Other User Name"

        # Test that supervisor is denied access to delete users
        delete_resp = await ac.delete(
            f"/users/{me_data['id']}", headers=supervisor_headers
        )
        assert (
            delete_resp.status_code == 403
        ), f"Supervisor user should be denied access to delete users: {delete_resp.text}"
        assert "Not allowed to delete users" in delete_resp.json()["detail"]

        # Test that supervisor is denied access to delete other users
        delete_other_resp = await ac.delete(
            f"/users/{other_user['id']}", headers=supervisor_headers
        )
        assert (
            delete_other_resp.status_code == 403
        ), f"Supervisor user should be denied access to delete other users: {delete_other_resp.text}"
        assert "Not allowed to delete users" in delete_other_resp.json()["detail"]
