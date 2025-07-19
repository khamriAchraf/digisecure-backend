import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, TEST_USERS


@pytest.mark.e2e
@pytest.mark.run(order=6)
@pytest.mark.asyncio
async def test_observer_user_permissions():
    """Test that Observer users have read-only permissions for user management operations."""

    observer_user = TEST_USERS["observer"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        observer_login_data = {
            "username": observer_user["email"],
            "password": observer_user["password"],
        }
        observer_resp = await ac.post("/auth/login", data=observer_login_data)
        assert (
            observer_resp.status_code == 200
        ), f"Observer login failed: {observer_resp.text}"
        observer_token = observer_resp.json()["access_token"]
        observer_headers = {"Authorization": f"Bearer {observer_token}"}

        me_resp = await ac.get("/users/me", headers=observer_headers)
        assert (
            me_resp.status_code == 200
        ), f"Observer user should be able to access own data: {me_resp.text}"
        me_data = me_resp.json()
        assert me_data["username"] == observer_user["username"]
        assert me_data["email"] == observer_user["email"]

        list_resp = await ac.get("/users/", headers=observer_headers)
        assert (
            list_resp.status_code == 200
        ), f"Observer user should be able to list users: {list_resp.text}"
        users_response = list_resp.json()
        assert (
            isinstance(users_response, dict) and "data" in users_response
        ), "Response should be a paginated dictionary"
        users = users_response["data"]
        assert isinstance(users, list), "Response should contain a list of users"

        other_user = None
        for user in users:
            if user["id"] != me_data["id"]:
                other_user = user
                break

        assert other_user is not None, "Should find another user to test with"
        get_user_resp = await ac.get(
            f"/users/{other_user['id']}", headers=observer_headers
        )
        assert (
            get_user_resp.status_code == 200
        ), f"Observer user should be able to read other users: {get_user_resp.text}"
        user_data = get_user_resp.json()
        assert user_data["id"] == other_user["id"]

        search_resp = await ac.get("/users/?search=test", headers=observer_headers)
        assert (
            search_resp.status_code == 200
        ), f"Observer user should be able to search users: {search_resp.text}"
        search_results = search_resp.json()
        assert (
            isinstance(search_results, dict) and "data" in search_results
        ), "Search response should be a paginated dictionary"
        assert isinstance(
            search_results["data"], list
        ), "Search response should contain a list"

        new_user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "role_id": 6,
        }
        create_user_resp = await ac.post(
            "/users/", json=new_user_data, headers=observer_headers
        )
        assert (
            create_user_resp.status_code == 403
        ), f"Observer user should be denied access to create users: {create_user_resp.text}"
        assert "Not allowed to create users" in create_user_resp.json()["detail"]

        # 7. Test that observer user is denied access to update users
        update_data = {"full_name": "Updated Name"}
        update_resp = await ac.put(
            f"/users/{me_data['id']}", json=update_data, headers=observer_headers
        )
        assert (
            update_resp.status_code == 403
        ), f"Observer user should be denied access to update users: {update_resp.text}"
        assert "Not allowed to update users" in update_resp.json()["detail"]

        # 8. Test that observer user is denied access to delete users
        delete_resp = await ac.delete(
            f"/users/{me_data['id']}", headers=observer_headers
        )
        assert (
            delete_resp.status_code == 403
        ), f"Observer user should be denied access to delete users: {delete_resp.text}"
        assert "Not allowed to delete users" in delete_resp.json()["detail"]
