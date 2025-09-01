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
        # Capture observer rank for hierarchy checks (lower rank = more privileged)
        observer_rank = me_data["role"]["rank"]

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

        # Find a user with same or lower privilege (rank >= observer_rank) → should be readable
        readable_user = None
        # Find a user with higher privilege (rank < observer_rank) → should be forbidden
        forbidden_user = None
        for user in users:
            # Ensure role is present in the response
            role = user.get("role") or {}
            rank = role.get("rank")
            if rank is None:
                continue
            if (
                user["id"] != me_data["id"]
                and rank >= observer_rank
                and readable_user is None
            ):
                readable_user = user
            if rank < observer_rank and forbidden_user is None:
                forbidden_user = user
            if readable_user and forbidden_user:
                break

        assert (
            readable_user is not None
        ), "Should find a user with same or lower privilege"
        get_user_resp_ok = await ac.get(
            f"/users/{readable_user['id']}", headers=observer_headers
        )
        assert (
            get_user_resp_ok.status_code == 200
        ), f"Observer should read users with same/lower privilege: {get_user_resp_ok.text}"
        user_data_ok = get_user_resp_ok.json()
        assert user_data_ok["id"] == readable_user["id"]

        assert (
            forbidden_user is not None
        ), "Should find a higher-privileged user to test access denial"
        get_user_resp_forbidden = await ac.get(
            f"/users/{forbidden_user['id']}", headers=observer_headers
        )
        assert get_user_resp_forbidden.status_code == 403, (
            f"Observer should be denied reading higher-privileged users: "
            f"{get_user_resp_forbidden.text}"
        )
        assert "hierarchy" in get_user_resp_forbidden.json()["detail"].lower()

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
