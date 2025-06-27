import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN, TEST_USERS


@pytest.mark.integration
@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_create_and_list_users():
    # 1. Login as super-admin
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        login_data = {
            "username": SUPER_ADMIN["email"],
            "password": SUPER_ADMIN["password"],
        }
        login_resp = await ac.post("/auth/login", data=login_data)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        roles = [
            (
                TEST_USERS["admin"]["role_id"],
                TEST_USERS["admin"]["username"],
                TEST_USERS["admin"]["email"],
            ),
            (
                TEST_USERS["supervisor"]["role_id"],
                TEST_USERS["supervisor"]["username"],
                TEST_USERS["supervisor"]["email"],
            ),
            (
                TEST_USERS["technician"]["role_id"],
                TEST_USERS["technician"]["username"],
                TEST_USERS["technician"]["email"],
            ),
            (
                TEST_USERS["hotliner"]["role_id"],
                TEST_USERS["hotliner"]["username"],
                TEST_USERS["hotliner"]["email"],
            ),
            (
                TEST_USERS["observer"]["role_id"],
                TEST_USERS["observer"]["username"],
                TEST_USERS["observer"]["email"],
            ),
            (
                TEST_USERS["self_service"]["role_id"],
                TEST_USERS["self_service"]["username"],
                TEST_USERS["self_service"]["email"],
            ),
        ]
        password = TEST_USERS["admin"]["password"]
        created_user_ids = []
        for role_id, username, email in roles:
            user_data = {
                "username": username,
                "email": email,
                "password": password,
                "roles": [role_id],
            }
            resp = await ac.post("/users/", json=user_data, headers=headers)
            assert (
                resp.status_code == 201
            ), f"Failed to create user {username}: {resp.text}"
            user = resp.json()
            created_user_ids.append(user["id"])
            assert user["username"] == username
            assert user["email"] == email
            assert any(r["id"] == role_id for r in user["roles"])

        list_resp = await ac.get("/users/", headers=headers)
        assert list_resp.status_code == 200, f"List users failed: {list_resp.text}"
        users = list_resp.json()
        usernames = {u["username"] for u in users}
        for _, username, _ in roles:
            assert username in usernames, f"User {username} not found in user list!"
