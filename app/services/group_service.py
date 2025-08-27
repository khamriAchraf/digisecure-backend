from datetime import datetime, timezone
from typing import List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import can_access, has_permission
from app.db.crud import group as group_crud
from app.db.models.asset import Asset
from app.db.models.group import Group
from app.db.models.user import User
from app.schemas.group import GroupCreate, GroupUpdate


class PermissionError(Exception):
    pass


class GroupService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def get_group(self, group_id: int) -> Group:
        logger.info(
            f"User {self.current_user.id} attempts to READ group {group_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "group"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to group {group_id}"
            )
            raise PermissionError("Not allowed to read groups.")
        group = group_crud.get_group(self.db, group_id)
        logger.info(f"User {self.current_user.id} successfully READ group {group_id}")
        return group

    def list_groups(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST groups at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "group"):
            logger.warning(f"User {self.current_user.id} denied LIST access to groups")
            raise PermissionError("Not allowed to list groups.")
        groups = group_crud.get_groups_with_counts(self.db, skip=skip, limit=limit)
        logger.info(f"User {self.current_user.id} successfully LISTED groups")
        return groups

    def get_paginated_groups(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[Group], int]:
        logger.info(
            f"User {self.current_user.id} attempts to LIST groups at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "group"):
            logger.warning(f"User {self.current_user.id} denied LIST access to groups")
            raise PermissionError("Not allowed to list groups.")
        groups, total = group_crud.get_paginated_groups(
            self.db, page, per_page, sort_by, sort_order, search, filters
        )
        logger.info(f"User {self.current_user.id} successfully LISTED groups")
        return groups, total

    def create_group(self, group_in: GroupCreate) -> Group:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE group {group_in.name} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "group"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for group {group_in.name}"
            )
            raise PermissionError("Not allowed to create groups.")
        try:
            group = group_crud.create_group(self.db, group_in)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(
            f"User {self.current_user.id} successfully CREATED group {group.id}"
        )
        return group

    def update_group(self, group: Group, group_in: GroupUpdate) -> Group:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE group {group.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "group"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for group {group.id}"
            )
            raise PermissionError("Not allowed to update groups.")
        updated_group = group_crud.update_group(self.db, group, group_in)
        logger.info(
            f"User {self.current_user.id} successfully UPDATED group {group.id}"
        )
        return updated_group

    def delete_group(self, group: Group) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE group {group.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "group"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for group {group.id}"
            )
            raise PermissionError("Not allowed to delete groups.")
        if group.users or group.assets or group.children:
            logger.warning(
                f"User {self.current_user.id} tried to delete group {group.id} but it has dependent children"
            )
            raise PermissionError(
                "Cannot delete group with assigned users, assets, or child groups."
            )
        group_crud.delete_group(self.db, group)
        logger.info(
            f"User {self.current_user.id} successfully DELETED group {group.id}"
        )
        return None

    def add_user_to_group(self, group_id: int, user: User) -> Group:
        from app.db.crud.group import get_group

        group = get_group(self.db, group_id)
        if not group:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Group not found")

        can_add, reason = self.can_add_remove_user_from_group(group, user, "add")
        if not can_add:
            logger.warning(
                f"User {self.current_user.id} denied ADD USER access for group {group.id}: {reason}"
            )
            raise PermissionError(f"Not allowed to add users to groups: {reason}")

        logger.info(
            f"User {self.current_user.id} attempts to ADD user {user.id} to group {group.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        updated_group = group_crud.add_user_to_group(self.db, group, user)
        logger.info(
            f"User {self.current_user.id} successfully ADDED user {user.id} to group {group.id}"
        )
        return updated_group

    def remove_user_from_group(self, group_id: int, user: User) -> Group:
        from app.db.crud.group import get_group

        group = get_group(self.db, group_id)
        if not group:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Group not found")

        can_remove, reason = self.can_add_remove_user_from_group(group, user, "remove")
        if not can_remove:
            logger.warning(
                f"User {self.current_user.id} denied REMOVE USER access for group {group.id}: {reason}"
            )
            raise PermissionError(f"Not allowed to remove users from groups: {reason}")

        logger.info(
            f"User {self.current_user.id} attempts to REMOVE user {user.id} from group {group.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        updated_group = group_crud.remove_user_from_group(self.db, group, user)
        logger.info(
            f"User {self.current_user.id} successfully REMOVED user {user.id} from group {group.id}"
        )
        return updated_group

    def create_group_with_users(self, group_in):
        from app.db.crud.user import get_user

        assert hasattr(group_in, "user_ids"), "group_in must have user_ids field"
        logger.info(
            f"User {self.current_user.id} attempts to CREATE group {group_in.name} with users at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "group"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for group {group_in.name} with users"
            )
            raise PermissionError("Not allowed to create groups.")

        group = group_crud.create_group(self.db, group_in)

        for user_id in getattr(group_in, "user_ids", []):
            user = get_user(self.db, user_id)
            if user:
                can_add, reason = self.can_add_remove_user_from_group(
                    group, user, "add"
                )
                if not can_add:
                    logger.warning(
                        f"User {self.current_user.id} denied ADD USER access for group {group.id}: {reason}"
                    )
                    raise PermissionError(
                        f"Not allowed to add users to groups: {reason}"
                    )
                group = group_crud.add_user_to_group(self.db, group, user)

        logger.info(
            f"User {self.current_user.id} successfully CREATED group {group.id} with users"
        )
        return group

    def add_asset_to_group(self, group_id: int, asset: Asset) -> Group:
        from app.db.crud.group import get_group

        group = get_group(self.db, group_id)
        if not group:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Group not found")

        can_add, reason = self.can_add_remove_asset_from_group(group, asset, "add")
        if not can_add:
            logger.warning(
                f"User {self.current_user.id} denied ADD ASSET access for group {group.id}: {reason}"
            )
            raise PermissionError(f"Not allowed to add assets to groups: {reason}")

        logger.info(
            f"User {self.current_user.id} attempts to ADD asset {asset.id} to group {group.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        updated_group = group_crud.add_asset_to_group(self.db, group, asset)
        logger.info(
            f"User {self.current_user.id} successfully ADDED asset {asset.id} to group {group.id}"
        )
        return updated_group

    def remove_asset_from_group(self, group_id: int, asset: Asset) -> Group:
        from app.db.crud.group import get_group

        group = get_group(self.db, group_id)
        if not group:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Group not found")

        can_remove, reason = self.can_add_remove_asset_from_group(
            group, asset, "remove"
        )
        if not can_remove:
            logger.warning(
                f"User {self.current_user.id} denied REMOVE ASSET access for group {group.id}: {reason}"
            )
            raise PermissionError(f"Not allowed to remove assets from groups: {reason}")

        logger.info(
            f"User {self.current_user.id} attempts to REMOVE asset {asset.id} from group {group.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        updated_group = group_crud.remove_asset_from_group(self.db, group, asset)
        logger.info(
            f"User {self.current_user.id} successfully REMOVED asset {asset.id} from group {group.id}"
        )
        return updated_group

    def _can_add_remove_resource_from_group(
        self, group: Group, resource: Union[Asset, User], action: str = "add"
    ) -> Tuple[bool, str]:
        """
        Check if the current user can add/remove a resource from a group.

        This function validates:
        1. User has update permission on groups
        2. User has update permission on the resource type
        3. User can access the group
        4. User can access the resource
        5. Group is configured to contain the resource type

        Args:
            group: Group object to add/remove resource from
            resource: Resource object (Asset or User) to add/remove
            action: Either "add" or "remove"

        Returns:
            Tuple[bool, str]: (can_perform_action, reason)
        """

        if action not in ["add", "remove"]:
            return False, f"Invalid action: {action}. Must be 'add' or 'remove'"

        # 1. Check update permission on groups
        if not has_permission(self.current_user, "update", "group"):
            return False, "User does not have update permission on groups"

        # 2. Check update permission on resource type
        resource_type = resource.type if isinstance(resource, Asset) else "user"
        if not has_permission(self.current_user, "update", resource_type):
            return False, f"User does not have update permission on {resource_type}s"

        # 3. Check if user can access the group
        if not can_access(self.current_user, group):
            return False, "User cannot access the group"

        # 4. Check if user can access the resource
        if not can_access(self.current_user, resource):
            return False, f"User cannot access the {resource_type}"

        # 5. Check if group is configured to contain the resource type
        if isinstance(resource, Asset) and not group.contain_items:
            return (
                False,
                f"Group '{group.name}' is not configured to contain items/assets",
            )

        if isinstance(resource, User) and not group.contain_users:
            return False, f"Group '{group.name}' is not configured to contain users"

        # Log the permission check
        logger.info(
            f"User {self.current_user.id} {action.upper()} permission check for {resource_type} {resource.id} in group {group.id}",
            extra={
                "log_type": "permission_check",
                "user_id": self.current_user.id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource.id,
                "group_id": group.id,
                "success": True,
            },
        )

        return True, f"User can {action} {resource_type} to/from group"

    def can_add_remove_asset_from_group(
        self, group: Group, asset: Asset, action: str = "add"
    ) -> Tuple[bool, str]:
        """
        Convenience method to check if user can add/remove an asset from a group.

        Args:
            group: Group object to add/remove asset from
            asset: Asset object to add/remove
            action: Either "add" or "remove"

        Returns:
            Tuple[bool, str]: (can_perform_action, reason)
        """
        return self._can_add_remove_resource_from_group(group, asset, action)

    def can_add_remove_user_from_group(
        self, group: Group, user: User, action: str = "add"
    ) -> Tuple[bool, str]:
        """
        Convenience method to check if user can add/remove a user from a group.

        Args:
            group: Group object to add/remove user from
            user: User object to add/remove
            action: Either "add" or "remove"

        Returns:
            Tuple[bool, str]: (can_perform_action, reason)
        """
        return self._can_add_remove_resource_from_group(group, user, action)
