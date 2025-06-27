import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.db.models.role import Permission, Role, role_permissions, user_roles
from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import app


@pytest.mark.integration
@pytest.mark.run(order=1)
@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "API is alive"}


@pytest.mark.integration
@pytest.mark.run(order=2)
def test_app_running_in_test_mode():
    """Test that the app is running with test settings."""
    assert (
        settings.DB_SCHEMA == "test"
    ), f"Expected DB_SCHEMA to be 'test', but got '{settings.DB_SCHEMA}'"

    import os

    assert (
        os.getenv("TESTING") == "true"
    ), "TESTING environment variable should be set to 'true'"


@pytest.mark.integration
@pytest.mark.run(order=3)
def test_db_seeded_correctly():
    """Test that the database contains required tables and data."""
    session = SessionLocal()
    try:
        user_count = (
            session.execute(select(func.count()).select_from(User)).scalar() or 0
        )
        assert user_count > 0, "Users table is empty!"
        admin = session.execute(
            select(User).where(
                User.username == "admin", User.email == "admin@admin.com"
            )
        ).scalar_one_or_none()
        assert admin is not None, "Admin user not found!"

        role_count = (
            session.execute(select(func.count()).select_from(Role)).scalar() or 0
        )
        assert role_count > 0, "Roles table is empty!"

        perm_count = (
            session.execute(select(func.count()).select_from(Permission)).scalar() or 0
        )
        assert perm_count > 0, "Permissions table is empty!"

        user_roles_count = (
            session.execute(select(func.count()).select_from(user_roles)).scalar() or 0
        )
        assert user_roles_count > 0, "user_roles table is empty!"

        role_permissions_count = (
            session.execute(select(func.count()).select_from(role_permissions)).scalar()
            or 0
        )
        assert role_permissions_count > 0, "role_permissions table is empty!"
    finally:
        session.close()
