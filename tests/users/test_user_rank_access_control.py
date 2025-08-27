from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN, TEST_USERS


def _extract_user_id_from_list(users_payload, email):
    for u in users_payload:
        if u.get("email") == email:
            return u.get("id")
    return None


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_user_rank_list_unaffected_and_read_update_enforced():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # ---------- Login as Admin (has user:list, user:read, user:update) ----------
        admin_login_resp = await ac.post(
            "/auth/login",
            data={
                "username": TEST_USERS["admin"]["email"],
                "password": TEST_USERS["admin"]["password"],
            },
        )
        assert (
            admin_login_resp.status_code == 200
        ), f"Admin login failed: {admin_login_resp.text}"
        admin_headers = {
            "Authorization": f"Bearer {admin_login_resp.json()['access_token']}"
        }

        # ---------- List users should work regardless of rank ----------
        list_resp = await ac.get("/users/", headers=admin_headers)
        assert (
            list_resp.status_code == 200
        ), f"Admin should be able to list users: {list_resp.text}"
        users_response = list_resp.json()
        assert isinstance(users_response, dict) and "data" in users_response
        all_users = users_response["data"]

        # Resolve target user IDs from existing seeded users
        super_admin_email = SUPER_ADMIN["email"]
        technician_email = TEST_USERS["technician"]["email"]

        super_admin_id = _extract_user_id_from_list(all_users, super_admin_email)
        technician_id = _extract_user_id_from_list(all_users, technician_email)

        # In case pagination hid a user, fetch broader list
        if super_admin_id is None or technician_id is None:
            wide_list_resp = await ac.get(
                "/users/", params={"page": 1, "per_page": 9999}, headers=admin_headers
            )
            assert wide_list_resp.status_code == 200
            all_users = wide_list_resp.json()["data"]
            if super_admin_id is None:
                super_admin_id = _extract_user_id_from_list(
                    all_users, super_admin_email
                )
            if technician_id is None:
                technician_id = _extract_user_id_from_list(all_users, technician_email)

        assert (
            super_admin_id is not None
        ), "Could not resolve Super-Admin user id from listing"
        assert (
            technician_id is not None
        ), "Could not resolve Technician user id from listing"

        # ---------- Reading/updating LOWER rank should succeed ----------
        # Admin (rank 2) -> Technician (rank 4)
        read_lower_resp = await ac.get(f"/users/{technician_id}", headers=admin_headers)
        assert (
            read_lower_resp.status_code == 200
        ), f"Admin should read lower-rank user: {read_lower_resp.text}"

        update_lower_resp = await ac.put(
            f"/users/{technician_id}",
            json={
                "full_name": f"Updated by Admin {datetime.now(timezone.utc).isoformat()}"
            },
            headers=admin_headers,
        )
        assert (
            update_lower_resp.status_code == 200
        ), f"Admin should update lower-rank user: {update_lower_resp.text}"

        # ---------- Reading/updating HIGHER rank should fail ----------
        # Admin (rank 2) -> Super-Admin (rank 1)
        read_higher_resp = await ac.get(
            f"/users/{super_admin_id}", headers=admin_headers
        )
        assert (
            read_higher_resp.status_code == 403
        ), "Admin must not read higher-rank user (Super-Admin)"

        update_higher_resp = await ac.put(
            f"/users/{super_admin_id}",
            json={"full_name": "should-not-succeed"},
            headers=admin_headers,
        )
        assert (
            update_higher_resp.status_code == 403
        ), "Admin must not update higher-rank user (Super-Admin)"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_user_rank_rules_with_technician():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # ---------- Login as Technician (has user:list, user:read, user:update) ----------
        tech_login_resp = await ac.post(
            "/auth/login",
            data={
                "username": TEST_USERS["technician"]["email"],
                "password": TEST_USERS["technician"]["password"],
            },
        )
        assert (
            tech_login_resp.status_code == 200
        ), f"Technician login failed: {tech_login_resp.text}"
        tech_headers = {
            "Authorization": f"Bearer {tech_login_resp.json()['access_token']}"
        }

        # ---------- List users should work ----------
        list_resp = await ac.get("/users/", headers=tech_headers)
        assert (
            list_resp.status_code == 200
        ), f"Technician should be able to list users: {list_resp.text}"
        users_response = list_resp.json()
        assert isinstance(users_response, dict) and "data" in users_response
        all_users = users_response["data"]

        admin_email = TEST_USERS["admin"]["email"]  # higher rank than technician
        observer_email = TEST_USERS["observer"]["email"]  # lower rank than technician

        admin_id = _extract_user_id_from_list(all_users, admin_email)
        observer_id = _extract_user_id_from_list(all_users, observer_email)

        if admin_id is None or observer_id is None:
            wide_list_resp = await ac.get(
                "/users/", params={"page": 1, "per_page": 9999}, headers=tech_headers
            )
            assert wide_list_resp.status_code == 200
            all_users = wide_list_resp.json()["data"]
            if admin_id is None:
                admin_id = _extract_user_id_from_list(all_users, admin_email)
            if observer_id is None:
                observer_id = _extract_user_id_from_list(all_users, observer_email)

        assert admin_id is not None, "Could not resolve Admin user id from listing"
        assert (
            observer_id is not None
        ), "Could not resolve Observer user id from listing"

        # ---------- Read/update lower-rank should succeed (Technician -> Observer) ----------
        read_lower_resp = await ac.get(f"/users/{observer_id}", headers=tech_headers)
        assert (
            read_lower_resp.status_code == 200
        ), f"Technician should read lower-rank user: {read_lower_resp.text}"

        update_lower_resp = await ac.put(
            f"/users/{observer_id}",
            json={
                "full_name": f"Updated by Tech {datetime.now(timezone.utc).isoformat()}"
            },
            headers=tech_headers,
        )
        assert (
            update_lower_resp.status_code == 200
        ), f"Technician should update lower-rank user: {update_lower_resp.text}"

        # ---------- Read/update higher-rank should fail (Technician -> Admin) ----------
        read_higher_resp = await ac.get(f"/users/{admin_id}", headers=tech_headers)
        assert (
            read_higher_resp.status_code == 403
        ), "Technician must not read higher-rank user (Admin)"

        update_higher_resp = await ac.put(
            f"/users/{admin_id}",
            json={"full_name": "should-not-succeed"},
            headers=tech_headers,
        )
        assert (
            update_higher_resp.status_code == 403
        ), "Technician must not update higher-rank user (Admin)"
