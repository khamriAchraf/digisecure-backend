import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, TEST_USERS


@pytest.mark.e2e
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
        hotliner_rank = me_data["role"]["rank"]

        list_resp = await ac.get("/users/", headers=hotliner_headers)
        assert (
            list_resp.status_code == 200
        ), f"Hotliner user should be able to list users: {list_resp.text}"
        users_response = list_resp.json()
        assert (
            isinstance(users_response, dict) and "data" in users_response
        ), "Response should be a paginated dictionary"
        users = users_response["data"]
        assert isinstance(users, list), "Response should contain a list of users"

        readable_user = None
        forbidden_user = None
        for user in users:
            role = user.get("role") or {}
            rank = role.get("rank")
            if rank is None:
                continue
            if (
                user["id"] != me_data["id"]
                and rank >= hotliner_rank
                and readable_user is None
            ):
                readable_user = user
            if rank < hotliner_rank and forbidden_user is None:
                forbidden_user = user
            if readable_user and forbidden_user:
                break

        assert (
            readable_user is not None
        ), "Should find a user with same or lower privilege"
        get_user_resp_ok = await ac.get(
            f"/users/{readable_user['id']}", headers=hotliner_headers
        )
        assert (
            get_user_resp_ok.status_code == 200
        ), f"Hotliner should read users with same/lower privilege: {get_user_resp_ok.text}"
        user_data_ok = get_user_resp_ok.json()
        assert user_data_ok["id"] == readable_user["id"]

        assert (
            forbidden_user is not None
        ), "Should find a higher-privileged user to test access denial"
        get_user_resp_forbidden = await ac.get(
            f"/users/{forbidden_user['id']}", headers=hotliner_headers
        )
        assert get_user_resp_forbidden.status_code == 403, (
            f"Hotliner should be denied reading higher-privileged users: "
            f"{get_user_resp_forbidden.text}"
        )
        assert "hierarchy" in get_user_resp_forbidden.json()["detail"].lower()

        search_resp = await ac.get("/users/?search=test", headers=hotliner_headers)
        assert (
            search_resp.status_code == 200
        ), f"Hotliner user should be able to search users: {search_resp.text}"
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
            "role_id": 5,  # Hotliner role
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
