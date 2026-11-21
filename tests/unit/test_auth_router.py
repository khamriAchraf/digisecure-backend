from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth import router
from app.db.session import get_db


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: object()

    with TestClient(app) as test_client:
        yield test_client


def test_public_registration_is_disabled(client):
    response = client.post("/api/v1/auth/register", json={})

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Public registration is disabled. Contact an administrator."
    )


def test_logout_accepts_refresh_token_in_json_body(client):
    with patch(
        "app.api.v1.auth.auth_service.revoke_refresh_token", return_value=True
    ) as revoke_refresh_token:
        response = client.post(
            "/api/v1/auth/logout", json={"refresh_token": "refresh-token"}
        )

    assert response.status_code == 200
    assert revoke_refresh_token.call_args.args[0] == "refresh-token"
    assert revoke_refresh_token.call_args.args[1] is not None


def test_logout_still_accepts_legacy_query_parameter(client):
    with patch(
        "app.api.v1.auth.auth_service.revoke_refresh_token", return_value=True
    ) as revoke_refresh_token:
        response = client.post(
            "/api/v1/auth/logout", params={"refresh_token": "refresh-token"}
        )

    assert response.status_code == 200
    assert revoke_refresh_token.call_args.args[0] == "refresh-token"


def test_logout_requires_a_refresh_token(client):
    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 422
    assert response.json()["detail"] == "refresh_token is required"
