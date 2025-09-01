from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_access_filters_computer_access_control():
    """
    Test access filters functionality for computer assets.

    This test:
    1. Creates a group
    2. Creates a role with computer read permissions
    3. Creates a user with that role and adds them to the group
    4. Creates three computers with different access scenarios
    5. Tests that the user can only see computers they have access to
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

        # ---------- 1. Login as Super-Admin ----------
        print(
            f"logging in using super admin credentials {SUPER_ADMIN['email']} and {SUPER_ADMIN['password']}"
        )
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )

        assert (
            login_resp.status_code == 200
        ), f"Super-Admin login failed: {login_resp.text}"
        admin_token = login_resp.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # ---------- 2. Create a group ----------
        group_payload = {
            "name": f"Test-Group-{unique_suffix}",
            "description": "Test group for access filters",
            "type": "org",
        }
        group_resp = await ac.post(
            "/groups/", json=group_payload, headers=admin_headers
        )
        assert (
            group_resp.status_code == 201
        ), f"Group creation failed: {group_resp.text}"
        group = group_resp.json()
        group_id = group["id"]
        print(f"Created group: {group['name']} (ID: {group_id})")

        # ---------- 3. Create a role with computer read permissions ----------
        role_payload = {
            "name": f"Computer-Reader-{unique_suffix}",
            "description": "Role with computer read permissions",
            "is_builtin": False,
        }
        role_resp = await ac.post("/roles/", json=role_payload, headers=admin_headers)
        assert role_resp.status_code == 201, f"Role creation failed: {role_resp.text}"
        role = role_resp.json()
        role_id = role["id"]
        print(f"Created role: {role['name']} (ID: {role_id})")

        # Assign computer read permission to the role
        # First, get the computer read permission
        permissions_resp = await ac.get("/roles/permissions", headers=admin_headers)
        assert (
            permissions_resp.status_code == 200
        ), f"Failed to get permissions: {permissions_resp.text}"
        permissions = permissions_resp.json()

        computer_read_permission = None
        computer_list_permission = None
        for perm in permissions:
            if perm["resource"] == "computer" and perm["action"] == "read":
                computer_read_permission = perm
            if perm["resource"] == "computer" and perm["action"] == "list":
                computer_list_permission = perm
            if computer_read_permission and computer_list_permission:
                break

        assert (
            computer_read_permission is not None
        ), "Computer read permission not found"
        assert (
            computer_list_permission is not None
        ), "Computer list permission not found"

        # Assign the permission to the role
        assign_resp = await ac.post(
            f"/roles/{role_id}/permissions/{computer_read_permission['id']}",
            headers=admin_headers,
        )
        assign_list_resp = await ac.post(
            f"/roles/{role_id}/permissions/{computer_list_permission['id']}",
            headers=admin_headers,
        )
        assert (
            assign_resp.status_code == 200
        ), f"Failed to assign permission: {assign_resp.text}"
        assert (
            assign_list_resp.status_code == 200
        ), f"Failed to assign permission: {assign_list_resp.text}"
        print(f"Assigned computer:read and computer:list permissions to role")

        # ---------- 4. Create a user with the new role ----------
        user_payload = {
            "email": f"testuser{unique_suffix}@example.com",
            "username": f"testuser{unique_suffix}",
            "full_name": f"Test User {unique_suffix}",
            "password": "testpass123!",
            "role_id": role_id,
        }
        user_resp = await ac.post("/users/", json=user_payload, headers=admin_headers)
        assert user_resp.status_code == 201, f"User creation failed: {user_resp.text}"
        user = user_resp.json()
        user_id = user["id"]
        print(f"Created user: {user['username']} (ID: {user_id})")

        # ---------- 5. Add user to the group ----------
        add_user_resp = await ac.post(
            f"/groups/{group_id}/users/{user_id}", headers=admin_headers
        )
        assert (
            add_user_resp.status_code == 200
        ), f"Failed to add user to group: {add_user_resp.text}"
        print(f"Added user to group")

        # ---------- 6. Create three computers with different access scenarios ----------
        computers = []

        # Computer 1: Assigned to the group (user should see this)
        computer1_payload = {
            "name": f"Group-Computer-{unique_suffix}",
            "status": "active",
            "cpu": "Intel Core i5",
            "ram": "8GB",
            "storage": "256GB SSD",
            "os": "Windows 10",
        }
        computer1_resp = await ac.post(
            "/assets/computers/", json=computer1_payload, headers=admin_headers
        )
        assert (
            computer1_resp.status_code == 201
        ), f"Computer 1 creation failed: {computer1_resp.text}"
        computer1 = computer1_resp.json()

        # Add computer to group using groups endpoint
        add_asset1_resp = await ac.post(
            f"/groups/{group_id}/assets/{computer1['id']}", headers=admin_headers
        )
        assert (
            add_asset1_resp.status_code == 200
        ), f"Failed to add computer 1 to group: {add_asset1_resp.text}"

        computers.append(("group", computer1))
        print(
            f"Created computer 1 (group access): {computer1['name']} (ID: {computer1['id']})"
        )

        # Computer 2: Assigned directly to the user (user should see this)
        computer2_payload = {
            "name": f"User-Computer-{unique_suffix}",
            "status": "active",
            "cpu": "Intel Core i7",
            "ram": "16GB",
            "storage": "512GB SSD",
            "os": "Windows 11",
            "assigned_to": user_id,  # Assigned directly to the user
        }
        computer2_resp = await ac.post(
            "/assets/computers/", json=computer2_payload, headers=admin_headers
        )
        assert (
            computer2_resp.status_code == 201
        ), f"Computer 2 creation failed: {computer2_resp.text}"
        computer2 = computer2_resp.json()
        computers.append(("user", computer2))
        print(
            f"Created computer 2 (user access): {computer2['name']} (ID: {computer2['id']})"
        )

        # Computer 3: Not assigned to anyone (user should NOT see this)
        computer3_payload = {
            "name": f"Unauthorized-Computer-{unique_suffix}",
            "status": "active",
            "cpu": "Intel Core i9",
            "ram": "32GB",
            "storage": "1TB SSD",
            "os": "Linux",
            # No group_id or assigned_to - should be inaccessible
        }
        computer3_resp = await ac.post(
            "/assets/computers/", json=computer3_payload, headers=admin_headers
        )
        assert (
            computer3_resp.status_code == 201
        ), f"Computer 3 creation failed: {computer3_resp.text}"
        computer3 = computer3_resp.json()
        computers.append(("unauthorized", computer3))
        print(
            f"Created computer 3 (no access): {computer3['name']} (ID: {computer3['id']})"
        )

        # ---------- 7. Login as the test user ----------
        user_login_resp = await ac.post(
            "/auth/login",
            data={
                "username": user_payload["email"],  # Login expects email, not username
                "password": user_payload["password"],
            },
        )
        assert (
            user_login_resp.status_code == 200
        ), f"User login failed: {user_login_resp.text}"
        user_token = user_login_resp.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        print(f"Logged in as test user: {user_payload['email']}")

        # ---------- 8. Test that user can only see accessible computers ----------
        list_resp = await ac.get(
            "/assets/computers/",
            params={"page": 1, "per_page": 100},  # Get all computers
            headers=user_headers,
        )
        assert list_resp.status_code == 200, f"Computer list failed: {list_resp.text}"

        accessible_computers = list_resp.json()["data"]
        accessible_ids = [comp["id"] for comp in accessible_computers]

        print(f"User can see {len(accessible_computers)} computers")
        print(f"Accessible computer IDs: {accessible_ids}")

        # Verify user can see computer 1 (group access)
        assert (
            computer1["id"] in accessible_ids
        ), f"User should see computer 1 (group access): {computer1['name']}"
        print(f"✅ User can see computer 1 (group access): {computer1['name']}")

        # Verify user can see computer 2 (direct assignment)
        assert (
            computer2["id"] in accessible_ids
        ), f"User should see computer 2 (direct assignment): {computer2['name']}"
        print(f"✅ User can see computer 2 (direct assignment): {computer2['name']}")

        # Verify user CANNOT see computer 3 (no access)
        assert (
            computer3["id"] not in accessible_ids
        ), f"User should NOT see computer 3 (no access): {computer3['name']}"
        print(
            f"✅ User correctly cannot see computer 3 (no access): {computer3['name']}"
        )

        # Verify total count is correct (should be 2 accessible computers)
        assert (
            len(accessible_computers) == 2
        ), f"User should see exactly 2 computers, but sees {len(accessible_computers)}"
        print(f"✅ User sees exactly 2 computers as expected")

        # ---------- 9. Test individual computer access ----------
        # Test that user can access computer 1 (group access)
        get_computer1_resp = await ac.get(
            f"/assets/computers/{computer1['id']}", headers=user_headers
        )
        assert (
            get_computer1_resp.status_code == 200
        ), f"User should be able to access computer 1: {get_computer1_resp.text}"
        print(f"✅ User can access computer 1 individually")

        # Test that user can access computer 2 (direct assignment)
        get_computer2_resp = await ac.get(
            f"/assets/computers/{computer2['id']}", headers=user_headers
        )
        assert (
            get_computer2_resp.status_code == 200
        ), f"User should be able to access computer 2: {get_computer2_resp.text}"
        print(f"✅ User can access computer 2 individually")

        # Test that user CANNOT access computer 3 (no access)
        get_computer3_resp = await ac.get(
            f"/assets/computers/{computer3['id']}", headers=user_headers
        )
        assert (
            get_computer3_resp.status_code == 403
        ), f"User should NOT be able to access computer 3: {get_computer3_resp.text}"
        print(f"✅ User correctly cannot access computer 3 individually")

        # ---------- 10. Test search functionality with access filters ----------
        # Search for computers - should only return accessible ones
        search_resp = await ac.get(
            "/assets/computers/",
            params={"search": "Computer", "page": 1, "per_page": 100},
            headers=user_headers,
        )
        assert search_resp.status_code == 200, f"Search failed: {search_resp.text}"

        search_results = search_resp.json()["data"]
        search_ids = [comp["id"] for comp in search_results]

        # Should only find the 2 accessible computers
        assert computer1["id"] in search_ids, "Search should find computer 1"
        assert computer2["id"] in search_ids, "Search should find computer 2"
        assert computer3["id"] not in search_ids, "Search should NOT find computer 3"
        print(f"✅ Search correctly returns only accessible computers")

        # ---------- 11. Test pagination with access filters ----------
        # Test pagination - should work correctly with access filters
        pagination_resp = await ac.get(
            "/assets/computers/",
            params={"page": 1, "per_page": 1},  # Only 1 per page
            headers=user_headers,
        )
        assert (
            pagination_resp.status_code == 200
        ), f"Pagination failed: {pagination_resp.text}"

        pagination_data = pagination_resp.json()
        assert (
            pagination_data["total"] == 2
        ), f"Total should be 2, but is {pagination_data['total']}"
        assert len(pagination_data["data"]) == 1, f"Should return 1 computer per page"
        print(f"✅ Pagination works correctly with access filters")

        # ---------- 12. Clean up - Delete all created resources ----------
        print("🧹 Cleaning up test resources...")

        # Delete computers
        for access_type, computer in computers:
            del_resp = await ac.delete(
                f"/assets/computers/{computer['id']}", headers=admin_headers
            )
            assert (
                del_resp.status_code == 204
            ), f"Failed to delete computer {computer['id']}: {del_resp.text}"
            print(f"Deleted computer: {computer['name']}")

        # Delete user
        del_user_resp = await ac.delete(f"/users/{user_id}", headers=admin_headers)
        assert (
            del_user_resp.status_code == 204
        ), f"Failed to delete user: {del_user_resp.text}"
        print(f"Deleted user: {user['username']}")

        # Delete role
        del_role_resp = await ac.delete(f"/roles/{role_id}", headers=admin_headers)
        assert (
            del_role_resp.status_code == 204
        ), f"Failed to delete role: {del_role_resp.text}"
        print(f"Deleted role: {role['name']}")

        # Delete group
        del_group_resp = await ac.delete(f"/groups/{group_id}", headers=admin_headers)
        assert (
            del_group_resp.status_code == 204
        ), f"Failed to delete group: {del_group_resp.text}"
        print(f"Deleted group: {group['name']}")

        print("✅ Access filters integration test completed successfully!")
