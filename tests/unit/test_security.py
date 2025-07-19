from unittest.mock import Mock

import pytest

from app.core.security import (get_password_hash, has_permission,
                               has_permission_from_token, verify_password)


@pytest.mark.unit
class TestPasswordFunctions:
    """Unit tests for password hashing and verification functions."""

    def test_get_password_hash(self):
        """Test that password hashing works correctly."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > len(password)

    def test_verify_password_correct(self):
        """Test that password verification works with correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        result = verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """Test that password verification fails with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword123"
        hashed = get_password_hash(password)

        result = verify_password(wrong_password, hashed)
        assert result is False

    def test_verify_password_empty(self):
        """Test password verification with empty strings."""
        password = ""
        hashed = get_password_hash(password)

        result = verify_password(password, hashed)
        assert result is True

        result = verify_password("wrong", hashed)
        assert result is False


@pytest.mark.unit
class TestHasPermission:
    """Unit tests for the has_permission function."""

    def test_has_permission_with_matching_permission(self):
        """Test that has_permission returns True when user has matching permission."""
        # Create mock permission
        mock_permission = Mock()
        mock_permission.action = "read"
        mock_permission.resource = "user"

        mock_role = Mock()
        mock_role.permissions = [mock_permission]

        mock_user = Mock()
        mock_user.role = mock_role

        result = has_permission(mock_user, "read", "user")
        assert result is True

    def test_has_permission_without_matching_permission(self):
        """Test that has_permission returns False when user lacks permission."""
        mock_permission = Mock()
        mock_permission.action = "write"
        mock_permission.resource = "user"

        mock_role = Mock()
        mock_role.permissions = [mock_permission]

        mock_user = Mock()
        mock_user.role = mock_role

        result = has_permission(mock_user, "read", "user")
        assert result is False

    def test_has_permission_single_role(self):
        """Test that has_permission works with a single role."""
        mock_permission1 = Mock()
        mock_permission1.action = "read"
        mock_permission1.resource = "user"

        mock_permission2 = Mock()
        mock_permission2.action = "write"
        mock_permission2.resource = "user"

        mock_role = Mock()
        mock_role.permissions = [mock_permission1, mock_permission2]

        mock_user = Mock()
        mock_user.role = mock_role

        assert has_permission(mock_user, "read", "user") is True
        assert has_permission(mock_user, "write", "user") is True
        assert has_permission(mock_user, "delete", "user") is False

    def test_has_permission_no_role(self):
        """Test that has_permission returns False when user has no role."""
        mock_user = Mock()
        mock_user.role = None

        result = has_permission(mock_user, "read", "user")
        assert result is False

    def test_has_permission_role_with_no_permissions(self):
        """Test that has_permission returns False when role has no permissions."""
        mock_role = Mock()
        mock_role.permissions = []

        mock_user = Mock()
        mock_user.role = mock_role

        result = has_permission(mock_user, "read", "user")
        assert result is False

    def test_has_permission_different_resource(self):
        """Test that has_permission correctly handles different resources."""
        mock_permission = Mock()
        mock_permission.action = "read"
        mock_permission.resource = "ticket"

        mock_role = Mock()
        mock_role.permissions = [mock_permission]

        mock_user = Mock()
        mock_user.role = mock_role

        assert has_permission(mock_user, "read", "ticket") is True
        assert has_permission(mock_user, "read", "user") is False

    def test_has_permission_different_action(self):
        """Test that has_permission correctly handles different actions."""
        mock_permission = Mock()
        mock_permission.action = "create"
        mock_permission.resource = "user"

        mock_role = Mock()
        mock_role.permissions = [mock_permission]

        mock_user = Mock()
        mock_user.role = mock_role

        assert has_permission(mock_user, "create", "user") is True
        assert has_permission(mock_user, "read", "user") is False

    def test_has_permission_case_sensitive(self):
        """Test that has_permission is case sensitive."""
        mock_permission = Mock()
        mock_permission.action = "Read"
        mock_permission.resource = "User"

        mock_role = Mock()
        mock_role.permissions = [mock_permission]

        mock_user = Mock()
        mock_user.role = mock_role

        assert has_permission(mock_user, "Read", "User") is True
        assert has_permission(mock_user, "read", "user") is False
        assert has_permission(mock_user, "READ", "USER") is False


@pytest.mark.unit
class TestHasPermissionFromToken:
    """Unit tests for the has_permission_from_token function."""

    def test_has_permission_from_token_with_matching_permission(self):
        """Test that has_permission_from_token returns True when token has matching permission."""
        token_payload = {
            "sub": "123",
            "email": "test@example.com",
            "role_id": 1,
            "permissions": ["user:read", "user:create", "role:read"],
        }

        result = has_permission_from_token(token_payload, "read", "user")
        assert result is True

    def test_has_permission_from_token_without_matching_permission(self):
        """Test that has_permission_from_token returns False when token lacks permission."""
        token_payload = {
            "sub": "123",
            "email": "test@example.com",
            "role_id": 1,
            "permissions": ["user:write", "user:create", "role:read"],
        }

        result = has_permission_from_token(token_payload, "read", "user")
        assert result is False

    def test_has_permission_from_token_multiple_permissions(self):
        """Test that has_permission_from_token works with multiple permissions."""
        token_payload = {
            "sub": "123",
            "email": "test@example.com",
            "role_id": 1,
            "permissions": ["user:read", "user:create", "user:update", "role:read"],
        }

        assert has_permission_from_token(token_payload, "read", "user") is True
        assert has_permission_from_token(token_payload, "create", "user") is True
        assert has_permission_from_token(token_payload, "update", "user") is True
        assert has_permission_from_token(token_payload, "delete", "user") is False

    def test_has_permission_from_token_no_permissions(self):
        """Test that has_permission_from_token returns False when token has no permissions."""
        token_payload = {
            "sub": "123",
            "email": "test@example.com",
            "role_id": 1,
            "permissions": [],
        }

        result = has_permission_from_token(token_payload, "read", "user")
        assert result is False

    def test_has_permission_from_token_missing_permissions_key(self):
        """Test that has_permission_from_token returns False when permissions key is missing."""
        token_payload = {"sub": "123", "email": "test@example.com", "role_id": 1}

        result = has_permission_from_token(token_payload, "read", "user")
        assert result is False

    def test_has_permission_from_token_different_resource(self):
        """Test that has_permission_from_token correctly handles different resources."""
        token_payload = {
            "sub": "123",
            "email": "test@example.com",
            "role_id": 1,
            "permissions": ["user:read", "ticket:create"],
        }

        assert has_permission_from_token(token_payload, "read", "user") is True
        assert has_permission_from_token(token_payload, "create", "ticket") is True
        assert has_permission_from_token(token_payload, "read", "ticket") is False

    def test_has_permission_from_token_different_action(self):
        """Test that has_permission_from_token correctly handles different actions."""
        token_payload = {
            "sub": "123",
            "email": "test@example.com",
            "role_id": 1,
            "permissions": ["user:create", "user:update"],
        }

        assert has_permission_from_token(token_payload, "create", "user") is True
        assert has_permission_from_token(token_payload, "update", "user") is True
        assert has_permission_from_token(token_payload, "read", "user") is False

    def test_has_permission_from_token_case_sensitive(self):
        """Test that has_permission_from_token is case sensitive."""
        token_payload = {
            "sub": "123",
            "email": "test@example.com",
            "role_id": 1,
            "permissions": ["User:Read", "Role:Create"],
        }

        assert has_permission_from_token(token_payload, "Read", "User") is True
        assert has_permission_from_token(token_payload, "read", "user") is False
        assert has_permission_from_token(token_payload, "READ", "USER") is False
