import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_bulk_update_role_permissions_with_ids_and_slugs():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # Login as super-admin
        login_data = {
            "username": SUPER_ADMIN["email"],
            "password": SUPER_ADMIN["password"],
        }
        login_resp = await ac.post("/auth/login", data=login_data)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a new role
        role_data = {
            "name": "perm_update_role",
            "description": "role for perm update test",
        }
        resp = await ac.post("/roles/", json=role_data, headers=headers)
        assert resp.status_code == 201, f"Failed to create role: {resp.text}"
        role = resp.json()
        role_id = role["id"]

        # Fetch available permissions
        perm_resp = await ac.get("/roles/permissions", headers=headers)
        assert (
            perm_resp.status_code == 200
        ), f"Failed to fetch permissions: {perm_resp.text}"
        permissions = perm_resp.json()
        assert len(permissions) > 0, "No permissions found"

        # Use first two permissions for testing
        perm1 = permissions[0]
        perm2 = permissions[1] if len(permissions) > 1 else permissions[0]
        perm1_id = perm1["id"]
        perm2_slug = f"{perm2['resource']}:{perm2['action']}"

        # Bulk update with one ID and one slug
        update_data = {"permissions": [perm1_id, perm2_slug]}
        update_resp = await ac.put(
            f"/roles/{role_id}/permissions", json=update_data, headers=headers
        )
        assert update_resp.status_code == 200, f"Bulk update failed: {update_resp.text}"
        updated_role = update_resp.json()
        updated_perms = {
            (p["id"], p["resource"], p["action"]) for p in updated_role["permissions"]
        }
        assert (perm1["id"], perm1["resource"], perm1["action"]) in updated_perms
        assert (perm2["id"], perm2["resource"], perm2["action"]) in updated_perms

        # Bulk update with invalid slug
        bad_update = {"permissions": ["notaslug"]}
        bad_resp = await ac.put(
            f"/roles/{role_id}/permissions", json=bad_update, headers=headers
        )
        assert bad_resp.status_code == 400
        assert "slug must be in the form" in bad_resp.text

        # Bulk update with non-existent ID
        bad_update = {"permissions": [9999999]}
        bad_resp = await ac.put(
            f"/roles/{role_id}/permissions", json=bad_update, headers=headers
        )
        assert bad_resp.status_code == 404
        assert "Permission not found" in bad_resp.text

        # Bulk update with non-existent slug
        bad_update = {"permissions": ["fake:perm"]}
        bad_resp = await ac.put(
            f"/roles/{role_id}/permissions", json=bad_update, headers=headers
        )
        assert bad_resp.status_code == 404
        assert "Permission not found" in bad_resp.text
