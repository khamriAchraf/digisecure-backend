from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_asset_computer_crud_and_pagination():
    """Full CRUD lifecycle for a Computer asset plus pagination and sorting."""
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

        # ---------- 2. Create a Computer ----------
        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        computer_payload = {
            "name": f"E2E-Computer-{unique_suffix}",
            "status": "active",
            "cpu": "Intel Core i5-12400",
            "ram": "16GB",
            "storage": "512GB SSD",
            "os": "Windows 11 Pro",
        }
        create_resp = await ac.post(
            "/assets/computers/", json=computer_payload, headers=headers
        )
        assert (
            create_resp.status_code == 201
        ), f"Computer creation failed: {create_resp.text}"
        computer = create_resp.json()
        computer_id = computer["id"]
        assert computer["type"] == "computer"
        assert computer["cpu"] == computer_payload["cpu"]

        # ---------- 3. GET computer endpoint ----------
        get_resp = await ac.get(f"/assets/computers/{computer_id}", headers=headers)
        assert get_resp.status_code == 200, f"Computer get failed: {get_resp.text}"
        assert get_resp.json()["id"] == computer_id
        assert get_resp.json()["cpu"] == computer_payload["cpu"]

        # ---------- 4. Update computer (RAM change) ----------
        update_payload = {"ram": "32GB"}
        update_resp = await ac.put(
            f"/assets/computers/{computer_id}", json=update_payload, headers=headers
        )
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        assert update_resp.json()["ram"] == "32GB"

        # ---------- 5. List computers with pagination ----------
        list_resp = await ac.get(
            "/assets/computers/", params={"page": 1, "per_page": 9999}, headers=headers
        )
        assert (
            list_resp.status_code == 200
        ), f"List with pagination failed: {list_resp.text}"
        paginated_data = list_resp.json()
        assert "data" in paginated_data and "total" in paginated_data
        assert paginated_data["total"] >= 1
        ids = [item["id"] for item in paginated_data["data"]]
        assert computer_id in ids, "Created computer missing from paginated list"

        # ---------- 6. List computers with sorting ----------
        sort_resp = await ac.get(
            "/assets/computers/",
            params={"sort_by": "name", "sort_order": "desc"},
            headers=headers,
        )
        assert (
            sort_resp.status_code == 200
        ), f"List with sorting failed: {sort_resp.text}"
        sorted_data = sort_resp.json()["data"]
        assert len(sorted_data) > 0, "Sorted list should not be empty"

        # ---------- 7. Search computers ----------
        search_resp = await ac.get(
            "/assets/computers/",
            params={"search": computer_payload["name"]},
            headers=headers,
        )
        assert search_resp.status_code == 200, f"Search failed: {search_resp.text}"
        search_data = search_resp.json()["data"]
        assert len(search_data) > 0
        ids = [item["id"] for item in search_data]
        assert computer_id in ids, "Created computer not found via search"

        # ---------- 9. Delete computer ----------
        del_resp = await ac.delete(f"/assets/computers/{computer_id}", headers=headers)
        assert del_resp.status_code == 204, f"Delete failed: {del_resp.text}"

        # ---------- 10. Confirm deletion ----------
        get_after_del = await ac.get(
            f"/assets/computers/{computer_id}", headers=headers
        )
        assert get_after_del.status_code == 404, "Deleted computer should return 404"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_all_asset_types_creation():
    """Test creation of all asset types to ensure polymorphic inheritance works."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

        test_assets = {
            "computers": {
                "name": f"E2E-Computer-{unique_suffix}",
                "status": "active",
                "cpu": "Intel Core i5",
            },
            "networkdevices": {
                "name": f"E2E-Network-{unique_suffix}",
                "status": "active",
                "device_type": "Switch",
            },
            "virtual_machines": {
                "name": f"E2E-VM-{unique_suffix}",
                "status": "active",
                "hypervisor_type": "VMware",
                "cpu_cores": 4,
                "memory_mb": 8192,
                "storage_gb": 100,
                "os_type": "Linux",
            },
        }

        created_assets = []

        # Use specific endpoints for each asset type
        for asset_type, payload in test_assets.items():
            endpoint = f"/assets/{asset_type}/"
            create_resp = await ac.post(endpoint, json=payload, headers=headers)
            assert (
                create_resp.status_code == 201
            ), f"Failed to create {asset_type}: {create_resp.text}"
            asset = create_resp.json()

            # Verify the asset type is correct
            if asset_type == "computers":
                assert asset["type"] == "computer"
            elif asset_type == "networkdevices":
                assert asset["type"] == "network_device"
            elif asset_type == "virtual_machines":
                assert asset["type"] == "virtual_machine"
            else:
                # Remove 's' from the end for the type
                expected_type = (
                    asset_type[:-1] if asset_type.endswith("s") else asset_type
                )
                assert asset["type"] == expected_type

            created_assets.append((asset_type, asset["id"]))

        # Verify each asset can be retrieved from its specific endpoint
        for asset_type, asset_id in created_assets:
            get_resp = await ac.get(f"/assets/{asset_type}/{asset_id}", headers=headers)
            assert get_resp.status_code == 200, f"Failed to get {asset_type} {asset_id}"
            assert get_resp.json()["id"] == asset_id

        # Clean up - delete all created assets
        for asset_type, asset_id in created_assets:
            del_resp = await ac.delete(
                f"/assets/{asset_type}/{asset_id}", headers=headers
            )
            assert (
                del_resp.status_code == 204
            ), f"Failed to delete {asset_type} {asset_id}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_asset_filtering_and_search():
    """Test various filtering and search scenarios."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

        test_assets = [
            {
                "name": f"Active-Computer-{unique_suffix}",
                "status": "active",
                "cpu": "Intel i5",
                "type": "computer",
            },
            {
                "name": f"Maintenance-Computer-{unique_suffix}",
                "status": "maintenance",
                "cpu": "Intel i7",
                "type": "computer",
            },
        ]

        created_ids = {}
        for asset_data in test_assets:
            create_resp = await ac.post(
                f"/assets/{asset_data['type']}/", json=asset_data, headers=headers
            )
            assert create_resp.status_code == 201
            created_ids[asset_data["name"]] = create_resp.json()["id"]

        # Test status filtering on computers
        active_resp = await ac.get(
            "/assets/computers/", params={"status": "active"}, headers=headers
        )
        assert active_resp.status_code == 200
        active_items = active_resp.json()["data"]
        assert any(
            item["id"] == created_ids[f"Active-Computer-{unique_suffix}"]
            for item in active_items
        )

        # Test search by name on computers
        search_resp = await ac.get(
            "/assets/computers/", params={"search": "Active-Computer"}, headers=headers
        )
        assert search_resp.status_code == 200
        search_items = search_resp.json()["data"]
        assert any(
            item["id"] == created_ids[f"Active-Computer-{unique_suffix}"]
            for item in search_items
        )

        # Test search on computers (should find both computers)
        search_computer_resp = await ac.get(
            "/assets/computers/",
            params={"search": "Computer"},
            headers=headers,
        )
        assert search_computer_resp.status_code == 200
        search_computer_items = search_computer_resp.json()["data"]
        assert len(search_computer_items) >= 2

        # Test pagination on computers
        paginated_resp = await ac.get(
            "/assets/computers/", params={"page": 1, "per_page": 2}, headers=headers
        )
        assert paginated_resp.status_code == 200
        paginated_items = paginated_resp.json()["data"]
        assert len(paginated_items) <= 2

        # Clean up
        for asset_id in created_ids.values():
            await ac.delete(f"/assets/computers/{asset_id}", headers=headers)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_asset_type_specific_operations():
    """Test that each asset type has its own complete CRUD operations."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

        # Test each asset type
        asset_types = [
            (
                "computers",
                {
                    "name": f"Test-Computer-{unique_suffix}",
                    "status": "active",
                    "cpu": "Intel i5",
                },
            ),
            (
                "printers",
                {
                    "name": f"Test-Printer-{unique_suffix}",
                    "status": "active",
                    "model": "HP LaserJet",
                },
            ),
            (
                "networkdevices",
                {
                    "name": f"Test-Network-{unique_suffix}",
                    "status": "active",
                    "device_type": "Switch",
                },
            ),
            (
                "phones",
                {
                    "name": f"Test-Phone-{unique_suffix}",
                    "status": "active",
                    "phone_type": "Desk Phone",
                },
            ),
            (
                "peripherals",
                {
                    "name": f"Test-Peripheral-{unique_suffix}",
                    "status": "active",
                    "peripheral_type": "Keyboard",
                },
            ),
            (
                "consumables",
                {
                    "name": f"Test-Consumable-{unique_suffix}",
                    "status": "active",
                    "consumable_type": "Toner",
                },
            ),
            (
                "racks",
                {
                    "name": f"Test-Rack-{unique_suffix}",
                    "status": "active",
                    "rack_type": "Server Rack",
                },
            ),
            (
                "cables",
                {
                    "name": f"Test-Cable-{unique_suffix}",
                    "status": "active",
                    "cable_type": "Ethernet",
                },
            ),
            (
                "simcarditems",
                {
                    "name": f"Test-SIM-{unique_suffix}",
                    "status": "active",
                    "sim_type": "Nano",
                },
            ),
        ]

        for endpoint, payload in asset_types:
            # Create
            create_resp = await ac.post(
                f"/assets/{endpoint}/", json=payload, headers=headers
            )
            assert (
                create_resp.status_code == 201
            ), f"Failed to create {endpoint}: {create_resp.text}"
            asset = create_resp.json()
            asset_id = asset["id"]

            # Read
            get_resp = await ac.get(f"/assets/{endpoint}/{asset_id}", headers=headers)
            assert (
                get_resp.status_code == 200
            ), f"Failed to get {endpoint}: {get_resp.text}"

            # Update
            update_payload = {"name": f"Updated-{payload['name']}"}
            update_resp = await ac.put(
                f"/assets/{endpoint}/{asset_id}", json=update_payload, headers=headers
            )
            assert (
                update_resp.status_code == 200
            ), f"Failed to update {endpoint}: {update_resp.text}"
            assert update_resp.json()["name"] == f"Updated-{payload['name']}"

            # List
            list_resp = await ac.get(f"/assets/{endpoint}/", headers=headers)
            assert (
                list_resp.status_code == 200
            ), f"Failed to list {endpoint}: {list_resp.text}"

            # Delete
            delete_resp = await ac.delete(
                f"/assets/{endpoint}/{asset_id}", headers=headers
            )
            assert (
                delete_resp.status_code == 204
            ), f"Failed to delete {endpoint}: {delete_resp.text}"

            # Verify deletion
            get_after_del = await ac.get(
                f"/assets/{endpoint}/{asset_id}", headers=headers
            )
            assert (
                get_after_del.status_code == 404
            ), f"Deleted {endpoint} should return 404"
