import pytest


@pytest.mark.anyio
async def test_root(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "API is alive"}
