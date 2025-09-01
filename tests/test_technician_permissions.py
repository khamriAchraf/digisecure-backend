import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, TEST_USERS


@pytest.mark.e2e
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
        technician_rank = me_data["role"]["rank"]

        list_resp = await ac.get("/users/", headers=technician_headers)
        assert (
            list_resp.status_code == 200
        ), f"Technician user should be able to list users: {list_resp.text}"
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
                and rank >= technician_rank
                and readable_user is None
            ):
                readable_user = user
            if rank < technician_rank and forbidden_user is None:
                forbidden_user = user
            if readable_user and forbidden_user:
                break

        assert (
            readable_user is not None
        ), "Should find a user with same or lower privilege"
        get_user_resp_ok = await ac.get(
            f"/users/{readable_user['id']}", headers=technician_headers
        )
        assert (
            get_user_resp_ok.status_code == 200
        ), f"Technician should read users with same/lower privilege: {get_user_resp_ok.text}"
        user_data_ok = get_user_resp_ok.json()
        assert user_data_ok["id"] == readable_user["id"]

        assert (
            forbidden_user is not None
        ), "Should find a higher-privileged user to test access denial"
        get_user_resp_forbidden = await ac.get(
            f"/users/{forbidden_user['id']}", headers=technician_headers
        )
        assert get_user_resp_forbidden.status_code == 403, (
            f"Technician should be denied reading higher-privileged users: "
            f"{get_user_resp_forbidden.text}"
        )
        assert "hierarchy" in get_user_resp_forbidden.json()["detail"].lower()

        search_resp = await ac.get("/users/?search=test", headers=technician_headers)
        assert (
            search_resp.status_code == 200
        ), f"Technician user should be able to search users: {search_resp.text}"
        search_results = search_resp.json()
        assert (
            isinstance(search_results, dict) and "data" in search_results
        ), "Search response should be a paginated dictionary"
        assert isinstance(
            search_results["data"], list
        ), "Search response should contain a list"

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
            f"/users/{readable_user['id']}",
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
            "role_id": 4,
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
