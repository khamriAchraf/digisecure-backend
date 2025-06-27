import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, TEST_USERS


@pytest.mark.integration
@pytest.mark.run(order=7)
@pytest.mark.asyncio
async def test_hotliner_user_permissions():
    """Test that Hotliner users have read-only permissions for user management operations."""

    hotliner_user = TEST_USERS["hotliner"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        hotliner_login_data = {
            "username": hotliner_user["email"],
            "password": hotliner_user["password"],
        }
        hotliner_resp = await ac.post("/auth/login", data=hotliner_login_data)
        assert (
            hotliner_resp.status_code == 200
        ), f"Hotliner login failed: {hotliner_resp.text}"
        hotliner_token = hotliner_resp.json()["access_token"]
        hotliner_headers = {"Authorization": f"Bearer {hotliner_token}"}

        me_resp = await ac.get("/users/me", headers=hotliner_headers)
        assert (
            me_resp.status_code == 200
        ), f"Hotliner user should be able to access own data: {me_resp.text}"
        me_data = me_resp.json()
        assert me_data["username"] == hotliner_user["username"]
        assert me_data["email"] == hotliner_user["email"]

        list_resp = await ac.get("/users/", headers=hotliner_headers)
        assert (
            list_resp.status_code == 200
        ), f"Hotliner user should be able to list users: {list_resp.text}"
        users = list_resp.json()
        assert isinstance(users, list), "Response should be a list of users"

        other_user = None
        for user in users:
            if user["id"] != me_data["id"]:
                other_user = user
                break

        assert other_user is not None, "Should find another user to test with"
        get_user_resp = await ac.get(
            f"/users/{other_user['id']}", headers=hotliner_headers
        )
        assert (
            get_user_resp.status_code == 200
        ), f"Hotliner user should be able to read other users: {get_user_resp.text}"
        user_data = get_user_resp.json()
        assert user_data["id"] == other_user["id"]

        search_resp = await ac.get(
            "/users/search/?query=test", headers=hotliner_headers
        )
        assert (
            search_resp.status_code == 200
        ), f"Hotliner user should be able to search users: {search_resp.text}"
        search_results = search_resp.json()
        assert isinstance(search_results, list), "Search response should be a list"

        new_user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "roles": [5],  # Hotliner role
        }
        create_user_resp = await ac.post(
            "/users/", json=new_user_data, headers=hotliner_headers
        )
        assert (
            create_user_resp.status_code == 403
        ), f"Hotliner user should be denied access to create users: {create_user_resp.text}"
        assert "Not allowed to create users" in create_user_resp.json()["detail"]

        update_data = {"full_name": "Updated Name"}
        update_resp = await ac.put(
            f"/users/{me_data['id']}", json=update_data, headers=hotliner_headers
        )
        assert (
            update_resp.status_code == 403
        ), f"Hotliner user should be denied access to update users: {update_resp.text}"
        assert "Not allowed to update users" in update_resp.json()["detail"]

        delete_resp = await ac.delete(
            f"/users/{me_data['id']}", headers=hotliner_headers
        )
        assert (
            delete_resp.status_code == 403
        ), f"Hotliner user should be denied access to delete users: {delete_resp.text}"
        assert "Not allowed to delete users" in delete_resp.json()["detail"]
