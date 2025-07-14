import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


# Fixture to provide an async test client
@pytest.fixture(scope="module")
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# Fixture to get an authentication token for a test user
@pytest.fixture(scope="module")
async def auth_token(async_client: AsyncClient):
    response = await async_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "admin@admin.com", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
class TestUserEndpoint:
    async def test_list_users_paginated(
        self, async_client: AsyncClient, auth_token: str
    ):
        # Test basic pagination
        response = await async_client.get(
            f"{settings.API_V1_STR}/users?page=1&per_page=5",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 5
        assert len(data["data"]) <= 5
        assert "total" in data
        assert "total_pages" in data

    async def test_filter_users_by_status(
        self, async_client: AsyncClient, auth_token: str
    ):
        # Test filtering by status
        response = await async_client.get(
            f"{settings.API_V1_STR}/users?status=active",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        for user in data["data"]:
            assert user["status"] == "active"

    async def test_search_users(self, async_client: AsyncClient, auth_token: str):
        # Test searching for a specific user
        # This assumes a user 'admin' exists from seeding
        response = await async_client.get(
            f"{settings.API_V1_STR}/users?search=admin",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) > 0
        assert any("admin" in user["username"].lower() for user in data["data"])

    async def test_sort_users(self, async_client: AsyncClient, auth_token: str):
        # Test sorting by username
        response = await async_client.get(
            f"{settings.API_V1_STR}/users?sort_by=username&sort_order=asc",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        usernames = [user["username"] for user in data["data"]]
        assert usernames == sorted(usernames)

        response = await async_client.get(
            f"{settings.API_V1_STR}/users?sort_by=username&sort_order=desc",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        usernames = [user["username"] for user in data["data"]]
        assert usernames == sorted(usernames, reverse=True)
