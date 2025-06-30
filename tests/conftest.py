# tests/conftest.py

import pytest


@pytest.fixture(autouse=True, scope="session")
def load_permissions_cache_once():
    from app.main import load_permissions_cache

    load_permissions_cache()
