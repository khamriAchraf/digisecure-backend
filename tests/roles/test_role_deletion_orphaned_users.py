import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN, TEST_PASSWORD


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_role_deletion_orphaned_users():
    """
    Test that deleting a role removes permissions from users assigned to that role.
    - Create a role with 'read' access to users
    - Create a user with that role
    - Verify the user can read users
    - Delete the role
    - Verify the user can no longer read users
    - Optionally, check the user's roles list is empty or updated
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # 1. Login as super-admin
        login_data = {
            "username": SUPER_ADMIN["email"],
            "password": SUPER_ADMIN["password"],
        }
        login_resp = await ac.post("/auth/login", data=login_data)
        assert (
            login_resp.status_code == 200
        ), f"Superadmin login failed: {login_resp.text}"
        super_token = login_resp.json()["access_token"]
        super_headers = {"Authorization": f"Bearer {super_token}"}

        # 2. Create a role with 'read' access to users
        role_data = {
            "name": "orphaned_role",
            "description": "Role for orphaned user test",
        }
        resp = await ac.post("/roles/", json=role_data, headers=super_headers)
        assert resp.status_code == 201, f"Failed to create role: {resp.text}"
        role_id = resp.json()["id"]

        # 3. Fetch permissions and find 'user:read'
        perm_resp = await ac.get("/roles/permissions", headers=super_headers)
        assert (
            perm_resp.status_code == 200
        ), f"Failed to fetch permissions: {perm_resp.text}"
        permissions = perm_resp.json()
        user_read_slug = next(
            (
                f"{p['resource']}:{p['action']}"
                for p in permissions
                if p["resource"] == "user" and p["action"] == "read"
            ),
            None,
        )
        assert user_read_slug, "user:read permission not found"

        # 4. Set role permissions to only 'user:read'
        update_data = {"permissions": [user_read_slug]}
        update_resp = await ac.put(
            f"/roles/{role_id}/permissions", json=update_data, headers=super_headers
        )
        assert (
            update_resp.status_code == 200
        ), f"Failed to set role permissions: {update_resp.text}"

        # 5. Create a user with that role
        new_user_email = "orphaned_user@example.com"
        new_user_data = {
            "username": "orphaned_user",
            "email": new_user_email,
            "password": TEST_PASSWORD,
            "roles": [role_id],
        }
        user_resp = await ac.post("/users/", json=new_user_data, headers=super_headers)
        assert user_resp.status_code == 201, f"Failed to create user: {user_resp.text}"

        # 6. Log in as the new user
        login_data = {"username": new_user_email, "password": TEST_PASSWORD}
        login_resp = await ac.post("/auth/login", data=login_data)
        assert (
            login_resp.status_code == 200
        ), f"New user login failed: {login_resp.text}"
        user_token = login_resp.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 7. Check that user can read users
        users_resp = await ac.get("/users/", headers=user_headers)
        assert (
            users_resp.status_code == 200
        ), f"User with 'read' should be able to list users: {users_resp.text}"

        # 8. Log back in as super-admin and delete the role
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )
        assert (
            login_resp.status_code == 200
        ), f"Superadmin re-login failed: {login_resp.text}"
        super_token = login_resp.json()["access_token"]
        super_headers = {"Authorization": f"Bearer {super_token}"}
        del_resp = await ac.delete(f"/roles/{role_id}", headers=super_headers)
        assert del_resp.status_code == 200, f"Failed to delete role: {del_resp.text}"

        # 9. Log in again as the new user
        login_resp = await ac.post("/auth/login", data=login_data)
        assert (
            login_resp.status_code == 200
        ), f"New user re-login failed: {login_resp.text}"
        user_token = login_resp.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 10. Check that user can no longer read users (should get 403)
        users_resp = await ac.get("/users/", headers=user_headers)
        assert (
            users_resp.status_code == 403
        ), f"User should not be able to list users after role deletion: {users_resp.text}"

        # 11. Optionally, check the user's roles list is empty or updated
        me_resp = await ac.get("/users/me", headers=user_headers)
        assert (
            me_resp.status_code == 200
        ), f"Failed to fetch user profile: {me_resp.text}"
        roles = me_resp.json().get("roles", [])
        assert (
            not roles
        ), f"User's roles should be empty after role deletion, got: {roles}"
