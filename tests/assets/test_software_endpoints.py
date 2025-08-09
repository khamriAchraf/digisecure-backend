from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_software_crud_and_pagination():
    """Full CRUD lifecycle for Software plus pagination and sorting."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # ---------- 1. Login as super-admin ----------
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

        # ---------- 2. Create a Software ----------
        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        software_payload = {
            "name": f"E2E-Software-{unique_suffix}",
            "vendor": "Test Vendor Inc.",
            "description": "Test software for E2E testing",
            "software_type": "Application",
            "encryption_enabled": True,
            "encryption_type": "AES-256",
            "vulnerability_status": "Compliant",
        }
        create_resp = await ac.post(
            "/assets/software/", json=software_payload, headers=headers
        )
        assert (
            create_resp.status_code == 201
        ), f"Software creation failed: {create_resp.text}"
        software = create_resp.json()
        software_id = software["id"]
        assert software["name"] == software_payload["name"]
        assert software["vendor"] == software_payload["vendor"]
        assert (
            software["vulnerability_status"] == software_payload["vulnerability_status"]
        )

        # ---------- 3. GET software endpoint ----------
        get_resp = await ac.get(f"/assets/software/{software_id}", headers=headers)
        assert get_resp.status_code == 200, f"Software get failed: {get_resp.text}"
        assert get_resp.json()["id"] == software_id
        assert get_resp.json()["encryption_type"] == software_payload["encryption_type"]

        # ---------- 4. Update software (PCI compliance change) ----------
        update_payload = {
            "vulnerability_status": "Non-Compliant",
            "patch_level": "2.0.0",
        }
        update_resp = await ac.put(
            f"/assets/software/{software_id}", json=update_payload, headers=headers
        )
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        updated_software = update_resp.json()
        assert updated_software["vulnerability_status"] == "Non-Compliant"
        assert updated_software["patch_level"] == "2.0.0"

        # ---------- 5. List software with pagination ----------
        list_resp = await ac.get(
            "/assets/software/", params={"page": 1, "per_page": 9999}, headers=headers
        )
        assert (
            list_resp.status_code == 200
        ), f"List with pagination failed: {list_resp.text}"
        paginated_data = list_resp.json()
        assert "data" in paginated_data and "total" in paginated_data
        assert paginated_data["total"] >= 1
        ids = [item["id"] for item in paginated_data["data"]]
        assert software_id in ids, "Created software missing from paginated list"

        # ---------- 6. List software with sorting ----------
        sort_resp = await ac.get(
            "/assets/software/",
            params={"sort_by": "name", "sort_order": "desc"},
            headers=headers,
        )
        assert (
            sort_resp.status_code == 200
        ), f"List with sorting failed: {sort_resp.text}"
        sorted_data = sort_resp.json()["data"]
        assert len(sorted_data) > 0, "Sorted list should not be empty"

        # ---------- 7. Search software ----------
        search_resp = await ac.get(
            "/assets/software/",
            params={"search": software_payload["name"]},
            headers=headers,
        )
        assert search_resp.status_code == 200, f"Search failed: {search_resp.text}"
        search_data = search_resp.json()["data"]
        assert len(search_data) > 0
        ids = [item["id"] for item in search_data]
        assert software_id in ids, "Created software not found via search"

        # ---------- 8. Delete software ----------
        del_resp = await ac.delete(f"/assets/software/{software_id}", headers=headers)
        assert del_resp.status_code == 204, f"Delete failed: {del_resp.text}"

        # ---------- 9. Confirm deletion ----------
        get_after_del = await ac.get(f"/assets/software/{software_id}", headers=headers)
        assert get_after_del.status_code == 404, "Deleted software should return 404"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_software_version_management():
    """Test software version creation and deletion."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # ---------- 1. Login as super-admin ----------
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

        # ---------- 2. Create a Software first ----------
        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        software_payload = {
            "name": f"Version-Test-Software-{unique_suffix}",
            "vendor": "Version Test Vendor",
            "description": "Software for version testing",
            "software_type": "Application",
        }
        create_software_resp = await ac.post(
            "/assets/software/", json=software_payload, headers=headers
        )
        assert (
            create_software_resp.status_code == 201
        ), f"Software creation failed: {create_software_resp.text}"
        software = create_software_resp.json()
        software_id = software["id"]

        # ---------- 3. Create Software Version 1.0 ----------
        version_1_0_payload = {
            "software_id": software_id,
            "version": "1.0.0",
            "build_number": "build-123",
            "release_date": "2024-01-15",
            "end_of_life_date": "2025-01-15",
            "end_of_support_date": "2024-12-31",
        }
        create_version_resp = await ac.post(
            "/assets/software/versions", json=version_1_0_payload, headers=headers
        )
        assert (
            create_version_resp.status_code == 201
        ), f"Version creation failed: {create_version_resp.text}"
        version_1_0 = create_version_resp.json()
        version_1_0_id = version_1_0["id"]
        assert version_1_0["version"] == "1.0.0"
        assert version_1_0["software_id"] == software_id

        # ---------- 4. Create Software Version 2.0 ----------
        version_2_0_payload = {
            "software_id": software_id,
            "version": "2.0.0",
            "build_number": "build-456",
            "release_date": "2024-06-15",
            "end_of_life_date": "2026-06-15",
            "end_of_support_date": "2025-12-31",
        }
        create_version_2_resp = await ac.post(
            "/assets/software/versions", json=version_2_0_payload, headers=headers
        )
        assert (
            create_version_2_resp.status_code == 201
        ), f"Version 2.0 creation failed: {create_version_2_resp.text}"
        version_2_0 = create_version_2_resp.json()


        # ---------- 6. Get software with versions ----------
        get_with_versions_resp = await ac.get(
            f"/assets/software/{software_id}/with-versions", headers=headers
        )
        assert (
            get_with_versions_resp.status_code == 200
        ), f"Get with versions failed: {get_with_versions_resp.text}"
        software_with_versions = get_with_versions_resp.json()
        assert len(software_with_versions["versions"]) == 2
        version_versions = [v["version"] for v in software_with_versions["versions"]]
        assert "1.0.0" in version_versions
        assert "2.0.0" in version_versions

        # ---------- 7. Delete version 1.0 ----------
        delete_version_resp = await ac.delete(
            f"/assets/software/versions/{version_1_0_id}", headers=headers
        )
        assert (
            delete_version_resp.status_code == 204
        ), f"Version deletion failed: {delete_version_resp.text}"

        # ---------- 8. Verify version 1.0 is deleted ----------
        get_with_versions_after_del = await ac.get(
            f"/assets/software/{software_id}/with-versions", headers=headers
        )
        assert (
            get_with_versions_after_del.status_code == 200
        ), f"Get with versions after deletion failed: {get_with_versions_after_del.text}"
        software_after_del = get_with_versions_after_del.json()
        assert len(software_after_del["versions"]) == 1
        assert software_after_del["versions"][0]["version"] == "2.0.0"

        # ---------- 9. Clean up - Delete software ----------
        del_software_resp = await ac.delete(
            f"/assets/software/{software_id}", headers=headers
        )
        assert (
            del_software_resp.status_code == 204
        ), f"Software deletion failed: {del_software_resp.text}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_software_security_fields():
    """Test software security-related fields and validation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # ---------- 1. Login as super-admin ----------
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

        # ---------- 2. Create software with comprehensive PCI fields ----------
        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        software_payload = {
            "name": f"PCI-Compliance-Software-{unique_suffix}",
            "vendor": "PCI Vendor Inc.",
            "description": "Software with comprehensive PCI compliance fields",
            "software_type": "Application",
            # Encryption and security
            "encryption_enabled": True,
            "encryption_type": "AES-256",
            "encryption_key_management": "HSM",
            "secure_communication": True,
            "communication_protocol": "HTTPS",
            # Authentication and access control
            "authentication_required": True,
            "multi_factor_auth_supported": True,
            "role_based_access_control": True,
            "session_timeout_enabled": True,
            "session_timeout_minutes": 30,
            # Logging and monitoring
            "audit_logging_enabled": True,
            "log_retention_days": 90,
            "log_integrity_protection": True,
            "centralized_logging": True,
            # Vulnerability and patch management
            "last_vulnerability_scan": "2024-01-15",
            "vulnerability_status": "Compliant",
            "known_vulnerabilities": "CVE-2023-1234, CVE-2023-5678",
            "patch_management_enabled": True,
            "last_patch_date": "2024-01-10",
            "patch_level": "2.1.3",
            "auto_update_enabled": True,
            # Network security
            "network_access_required": True,
            "firewall_rules_required": "Both",
            "vpn_required": True,
            "network_segmentation": "PCI",
            # Data protection and privacy
            "data_retention_policy": "7 years",
            "data_backup_enabled": True,
            "data_encryption_at_rest": True,
            # Software lifecycle
            "end_of_life_date": "2026-12-31",
            "end_of_support_date": "2025-12-31",
            "replacement_planned": False,
            # Performance and resource usage
            "minimum_requirements": "4GB RAM, 2 CPU cores",
            "recommended_requirements": "8GB RAM, 4 CPU cores",
            "resource_usage_monitoring": True,
        }

        create_resp = await ac.post(
            "/assets/software/", json=software_payload, headers=headers
        )
        assert (
            create_resp.status_code == 201
        ), f"Software creation failed: {create_resp.text}"
        software = create_resp.json()
        software_id = software["id"]

        # ---------- 3. Verify all PCI fields are saved correctly ----------
        get_resp = await ac.get(f"/assets/software/{software_id}", headers=headers)
        assert get_resp.status_code == 200, f"Software get failed: {get_resp.text}"
        retrieved_software = get_resp.json()

        # Verify encryption fields
        assert retrieved_software["encryption_enabled"] == True
        assert retrieved_software["encryption_type"] == "AES-256"
        assert retrieved_software["encryption_key_management"] == "HSM"
        assert retrieved_software["secure_communication"] == True
        assert retrieved_software["communication_protocol"] == "HTTPS"

        # Verify authentication fields
        assert retrieved_software["authentication_required"] == True
        assert retrieved_software["multi_factor_auth_supported"] == True
        assert retrieved_software["role_based_access_control"] == True
        assert retrieved_software["session_timeout_enabled"] == True
        assert retrieved_software["session_timeout_minutes"] == 30

        # Verify logging fields
        assert retrieved_software["audit_logging_enabled"] == True
        assert retrieved_software["log_retention_days"] == 90
        assert retrieved_software["log_integrity_protection"] == True
        assert retrieved_software["centralized_logging"] == True

        # Verify vulnerability fields
        assert retrieved_software["vulnerability_status"] == "Compliant"
        assert (
            retrieved_software["known_vulnerabilities"]
            == "CVE-2023-1234, CVE-2023-5678"
        )
        assert retrieved_software["patch_management_enabled"] == True
        assert retrieved_software["patch_level"] == "2.1.3"
        assert retrieved_software["auto_update_enabled"] == True

        # Verify network security fields
        assert retrieved_software["network_access_required"] == True
        assert retrieved_software["firewall_rules_required"] == "Both"
        assert retrieved_software["vpn_required"] == True
        assert retrieved_software["network_segmentation"] == "PCI"

        # Verify data protection fields
        assert retrieved_software["data_retention_policy"] == "7 years"
        assert retrieved_software["data_backup_enabled"] == True
        assert retrieved_software["data_encryption_at_rest"] == True

        # ---------- 4. Update compliance status ----------
        update_payload = {
            "vulnerability_status": "Non-Compliant",
            "patch_level": "2.1.4",
        }
        update_resp = await ac.put(
            f"/assets/software/{software_id}", json=update_payload, headers=headers
        )
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        updated_software = update_resp.json()
        assert updated_software["vulnerability_status"] == "Non-Compliant"
        assert updated_software["patch_level"] == "2.1.4"

        # ---------- 5. Clean up ----------
        del_resp = await ac.delete(f"/assets/software/{software_id}", headers=headers)
        assert del_resp.status_code == 204, f"Delete failed: {del_resp.text}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_software_validation_and_error_handling():
    """Test software validation and error handling."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # ---------- 1. Login as super-admin ----------
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

        # ---------- 2. Test duplicate software name (should fail) ----------
        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        software_name = f"Duplicate-Test-Software-{unique_suffix}"

        software_payload = {
            "name": software_name,
            "vendor": "Test Vendor",
            "description": "Test software",
        }

        # Create first software
        create_resp = await ac.post(
            "/assets/software/", json=software_payload, headers=headers
        )
        assert (
            create_resp.status_code == 201
        ), f"First software creation failed: {create_resp.text}"
        software_id = create_resp.json()["id"]

        # ---------- 3. Test invalid software ID for version creation ----------
        invalid_version_payload = {
            "software_id": 99999,  # Non-existent software ID
            "version": "1.0.0",
        }
        invalid_version_resp = await ac.post(
            "/assets/software/versions", json=invalid_version_payload, headers=headers
        )
        assert (
            invalid_version_resp.status_code == 409
        ), "Should not allow version creation for non-existent software"

        # ---------- 4. Test duplicate version for same software ----------
        version_payload = {
            "software_id": software_id,
            "version": "1.0.0",
        }

        # Create first version
        create_version_resp = await ac.post(
            "/assets/software/versions", json=version_payload, headers=headers
        )
        assert (
            create_version_resp.status_code == 201
        ), f"First version creation failed: {create_version_resp.text}"
        version_id = create_version_resp.json()["id"]

        # Try to create duplicate version
        duplicate_version_resp = await ac.post(
            "/assets/software/versions", json=version_payload, headers=headers
        )
        assert (
            duplicate_version_resp.status_code == 409
        ), "Should not allow duplicate versions for same software"

        # ---------- 5. Test non-existent version deletion ----------
        invalid_delete_resp = await ac.delete(
            "/assets/software/versions/99999", headers=headers
        )
        assert (
            invalid_delete_resp.status_code == 404
        ), "Should return 404 for non-existent version"

        # ---------- 6. Test non-existent software access ----------
        invalid_get_resp = await ac.get("/assets/software/99999", headers=headers)
        assert (
            invalid_get_resp.status_code == 404
        ), "Should return 404 for non-existent software"

        # ---------- 7. Clean up ----------
        del_version_resp = await ac.delete(
            f"/assets/software/versions/{version_id}", headers=headers
        )
        assert (
            del_version_resp.status_code == 204
        ), f"Version deletion failed: {del_version_resp.text}"

        del_software_resp = await ac.delete(
            f"/assets/software/{software_id}", headers=headers
        )
        assert (
            del_software_resp.status_code == 204
        ), f"Software deletion failed: {del_software_resp.text}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_software_filtering_and_search():
    """Test software filtering and search functionality."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # ---------- 1. Login as super-admin ----------
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

        # ---------- 2. Create multiple software items with different characteristics ----------
        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

        software_items = [
            {
                "name": f"Compliant-Software-{unique_suffix}",
                "vendor": "Compliant Vendor",
                "vulnerability_status": "Compliant",
                "software_type": "Application",
            },
            {
                "name": f"Non-Compliant-Software-{unique_suffix}",
                "vendor": "Non-Compliant Vendor",
                "vulnerability_status": "Non-Compliant",
                "software_type": "Operating System",
            },
            {
                "name": f"Security-Tool-{unique_suffix}",
                "vendor": "Security Vendor",
                "vulnerability_status": "Pending",
                "software_type": "Security Tool",
            },
        ]

        created_ids = []
        for software_payload in software_items:
            create_resp = await ac.post(
                "/assets/software/", json=software_payload, headers=headers
            )
            assert (
                create_resp.status_code == 201
            ), f"Software creation failed: {create_resp.text}"
            created_ids.append(create_resp.json()["id"])

        # ---------- 3. Test filtering by vulnerability status ----------
        compliant_resp = await ac.get(
            "/assets/software/",
            params={"vulnerability_status": "Compliant"},
            headers=headers,
        )
        assert (
            compliant_resp.status_code == 200
        ), f"Filter by vulnerability_status failed: {compliant_resp.text}"
        compliant_data = compliant_resp.json()["data"]
        assert all(
            item["vulnerability_status"] == "Compliant" for item in compliant_data
        )

        # ---------- 4. Test filtering by software type ----------
        security_tool_resp = await ac.get(
            "/assets/software/",
            params={"software_type": "Security Tool"},
            headers=headers,
        )
        assert (
            security_tool_resp.status_code == 200
        ), f"Filter by type failed: {security_tool_resp.text}"
        security_tool_data = security_tool_resp.json()["data"]
        assert all(
            item["software_type"] == "Security Tool" for item in security_tool_data
        )

        # ---------- 5. Test search by vendor ----------
        search_resp = await ac.get(
            "/assets/software/",
            params={"search": "Compliant Vendor"},
            headers=headers,
        )
        assert search_resp.status_code == 200, f"Search failed: {search_resp.text}"
        search_data = search_resp.json()["data"]
        assert len(search_data) > 0
        assert any("Compliant Vendor" in item["vendor"] for item in search_data)

        # ---------- 6. Test pagination ----------
        pagination_resp = await ac.get(
            "/assets/software/",
            params={"page": 1, "per_page": 2},
            headers=headers,
        )
        assert (
            pagination_resp.status_code == 200
        ), f"Pagination failed: {pagination_resp.text}"
        pagination_data = pagination_resp.json()
        assert len(pagination_data["data"]) <= 2
        assert pagination_data["total"] >= len(created_ids)

        # ---------- 7. Test sorting ----------
        sort_resp = await ac.get(
            "/assets/software/",
            params={"sort_by": "name", "sort_order": "desc"},
            headers=headers,
        )
        assert sort_resp.status_code == 200, f"Sorting failed: {sort_resp.text}"
        sort_data = sort_resp.json()["data"]
        assert len(sort_data) > 0

        # ---------- 8. Clean up ----------
        for software_id in created_ids:
            del_resp = await ac.delete(
                f"/assets/software/{software_id}", headers=headers
            )
            assert (
                del_resp.status_code == 204
            ), f"Delete failed for {software_id}: {del_resp.text}"
