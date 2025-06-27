import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, TEST_USERS


@pytest.mark.integration
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
        users = list_resp.json()
        assert isinstance(users, list), "Response should be a list of users"

        other_user = None
        for user in users:
            if user["id"] != me_data["id"]:
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

        search_resp = await ac.get("/users/search/?query=test", headers=admin_headers)
        assert (
            search_resp.status_code == 200
        ), f"Admin user should be able to search users: {search_resp.text}"
        search_results = search_resp.json()
        assert isinstance(search_results, list), "Search response should be a list"

        # Test that admin can create users (create permission)
        new_user_data = {
            "username": "new_admin_user",
            "email": "new_admin_user@example.com",
            "password": "password123",
            "roles": [6],  # Observer role
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
        assert any(r["id"] == 6 for r in created_user["roles"])

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
        delete_resp = await ac.delete(
            f"/users/{created_user['id']}", headers=admin_headers
        )
        assert (
            delete_resp.status_code == 200
        ), f"Admin user should be able to delete users: {delete_resp.text}"
        deleted_user = delete_resp.json()
        assert deleted_user["status"] == "deleted", "User should be soft deleted"

        # Test that admin can delete other users too
        delete_other_resp = await ac.delete(
            f"/users/{other_user['id']}", headers=admin_headers
        )
        assert (
            delete_other_resp.status_code == 200
        ), f"Admin user should be able to delete other users: {delete_other_resp.text}"
        deleted_other_user = delete_other_resp.json()
        assert (
            deleted_other_user["status"] == "deleted"
        ), "Other user should be soft deleted"

        # Test that admin cannot delete themselves (this might be a business rule)
        # This depends on your implementation - some systems prevent self-deletion
        try:
            self_delete_resp = await ac.delete(
                f"/users/{me_data['id']}", headers=admin_headers
            )
            # If self-deletion is allowed, it should work
            if self_delete_resp.status_code == 200:
                deleted_self = self_delete_resp.json()
                assert (
                    deleted_self["status"] == "deleted"
                ), "Self should be soft deleted"
            else:
                # If self-deletion is not allowed, it should return an error
                assert self_delete_resp.status_code in [
                    400,
                    403,
                    422,
                ], f"Self-deletion should be prevented: {self_delete_resp.text}"
        except Exception as e:
            # Handle any unexpected errors
            assert False, f"Unexpected error during self-deletion test: {e}"
