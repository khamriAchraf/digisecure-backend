import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN, TEST_PASSWORD


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_role_permission_escalation():
    """
    Test the escalation of permissions for a user role:
    - Create a role with only 'read' access to users
    - Create a user with that role
    - Verify the user can read users but cannot create roles
    - Escalate the role to allow 'create' on roles
    - Verify the user can now create roles
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

        # 2. Create a role with only 'read' access to users
        role_data = {
            "name": "escalation_role",
            "description": "Role for escalation test",
        }
        resp = await ac.post("/roles/", json=role_data, headers=super_headers)
        assert resp.status_code == 201, f"Failed to create role: {resp.text}"
        role_id = resp.json()["id"]

        # 3. Fetch permissions and find 'user:read' and 'role:create'
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
        role_create_slug = next(
            (
                f"{p['resource']}:{p['action']}"
                for p in permissions
                if p["resource"] == "role" and p["action"] == "create"
            ),
            None,
        )
        assert user_read_slug, "user:read permission not found"
        assert role_create_slug, "role:create permission not found"

        # 4. Set role permissions to only 'user:read'
        update_data = {"permissions": [user_read_slug]}
        update_resp = await ac.put(
            f"/roles/{role_id}/permissions", json=update_data, headers=super_headers
        )
        assert (
            update_resp.status_code == 200
        ), f"Failed to set role permissions: {update_resp.text}"

        # 5. Create a user with that role
        new_user_email = "escalation_user@example.com"
        new_user_data = {
            "username": "escalation_user",
            "email": new_user_email,
            "password": TEST_PASSWORD,
            "role_id": role_id,
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

        # 8. Check that user cannot create a new role
        new_role_data = {"name": "should_fail", "description": "should not be allowed"}
        create_role_resp = await ac.post(
            "/roles/", json=new_role_data, headers=user_headers
        )
        assert (
            create_role_resp.status_code == 403
        ), f"User should not be able to create roles: {create_role_resp.text}"

        # 9. Log back in as super-admin and escalate permissions
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
        update_data = {"permissions": [user_read_slug, role_create_slug]}
        update_resp = await ac.put(
            f"/roles/{role_id}/permissions", json=update_data, headers=super_headers
        )
        assert (
            update_resp.status_code == 200
        ), f"Failed to escalate role permissions: {update_resp.text}"

        # 10. Log in again as the new user
        login_resp = await ac.post("/auth/login", data=login_data)
        assert (
            login_resp.status_code == 200
        ), f"New user re-login failed: {login_resp.text}"
        user_token = login_resp.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 11. Check that user can now create a role
        new_role_data = {
            "name": "should_succeed",
            "description": "should be allowed now",
        }
        create_role_resp = await ac.post(
            "/roles/", json=new_role_data, headers=user_headers
        )
        assert (
            create_role_resp.status_code == 201
        ), f"User should now be able to create roles: {create_role_resp.text}"
