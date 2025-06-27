import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, TEST_USERS


@pytest.mark.integration
@pytest.mark.run(order=8)
@pytest.mark.asyncio
async def test_technician_user_permissions():
    """Test that Technician users have read and update permissions for user management operations."""

    technician_user = TEST_USERS["technician"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        technician_login_data = {
            "username": technician_user["email"],
            "password": technician_user["password"],
        }
        technician_resp = await ac.post("/auth/login", data=technician_login_data)
        assert (
            technician_resp.status_code == 200
        ), f"Technician login failed: {technician_resp.text}"
        technician_token = technician_resp.json()["access_token"]
        technician_headers = {"Authorization": f"Bearer {technician_token}"}

        me_resp = await ac.get("/users/me", headers=technician_headers)
        assert (
            me_resp.status_code == 200
        ), f"Technician user should be able to access own data: {me_resp.text}"
        me_data = me_resp.json()
        assert me_data["username"] == technician_user["username"]
        assert me_data["email"] == technician_user["email"]

        list_resp = await ac.get("/users/", headers=technician_headers)
        assert (
            list_resp.status_code == 200
        ), f"Technician user should be able to list users: {list_resp.text}"
        users = list_resp.json()
        assert isinstance(users, list), "Response should be a list of users"

        other_user = None
        for user in users:
            if user["id"] != me_data["id"]:
                other_user = user
                break

        assert other_user is not None, "Should find another user to test with"
        get_user_resp = await ac.get(
            f"/users/{other_user['id']}", headers=technician_headers
        )
        assert (
            get_user_resp.status_code == 200
        ), f"Technician user should be able to read other users: {get_user_resp.text}"
        user_data = get_user_resp.json()
        assert user_data["id"] == other_user["id"]

        search_resp = await ac.get(
            "/users/search/?query=test", headers=technician_headers
        )
        assert (
            search_resp.status_code == 200
        ), f"Technician user should be able to search users: {search_resp.text}"
        search_results = search_resp.json()
        assert isinstance(search_results, list), "Search response should be a list"

        # Test that technician can update users (update permission)
        update_data = {"full_name": "Updated Technician Name"}
        update_resp = await ac.put(
            f"/users/{me_data['id']}", json=update_data, headers=technician_headers
        )
        assert (
            update_resp.status_code == 200
        ), f"Technician user should be able to update users: {update_resp.text}"
        updated_user = update_resp.json()
        assert updated_user["full_name"] == "Updated Technician Name"

        # Test that technician can update other users too
        other_user_update_data = {"full_name": "Updated Other User Name"}
        other_update_resp = await ac.put(
            f"/users/{other_user['id']}",
            json=other_user_update_data,
            headers=technician_headers,
        )
        assert (
            other_update_resp.status_code == 200
        ), f"Technician user should be able to update other users: {other_update_resp.text}"
        other_updated_user = other_update_resp.json()
        assert other_updated_user["full_name"] == "Updated Other User Name"

        # Test that technician is denied access to create users
        new_user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "roles": [4],
        }
        create_user_resp = await ac.post(
            "/users/", json=new_user_data, headers=technician_headers
        )
        assert (
            create_user_resp.status_code == 403
        ), f"Technician user should be denied access to create users: {create_user_resp.text}"
        assert "Not allowed to create users" in create_user_resp.json()["detail"]

        # Test that technician is denied access to delete users
        delete_resp = await ac.delete(
            f"/users/{me_data['id']}", headers=technician_headers
        )
        assert (
            delete_resp.status_code == 403
        ), f"Technician user should be denied access to delete users: {delete_resp.text}"
        assert "Not allowed to delete users" in delete_resp.json()["detail"]
