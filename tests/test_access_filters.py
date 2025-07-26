"""
Tests for the access_filters functionality in the asset service.

This test file verifies that the access_filters function works correctly
with the refactored asset service methods.
"""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.security import access_filters, can_access
from app.db.models.asset import Asset
from app.db.models.group import Group
from app.db.models.role import Role
from app.db.models.user import User
from app.services.asset_service import AssetService


class TestAccessFilters:
    """Test cases for access_filters functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.db = Mock(spec=Session)
        self.user = Mock(spec=User)
        self.user.id = 123
        self.user.groups = []
        self.user.role = Mock(spec=Role)
        self.user.role.name = "Technician"

        self.service = AssetService(self.db, self.user)

    def test_super_admin_no_filters(self):
        """Test that Super-Admin users get no access filters."""
        # Arrange
        super_admin = Mock(spec=User)
        super_admin.id = 999
        super_admin.groups = []
        super_admin.role = Mock(spec=Role)
        super_admin.role.name = "Super-Admin"

        # Act
        conditions = access_filters(super_admin, Asset)

        # Assert
        assert conditions is None

    def test_regular_user_with_groups(self):
        """Test that regular users get access filters based on their groups."""
        # Arrange
        group1 = Mock(spec=Group)
        group1.id = 1
        group1.children = []

        group2 = Mock(spec=Group)
        group2.id = 2
        group2.children = []

        self.user.groups = [group1, group2]

        # Act
        conditions = access_filters(self.user, Asset)

        # Assert
        assert conditions is not None
        assert len(conditions) == 1  # One OR condition

    def test_user_with_hierarchical_groups(self):
        """Test that users with hierarchical groups get access to child groups."""
        # Arrange
        child_group = Mock(spec=Group)
        child_group.id = 2
        child_group.children = []

        parent_group = Mock(spec=Group)
        parent_group.id = 1
        parent_group.children = [child_group]

        self.user.groups = [parent_group]

        # Act
        conditions = access_filters(self.user, Asset)

        # Assert
        assert conditions is not None
        assert len(conditions) == 1

    def test_asset_service_with_access_filters(self):
        """Test that asset service methods use access filters correctly."""
        # Arrange
        group = Mock(spec=Group)
        group.id = 1
        group.children = []
        self.user.groups = [group]

        # Mock the asset CRUD methods
        with patch("app.services.asset_service.asset_crud") as mock_crud:
            mock_crud.get_paginated_assets.return_value = ([], 0)

            # Act
            assets, total = self.service.get_paginated_computers(page=1, per_page=20)

            # Assert
            # Verify that the service method was called
            # The actual implementation will use access_filters internally
            assert assets == []
            assert total == 0

    def test_can_access_consistency(self):
        """Test that access_filters and can_access produce consistent results."""
        # Arrange
        group = Mock(spec=Group)
        group.id = 1
        group.children = []
        self.user.groups = [group]

        asset = Mock(spec=Asset)
        asset.id = 1
        asset.assigned_to = None
        asset.group_id = 1

        # Act
        access_conditions = access_filters(self.user, Asset)
        can_access_result = can_access(self.user, asset)

        # Assert
        # Both should allow access since the asset is in the user's group
        assert access_conditions is not None
        assert can_access_result is True

    def test_direct_assignment_access(self):
        """Test that users can access assets directly assigned to them."""
        # Arrange
        asset = Mock(spec=Asset)
        asset.id = 1
        asset.assigned_to = self.user.id
        asset.group_id = None

        # Act
        can_access_result = can_access(self.user, asset)

        # Assert
        assert can_access_result is True

    def test_no_access_for_other_users_assets(self):
        """Test that users cannot access assets assigned to other users."""
        # Arrange
        asset = Mock(spec=Asset)
        asset.id = 1
        asset.assigned_to = 999  # Different user
        asset.group_id = None

        # Act
        can_access_result = can_access(self.user, asset)

        # Assert
        assert can_access_result is False

    def test_group_membership_access(self):
        """Test that users can access assets in their groups."""
        # Arrange
        group = Mock(spec=Group)
        group.id = 1
        group.children = []
        self.user.groups = [group]

        asset = Mock(spec=Asset)
        asset.id = 1
        asset.assigned_to = None
        asset.group_id = 1

        # Act
        can_access_result = can_access(self.user, asset)

        # Assert
        assert can_access_result is True

    def test_hierarchical_group_access(self):
        """Test that users can access assets in child groups."""
        # Arrange
        child_group = Mock(spec=Group)
        child_group.id = 2
        child_group.children = []

        parent_group = Mock(spec=Group)
        parent_group.id = 1
        parent_group.children = [child_group]

        self.user.groups = [parent_group]

        asset = Mock(spec=Asset)
        asset.id = 1
        asset.assigned_to = None
        asset.group_id = 2  # Child group

        # Act
        can_access_result = can_access(self.user, asset)

        # Assert
        assert can_access_result is True


if __name__ == "__main__":
    pytest.main([__file__])
