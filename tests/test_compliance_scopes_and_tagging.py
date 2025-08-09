import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_compliance_scope_crud_and_asset_tagging():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # Login as super-admin
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a compliance scope
        scope_payload = {
            "name": "Test-Scope-Tagging",
            "description": "Scope for tagging test",
            "reference_url": "https://example.com/scope",
        }
        create_scope_resp = await ac.post(
            "/compliance/scopes", json=scope_payload, headers=headers
        )
        assert (
            create_scope_resp.status_code == 201
        ), f"Scope creation failed: {create_scope_resp.text}"
        scope = create_scope_resp.json()
        scope_id = scope["id"]

        # Create an asset (computer)
        computer_payload = {
            "name": "Taggable-Computer",
            "status": "active",
            "cpu": "Intel Core i5",
        }
        create_asset_resp = await ac.post(
            "/assets/computers/", json=computer_payload, headers=headers
        )
        assert (
            create_asset_resp.status_code == 201
        ), f"Computer creation failed: {create_asset_resp.text}"
        asset_id = create_asset_resp.json()["id"]

        # Tag asset with scope via asset router
        tag_resp = await ac.post(
            f"/assets/{asset_id}/scopes/{scope_id}",
            json={"justification": "In scope for PCI segment"},
            headers=headers,
        )
        assert tag_resp.status_code in (200, 201), f"Tagging failed: {tag_resp.text}"

        # Replace asset scopes with multiple scope IDs (including existing scope)
        # Create a second scope
        scope2_payload = {"name": "Test-Scope-2", "description": "Second scope"}
        create_scope2_resp = await ac.post(
            "/compliance/scopes", json=scope2_payload, headers=headers
        )
        assert (
            create_scope2_resp.status_code == 201
        ), f"Scope 2 creation failed: {create_scope2_resp.text}"
        scope2_id = create_scope2_resp.json()["id"]

        replace_resp = await ac.put(
            f"/assets/{asset_id}/scopes",
            json=[scope_id, scope2_id],
            headers=headers,
        )
        assert (
            replace_resp.status_code == 204
        ), f"Replacing scopes failed: {replace_resp.text}"

        # Attempt to delete a scope that's in use should fail with 409
        del_in_use_resp = await ac.delete(
            f"/compliance/scopes/{scope_id}", headers=headers
        )
        assert (
            del_in_use_resp.status_code == 409
        ), "Deleting in-use scope should return 409"

        # Untag one scope
        untag_resp = await ac.delete(
            f"/assets/{asset_id}/scopes/{scope2_id}", headers=headers
        )
        assert untag_resp.status_code == 204, f"Untagging failed: {untag_resp.text}"

        # Now replace with empty list to clear all scopes
        clear_resp = await ac.put(
            f"/assets/{asset_id}/scopes", json=[], headers=headers
        )
        assert (
            clear_resp.status_code == 204
        ), f"Clearing scopes failed: {clear_resp.text}"

        # After clearing, deleting the scopes should succeed
        del_scope2_resp = await ac.delete(
            f"/compliance/scopes/{scope2_id}", headers=headers
        )
        assert del_scope2_resp.status_code in (
            204,
            200,
        ), f"Deleting unused scope failed: {del_scope2_resp.text}"
        del_scope_resp = await ac.delete(
            f"/compliance/scopes/{scope_id}", headers=headers
        )
        assert del_scope_resp.status_code in (
            204,
            200,
        ), f"Deleting unused scope failed: {del_scope_resp.text}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_compliance_manage_permission_required_for_tagging():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # Login as super-admin
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        admin_token = login_resp.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Create a compliance scope and an asset as setup
        scope_payload = {"name": "Perm-Check-Scope", "description": "scope"}
        scope_resp = await ac.post(
            "/compliance/scopes", json=scope_payload, headers=admin_headers
        )
        assert (
            scope_resp.status_code == 201
        ), f"Scope creation failed: {scope_resp.text}"
        scope_id = scope_resp.json()["id"]

        computer_payload = {
            "name": "Perm-Check-Computer",
            "status": "active",
            "cpu": "i5",
        }
        comp_resp = await ac.post(
            "/assets/computers/", json=computer_payload, headers=admin_headers
        )
        assert (
            comp_resp.status_code == 201
        ), f"Computer creation failed: {comp_resp.text}"
        asset_id = comp_resp.json()["id"]

        # Create a role WITHOUT asset:compliance_manage
        role_payload = {
            "name": "No-Compliance-Role",
            "description": "no compliance manage",
        }
        role_resp = await ac.post("/roles/", json=role_payload, headers=admin_headers)
        assert role_resp.status_code == 201, f"Role creation failed: {role_resp.text}"
        role_id = role_resp.json()["id"]

        # Assign only computer:read permission
        perms_resp = await ac.get("/roles/permissions", headers=admin_headers)
        assert perms_resp.status_code == 200
        perms = perms_resp.json()
        comp_read = next(
            p for p in perms if p["resource"] == "computer" and p["action"] == "read"
        )
        assign_resp = await ac.post(
            f"/roles/{role_id}/permissions/{comp_read['id']}", headers=admin_headers
        )
        assert assign_resp.status_code == 200

        # Create a user with this role
        unique_email = "no_compliance_user@example.com"
        user_payload = {
            "email": unique_email,
            "username": "no_compliance_user",
            "password": "testpass123!",
            "role_id": role_id,
        }
        user_resp = await ac.post("/users/", json=user_payload, headers=admin_headers)
        assert user_resp.status_code == 201, f"User creation failed: {user_resp.text}"

        # Login as that user
        login2_resp = await ac.post(
            "/auth/login", data={"username": unique_email, "password": "testpass123!"}
        )
        assert login2_resp.status_code == 200
        user_token = login2_resp.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Attempt to tag asset -> expect permission denial. Depending on transport settings,
        # FastAPI may surface PermissionError directly or return HTTP 403.
        try:
            tag_resp = await ac.post(
                f"/assets/{asset_id}/scopes/{scope_id}",
                json={"justification": "attempt"},
                headers=user_headers,
            )
            assert (
                tag_resp.status_code == 403
            ), "User without compliance_manage should not tag assets"
        except Exception as exc:  # ASGITransport may bubble service PermissionError
            assert (
                exc.__class__.__name__ == "PermissionError"
            ), f"Unexpected exception type: {type(exc)}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_compliance_scope_includes_assets():
    """Test that compliance scope responses include associated assets."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # Login as super-admin
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a compliance scope
        scope_payload = {
            "name": "Test-Assets-Response",
            "description": "Test scope for asset inclusion",
        }
        create_scope_resp = await ac.post(
            "/compliance/scopes", json=scope_payload, headers=headers
        )
        assert (
            create_scope_resp.status_code == 201
        ), f"Scope creation failed: {create_scope_resp.text}"
        scope = create_scope_resp.json()
        scope_id = scope["id"]
        
        # Verify empty assets list initially
        assert "assets" in scope
        assert scope["assets"] == []

        # Create two assets
        computer_payload = {
            "name": "Test-Computer-Assets",
            "status": "active",
            "cpu": "Intel Core i5",
        }
        create_computer_resp = await ac.post(
            "/assets/computers/", json=computer_payload, headers=headers
        )
        assert create_computer_resp.status_code == 201
        computer_id = create_computer_resp.json()["id"]

        printer_payload = {
            "name": "Test-Printer-Assets",
            "status": "active",
            "model": "HP LaserJet",
        }
        create_printer_resp = await ac.post(
            "/assets/printers/", json=printer_payload, headers=headers
        )
        assert create_printer_resp.status_code == 201
        printer_id = create_printer_resp.json()["id"]

        # Tag both assets with the scope
        tag_computer_resp = await ac.post(
            f"/compliance/assets/{computer_id}/scopes/{scope_id}",
            headers=headers,
        )
        assert tag_computer_resp.status_code == 201

        tag_printer_resp = await ac.post(
            f"/compliance/assets/{printer_id}/scopes/{scope_id}",
            headers=headers,
        )
        assert tag_printer_resp.status_code == 201

        # Get the scope and verify assets are included
        get_scope_resp = await ac.get(f"/compliance/scopes/{scope_id}", headers=headers)
        assert get_scope_resp.status_code == 200
        scope_with_assets = get_scope_resp.json()
        
        # Verify assets field exists and contains both assets
        assert "assets" in scope_with_assets
        assert len(scope_with_assets["assets"]) == 2
        
        # Verify asset objects contain only id, name, and type
        asset_names = {asset["name"] for asset in scope_with_assets["assets"]}
        asset_types = {asset["type"] for asset in scope_with_assets["assets"]}
        asset_ids = {asset["id"] for asset in scope_with_assets["assets"]}
        
        assert "Test-Computer-Assets" in asset_names
        assert "Test-Printer-Assets" in asset_names
        assert "computer" in asset_types
        assert "printer" in asset_types
        assert computer_id in asset_ids
        assert printer_id in asset_ids
        
        # Verify each asset only has id, name, type fields
        for asset in scope_with_assets["assets"]:
            assert set(asset.keys()) == {"id", "name", "type"}

        # Test list scopes endpoint also includes assets
        list_scopes_resp = await ac.get("/compliance/scopes", headers=headers)
        assert list_scopes_resp.status_code == 200
        scopes_list = list_scopes_resp.json()
        
        # Find our scope in the list
        our_scope = next(s for s in scopes_list if s["id"] == scope_id)
        assert "assets" in our_scope
        assert len(our_scope["assets"]) == 2

        # Clean up
        await ac.delete(f"/assets/computers/{computer_id}", headers=headers)
        await ac.delete(f"/assets/printers/{printer_id}", headers=headers)
        await ac.delete(f"/compliance/scopes/{scope_id}", headers=headers)
