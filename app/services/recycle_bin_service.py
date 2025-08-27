from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import asset as asset_crud
from app.db.crud import group as group_crud
from app.db.crud import user as user_crud
from app.db.models.asset import Asset
from app.db.models.group import Group
from app.db.models.user import User
from app.services.user_service import PermissionError


class RecycleBinService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def get_paginated_deleted_users(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[User], int]:
        logger.info(
            f"User {self.current_user.id} attempts to LIST recycle bin(users) at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "recycle_bin_user"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to recycle bin(users)"
            )
            raise PermissionError("Not allowed to list recycle bin(users).")
        users, total = user_crud.get_paginated_deleted_users(
            self.db, page, per_page, sort_by, sort_order, search, filters
        )
        logger.info(
            f"User {self.current_user.id} successfully LISTED recycle bin(users)"
        )
        return users, total

    def _get_paginated_deleted_groups(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[Group], int]:
        logger.info(
            f"User {self.current_user.id} attempts to LIST recycle bin(groups) at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "recycle_bin_group"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to recycle bin(groups)"
            )
            raise PermissionError("Not allowed to list recycle bin(groups).")
        groups, total = group_crud.get_paginated_deleted_groups(
            self.db, page, per_page, sort_by, sort_order, search, filters
        )
        logger.info(
            f"User {self.current_user.id} successfully LISTED recycle bin(groups)"
        )
        return groups, total

    def _get_paginated_deleted_assets_by_type(
        self,
        asset_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[Asset], int]:
        """Internal helper to list soft-deleted assets using CRUD.

        Defaults sorting to deleted_at DESC to surface most-recently deleted first.
        """
        logger.info(
            f"User {self.current_user.id} attempts to LIST recycle bin({asset_type}) at {datetime.now(timezone.utc).isoformat()}"
        )
        # Delegate to AssetService for permission and retrieval
        from app.services.asset_service import AssetService

        asset_service = AssetService(self.db, self.current_user)
        assets, total = asset_service.get_paginated_deleted_assets_by_time(
            page=page,
            per_page=per_page,
            sort_by=sort_by or "deleted_at",
            sort_order=sort_order,
            search=search,
            filters=filters,
            asset_type=asset_type,
        )
        logger.info(
            f"User {self.current_user.id} successfully LISTED recycle bin({asset_type})"
        )
        return assets, total

    def restore_asset(self, asset_id: int, asset_type: str) -> Optional[Asset]:
        """Restore a soft-deleted asset by id after permission check."""
        logger.info(
            f"User {self.current_user.id} attempts to RESTORE {asset_type} {asset_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(
            self.current_user, "restore", f"recycle_bin_{asset_type}"
        ):
            logger.warning(
                f"User {self.current_user.id} denied RESTORE access for {asset_type} {asset_id}"
            )
            raise PermissionError(f"Not allowed to restore {asset_type}s.")

        restored = asset_crud.restore_asset(self.db, asset_id)
        if restored:
            logger.info(
                f"User {self.current_user.id} successfully RESTORED {asset_type} {asset_id}"
            )
        else:
            logger.warning(
                f"User {self.current_user.id} attempted to RESTORE {asset_type} {asset_id} but it was not found"
            )
        return restored

    def purge_asset(self, asset_id: int, asset_type: str) -> Optional[Asset]:
        """Permanently delete a soft-deleted asset."""
        logger.info(
            f"User {self.current_user.id} attempts to PURGE {asset_type} {asset_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "purge", f"recycle_bin_{asset_type}"):
            logger.warning(
                f"User {self.current_user.id} denied PURGE access for {asset_type} {asset_id}"
            )
            raise PermissionError(f"Not allowed to purge {asset_type}s.")
        asset = asset_crud.purge_asset(self.db, asset_id)
        logger.info(
            f"User {self.current_user.id} successfully PURGED {asset_type} {asset_id}"
        )
        return asset

    def purge_user(self, user_id: int) -> Optional[User]:
        logger.info(
            f"User {self.current_user.id} attempts to PURGE user {user_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "purge", "recycle_bin_user"):
            logger.warning(
                f"User {self.current_user.id} denied PURGE access to user {user_id}"
            )
            raise PermissionError("Not allowed to purge users.")
        user = user_crud.purge_user(self.db, user_id)
        logger.info(f"User {self.current_user.id} successfully PURGED user {user_id}")
        return user

    def restore_user(self, user_id: int) -> Optional[User]:
        """Restore a soft-deleted user."""
        logger.info(
            f"User {self.current_user.id} attempts to RESTORE user {user_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "restore", "recycle_bin_user"):
            logger.warning(
                f"User {self.current_user.id} denied RESTORE access to user {user_id}"
            )
            raise PermissionError("Not allowed to restore users.")
        user = user_crud.restore_user(self.db, user_id)
        logger.info(f"User {self.current_user.id} successfully RESTORED user {user_id}")
        return user

    def purge_group(self, group_id: int) -> Optional[Group]:
        """Permanently delete a soft-deleted group."""
        logger.info(
            f"User {self.current_user.id} attempts to PURGE group {group_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "purge", "recycle_bin_group"):
            logger.warning(
                f"User {self.current_user.id} denied PURGE access to group {group_id}"
            )
            raise PermissionError("Not allowed to purge groups.")
        group = group_crud.purge_group(self.db, group_id)
        logger.info(f"User {self.current_user.id} successfully PURGED group {group_id}")
        return group

    def restore_group(self, group_id: int) -> Optional[Group]:
        """Restore a soft-deleted group."""
        logger.info(
            f"User {self.current_user.id} attempts to RESTORE group {group_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "restore", "recycle_bin_group"):
            logger.warning(
                f"User {self.current_user.id} denied RESTORE access to group {group_id}"
            )
            raise PermissionError("Not allowed to restore groups.")
        group = group_crud.restore_group(self.db, group_id)
        logger.info(
            f"User {self.current_user.id} successfully RESTORED group {group_id}"
        )
        return group
