from datetime import datetime

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
        unique_suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
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

        # ---------- 3. GET generic endpoint ----------
        get_resp = await ac.get(f"/assets/{computer_id}", headers=headers)
        assert get_resp.status_code == 200, f"Generic get failed: {get_resp.text}"
        assert get_resp.json()["id"] == computer_id

        # ---------- 4. GET subtype endpoint ----------
        get_sub_resp = await ac.get(f"/assets/computers/{computer_id}", headers=headers)
        assert (
            get_sub_resp.status_code == 200
        ), f"Subtype get failed: {get_sub_resp.text}"
        assert get_sub_resp.json()["cpu"] == computer_payload["cpu"]

        # ---------- 5. Update asset (RAM change) ----------
        update_payload = {"ram": "32GB"}
        update_resp = await ac.put(
            f"/assets/computers/{computer_id}", json=update_payload, headers=headers
        )
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        assert update_resp.json()["ram"] == "32GB"

        # ---------- 6. List with pagination ----------
        list_resp = await ac.get(
            "/assets/", params={"page": 1, "per_page": 9999}, headers=headers
        )
        assert (
            list_resp.status_code == 200
        ), f"List with pagination failed: {list_resp.text}"
        paginated_data = list_resp.json()
        assert "data" in paginated_data and "total" in paginated_data
        assert paginated_data["total"] >= 1
        ids = [item["id"] for item in paginated_data["data"]]
        assert computer_id in ids, "Created computer missing from paginated list"

        # ---------- 7. List with sorting ----------
        sort_resp = await ac.get(
            "/assets/",
            params={"sort_by": "name", "sort_order": "desc"},
            headers=headers,
        )
        assert (
            sort_resp.status_code == 200
        ), f"List with sorting failed: {sort_resp.text}"
        sorted_data = sort_resp.json()["data"]
        assert len(sorted_data) > 0, "Sorted list should not be empty"

        # ---------- 8. Search endpoint ----------
        search_resp = await ac.get(
            "/assets/", params={"search": computer_payload["name"]}, headers=headers
        )
        assert search_resp.status_code == 200, f"Search failed: {search_resp.text}"
        search_data = search_resp.json()["data"]
        assert len(search_data) > 0
        ids = [item["id"] for item in search_data]
        assert computer_id in ids, "Created computer not found via search"

        # ---------- 9. Analytics counts ----------
        count_resp = await ac.get("/assets/analytics/counts/by-type", headers=headers)
        assert count_resp.status_code == 200, f"Analytics failed: {count_resp.text}"
        counts = count_resp.json()
        assert (
            "computer" in counts and counts["computer"] >= 1
        ), "Analytics count missing or incorrect"

        # ---------- 10. Delete asset ----------
        del_resp = await ac.delete(f"/assets/{computer_id}", headers=headers)
        assert del_resp.status_code == 204, f"Delete failed: {del_resp.text}"

        # ---------- 11. Confirm deletion ----------
        get_after_del = await ac.get(f"/assets/{computer_id}", headers=headers)
        assert get_after_del.status_code == 404, "Deleted asset should return 404"


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
        unique_suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

        test_assets = {
            "network_device": {
                "name": f"E2E-Network-{unique_suffix}",
                "status": "active",
                "device_type": "Switch",
            },
            "phone": {
                "name": f"E2E-Phone-{unique_suffix}",
                "status": "active",
                "phone_type": "Desk Phone",
            },
            "peripheral": {
                "name": f"E2E-Peripheral-{unique_suffix}",
                "status": "active",
                "peripheral_type": "Keyboard",
            },
            "consumable": {
                "name": f"E2E-Consumable-{unique_suffix}",
                "status": "active",
                "consumable_type": "Toner",
            },
            "rack": {
                "name": f"E2E-Rack-{unique_suffix}",
                "status": "active",
                "rack_type": "Server Rack",
            },
            "cable": {
                "name": f"E2E-Cable-{unique_suffix}",
                "status": "active",
                "cable_type": "Ethernet",
            },
            "sim_card_item": {
                "name": f"E2E-SIM-{unique_suffix}",
                "status": "active",
                "sim_type": "Nano",
            },
        }

        created_assets = []

        # Use specific endpoints for each asset type
        for asset_type, payload in test_assets.items():
            if asset_type == "network_device":
                endpoint = "/assets/networkdevices/"
            elif asset_type == "sim_card_item":
                endpoint = "/assets/simcarditems/"
            else:
                endpoint = f"/assets/{asset_type}s/"
            create_resp = await ac.post(endpoint, json=payload, headers=headers)
            assert (
                create_resp.status_code == 201
            ), f"Failed to create {asset_type}: {create_resp.text}"
            asset = create_resp.json()
            assert asset["type"] == asset_type
            created_assets.append(asset["id"])

        list_resp = await ac.get("/assets/", headers=headers)
        assert list_resp.status_code == 200
        global_ids = [item["id"] for item in list_resp.json()["data"]]
        for asset_id in created_assets:
            assert asset_id in global_ids

        for asset_id in created_assets:
            await ac.delete(f"/assets/{asset_id}", headers=headers)


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
        unique_suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

        test_assets = [
            {
                "name": f"Active-Computer-{unique_suffix}",
                "status": "active",
                "cpu": "Intel i5",
            },
            {
                "name": f"Inactive-Printer-{unique_suffix}",
                "status": "inactive",
                "model": "HP LaserJet",
            },
            {
                "name": f"Maintenance-Computer-{unique_suffix}",
                "status": "maintenance",
                "cpu": "Intel i7",
            },
        ]

        created_ids = {}
        # Create computers using the computers endpoint
        for i, asset_data in enumerate(test_assets):
            if "cpu" in asset_data:  # Computer
                create_resp = await ac.post(
                    "/assets/computers/", json=asset_data, headers=headers
                )
            else:  # Printer
                create_resp = await ac.post(
                    "/assets/printers/", json=asset_data, headers=headers
                )
            assert create_resp.status_code == 201
            created_ids[asset_data["name"]] = create_resp.json()["id"]

        # Test status filtering
        active_resp = await ac.get(
            "/assets/", params={"status": "active"}, headers=headers
        )
        assert active_resp.status_code == 200
        active_items = active_resp.json()["data"]
        assert any(
            item["id"] == created_ids[f"Active-Computer-{unique_suffix}"]
            for item in active_items
        )

        # Test search by name
        search_resp = await ac.get(
            "/assets/", params={"search": "Active-Computer"}, headers=headers
        )
        assert search_resp.status_code == 200
        search_items = search_resp.json()["data"]
        assert any(
            item["id"] == created_ids[f"Active-Computer-{unique_suffix}"]
            for item in search_items
        )

        # Test search with asset type filter
        search_filtered_resp = await ac.get(
            "/assets/",
            params={"search": "Computer", "asset_type": "computer"},
            headers=headers,
        )
        assert search_filtered_resp.status_code == 200
        search_filtered_items = search_filtered_resp.json()["data"]
        assert len(search_filtered_items) >= 2

        # Test pagination
        paginated_resp = await ac.get(
            "/assets/", params={"page": 1, "per_page": 2}, headers=headers
        )
        assert paginated_resp.status_code == 200
        paginated_items = paginated_resp.json()["data"]
        assert len(paginated_items) <= 2

        for asset_id in created_ids.values():
            await ac.delete(f"/assets/{asset_id}", headers=headers)
