from unittest.mock import Mock

import pytest

from app.core.security import (get_password_hash, has_permission,
                               verify_password)


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
        mock_user.roles = [mock_role]

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
        mock_user.roles = [mock_role]

        result = has_permission(mock_user, "read", "user")
        assert result is False

    def test_has_permission_multiple_roles(self):
        """Test that has_permission works with multiple roles."""
        mock_permission1 = Mock()
        mock_permission1.action = "read"
        mock_permission1.resource = "user"

        mock_permission2 = Mock()
        mock_permission2.action = "write"
        mock_permission2.resource = "user"

        mock_role1 = Mock()
        mock_role1.permissions = [mock_permission1]

        mock_role2 = Mock()
        mock_role2.permissions = [mock_permission2]

        mock_user = Mock()
        mock_user.roles = [mock_role1, mock_role2]

        assert has_permission(mock_user, "read", "user") is True
        assert has_permission(mock_user, "write", "user") is True
        assert has_permission(mock_user, "delete", "user") is False

    def test_has_permission_no_roles(self):
        """Test that has_permission returns False when user has no roles."""
        mock_user = Mock()
        mock_user.roles = []

        result = has_permission(mock_user, "read", "user")
        assert result is False

    def test_has_permission_role_with_no_permissions(self):
        """Test that has_permission returns False when role has no permissions."""
        mock_role = Mock()
        mock_role.permissions = []

        mock_user = Mock()
        mock_user.roles = [mock_role]

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
        mock_user.roles = [mock_role]

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
        mock_user.roles = [mock_role]

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
        mock_user.roles = [mock_role]

        assert has_permission(mock_user, "Read", "User") is True
        assert has_permission(mock_user, "read", "user") is False
        assert has_permission(mock_user, "READ", "USER") is False
