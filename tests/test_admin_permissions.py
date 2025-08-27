import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, TEST_USERS


@pytest.mark.e2e
@pytest.mark.run(order=10)
@pytest.mark.asyncio
async def test_admin_user_permissions():
    """Test that Admin users have read, create, update, and delete permissions for user management operations."""

    admin_user = TEST_USERS["admin"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        admin_login_data = {
            "username": admin_user["email"],
            "password": admin_user["password"],
        }
        admin_resp = await ac.post("/auth/login", data=admin_login_data)
        assert admin_resp.status_code == 200, f"Admin login failed: {admin_resp.text}"
        admin_token = admin_resp.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        me_resp = await ac.get("/users/me", headers=admin_headers)
        assert (
            me_resp.status_code == 200
        ), f"Admin user should be able to access own data: {me_resp.text}"
        me_data = me_resp.json()
        assert me_data["username"] == admin_user["username"]
        assert me_data["email"] == admin_user["email"]

        list_resp = await ac.get("/users/", headers=admin_headers)
        assert (
            list_resp.status_code == 200
        ), f"Admin user should be able to list users: {list_resp.text}"
        users_response = list_resp.json()
        assert (
            isinstance(users_response, dict) and "data" in users_response
        ), "Response should be a paginated dictionary"
        users = users_response["data"]
        assert isinstance(users, list), "Response should contain a list of users"

        other_user = None
        for user in users:
            if (
                user["id"] != me_data["id"]
                and user.get("role", {}).get("name") != "Super-Admin"
            ):
                other_user = user
                break

        assert other_user is not None, "Should find another user to test with"
        get_user_resp = await ac.get(
            f"/users/{other_user['id']}", headers=admin_headers
        )
        assert (
            get_user_resp.status_code == 200
        ), f"Admin user should be able to read other users: {get_user_resp.text}"
        user_data = get_user_resp.json()
        assert user_data["id"] == other_user["id"]

        search_resp = await ac.get("/users/?search=test", headers=admin_headers)
        assert (
            search_resp.status_code == 200
        ), f"Admin user should be able to search users: {search_resp.text}"
        search_results = search_resp.json()
        assert (
            isinstance(search_results, dict) and "data" in search_results
        ), "Search response should be a paginated dictionary"
        assert isinstance(
            search_results["data"], list
        ), "Search response should contain a list"

        # Test that admin can create users (create permission)
        new_user_data = {
            "username": "new_admin_user",
            "email": "new_admin_user@example.com",
            "password": "password123",
            "role_id": 6,  # Observer role
        }
        create_user_resp = await ac.post(
            "/users/", json=new_user_data, headers=admin_headers
        )
        assert (
            create_user_resp.status_code == 201
        ), f"Admin user should be able to create users: {create_user_resp.text}"
        created_user = create_user_resp.json()
        assert created_user["username"] == "new_admin_user"
        assert created_user["email"] == "new_admin_user@example.com"
        assert created_user["role"]["id"] == 6

        # Test that admin can update users (update permission)
        update_data = {"full_name": "Updated Admin Name"}
        update_resp = await ac.put(
            f"/users/{me_data['id']}", json=update_data, headers=admin_headers
        )
        assert (
            update_resp.status_code == 200
        ), f"Admin user should be able to update users: {update_resp.text}"
        updated_user = update_resp.json()
        assert updated_user["full_name"] == "Updated Admin Name"

        # Test that admin can update other users too
        other_user_update_data = {"full_name": "Updated Other User Name"}
        other_update_resp = await ac.put(
            f"/users/{other_user['id']}",
            json=other_user_update_data,
            headers=admin_headers,
        )
        assert (
            other_update_resp.status_code == 200
        ), f"Admin user should be able to update other users: {other_update_resp.text}"
        other_updated_user = other_update_resp.json()
        assert other_updated_user["full_name"] == "Updated Other User Name"

        # Test that admin can delete users (delete permission) - soft delete
        print(f"deleting user {created_user['id']}")
        delete_resp = await ac.delete(
            f"/users/{created_user['id']}", headers=admin_headers
        )
        assert (
            delete_resp.status_code == 204
        ), f"Admin user should be able to delete users: {delete_resp.text}"

        # Test that admin can delete other users too (use a new disposable user)
        second_user_data = {
            "username": "new_admin_user_2",
            "email": "new_admin_user_2@example.com",
            "password": "password123",
            "role_id": 6,  # Observer role
        }
        create_second_resp = await ac.post(
            "/users/", json=second_user_data, headers=admin_headers
        )
        assert (
            create_second_resp.status_code == 201
        ), f"Admin should be able to create second user: {create_second_resp.text}"
        second_user = create_second_resp.json()

        delete_other_resp = await ac.delete(
            f"/users/{second_user['id']}", headers=admin_headers
        )
        assert (
            delete_other_resp.status_code == 204
        ), f"Admin user should be able to delete other users: {delete_other_resp.text}"

        # Test that admin cannot delete themselves
