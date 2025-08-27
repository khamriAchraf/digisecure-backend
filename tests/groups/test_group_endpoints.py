import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN, TEST_USERS

GROUP_BASE = {
    "name": "test_group",
    "description": "A test group",
    "type": "org",
    "contain_users": True,
    "contain_items": True,
    "parent_id": None,
}


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_group_crud_as_super_admin():
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

        # Create group
        resp = await ac.post("/groups/", json=GROUP_BASE, headers=headers)
        assert resp.status_code == 201, f"Failed to create group: {resp.text}"
        group = resp.json()
        group_id = group["id"]
        assert group["name"] == GROUP_BASE["name"]

        # Duplicate group name
        resp = await ac.post("/groups/", json=GROUP_BASE, headers=headers)
        assert resp.status_code == 409, "Should not allow duplicate group name"

        # Missing required field
        bad_group = {"description": "desc"}
        resp = await ac.post("/groups/", json=bad_group, headers=headers)
        assert resp.status_code == 422

        # List groups
        resp = await ac.get("/groups/", headers=headers)
        assert resp.status_code == 200
        groups_data = resp.json()
        assert "data" in groups_data
        assert any(g["id"] == group_id for g in groups_data["data"])

        # Get group by id
        resp = await ac.get(f"/groups/{group_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == group_id

        # Update group
        update_data = {"description": "Updated description"}
        resp = await ac.put(f"/groups/{group_id}", json=update_data, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated description"

        # Add user to group
        user_id = 1  # Assuming super-admin user exists with id=1
        resp = await ac.post(f"/groups/{group_id}/users/{user_id}", headers=headers)
        assert resp.status_code == 200
        assert any(u["id"] == user_id for u in resp.json()["users"])

        # Remove user from group
        resp = await ac.delete(f"/groups/{group_id}/users/{user_id}", headers=headers)
        assert resp.status_code == 200
        assert all(u["id"] != user_id for u in resp.json()["users"])


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_group_permissions_for_non_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        login_data = {
            "username": TEST_USERS["observer"]["email"],
            "password": TEST_USERS["observer"]["password"],
        }
        login_resp = await ac.post("/auth/login", data=login_data)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to create group
        resp = await ac.post("/groups/", json=GROUP_BASE, headers=headers)
        assert resp.status_code == 403

        # Try to update group (id 1)
        resp = await ac.put("/groups/1", json={"description": "desc"}, headers=headers)
        assert resp.status_code == 403 or resp.status_code == 404

        # Try to add/remove user to/from group
        resp = await ac.post("/groups/1/users/1", headers=headers)
        assert resp.status_code == 403 or resp.status_code == 404
        resp = await ac.delete("/groups/1/users/1", headers=headers)
        assert resp.status_code == 403 or resp.status_code == 404

        resp = await ac.get("/groups/", headers=headers)
        assert resp.status_code == 200
        groups_data = resp.json()
        assert "data" in groups_data
        resp = await ac.get("/groups/1", headers=headers)
        assert resp.status_code in (200, 404)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_group_with_users():
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

        # Check if users exist first
        users_resp = await ac.get("/users/", headers=headers)
        assert users_resp.status_code == 200, f"Failed to get users: {users_resp.text}"
        users_data = users_resp.json()
        assert "data" in users_data
        users = users_data["data"]
        print(f"Available users: {[(u['id'], u['username']) for u in users]}")

        # Check if user ID 2 exists
        user_2_resp = await ac.get("/users/2", headers=headers)
        print(f"User 2 response: {user_2_resp.status_code} - {user_2_resp.text}")

        # Prepare group with users
        group_with_users = {
            "name": "group_with_users",
            "description": "Group with initial users",
            "type": "org",
            "contain_users": True,
            "contain_items": True,
            "comment": "Group with initial users",
            "parent_id": None,
            "user_ids": [1, 3],
        }
        resp = await ac.post(
            "/groups/with-users", json=group_with_users, headers=headers
        )
        assert (
            resp.status_code == 201
        ), f"Failed to create group with users: {resp.text}"
        group = resp.json()
        assert (
            group["name"] == group_with_users["name"]
        ), f"Group name mismatch: {group['name']} != {group_with_users['name']}"
        assert any(
            u["id"] == 1 for u in group["users"]
        ), f"User 1 not found in group: {group['users']}"
        assert any(
            u["id"] == 3 for u in group["users"]
        ), f"User 3 not found in group: {group['users']}"
