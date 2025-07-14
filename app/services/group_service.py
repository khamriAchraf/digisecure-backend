from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import group as group_crud
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
            f"User {self.current_user.id} attempts to READ group {group_id} at {datetime.utcnow().isoformat()}"
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
            f"User {self.current_user.id} attempts to LIST groups at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "group"):
            logger.warning(f"User {self.current_user.id} denied LIST access to groups")
            raise PermissionError("Not allowed to list groups.")
        groups = group_crud.list_groups(self.db, skip=skip, limit=limit)
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
            f"User {self.current_user.id} attempts to LIST groups at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "group"):
            logger.warning(f"User {self.current_user.id} denied LIST access to groups")
            raise PermissionError("Not allowed to list groups.")
        groups, total = group_crud.get_paginated_groups(
            self.db, page, per_page, sort_by, sort_order, search, filters
        )
        logger.info(f"User {self.current_user.id} successfully LISTED groups")
        return groups, total

    def create_group(self, group_in: GroupCreate) -> Group:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE group {group_in.name} at {datetime.utcnow().isoformat()}"
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
            f"User {self.current_user.id} attempts to UPDATE group {group.id} at {datetime.utcnow().isoformat()}"
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
            f"User {self.current_user.id} attempts to DELETE group {group.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "group"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for group {group.id}"
            )
            raise PermissionError("Not allowed to delete groups.")
        group_crud.delete_group(self.db, group)
        logger.info(
            f"User {self.current_user.id} successfully DELETED group {group.id}"
        )

    def add_user_to_group(self, group_id: int, user: User) -> Group:
        from app.db.crud.group import get_group

        group = get_group(self.db, group_id)
        if not group:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Group not found")
        logger.info(
            f"User {self.current_user.id} attempts to ADD user {user.id} to group {group.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "update", "group"):
            logger.warning(
                f"User {self.current_user.id} denied ADD USER access for group {group.id}"
            )
            raise PermissionError("Not allowed to add users to groups.")
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
        logger.info(
            f"User {self.current_user.id} attempts to REMOVE user {user.id} from group {group.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "update", "group"):
            logger.warning(
                f"User {self.current_user.id} denied REMOVE USER access for group {group.id}"
            )
            raise PermissionError("Not allowed to remove users from groups.")
        updated_group = group_crud.remove_user_from_group(self.db, group, user)
        logger.info(
            f"User {self.current_user.id} successfully REMOVED user {user.id} from group {group.id}"
        )
        return updated_group

    def create_group_with_users(self, group_in):
        from app.db.crud.user import get_user

        assert hasattr(group_in, "user_ids"), "group_in must have user_ids field"
        logger.info(
            f"User {self.current_user.id} attempts to CREATE group {group_in.name} with users at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "create", "group"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for group {group_in.name} with users"
            )
            raise PermissionError("Not allowed to create groups.")
        # Create the group first
        group = group_crud.create_group(self.db, group_in)
        # Add users
        for user_id in getattr(group_in, "user_ids", []):
            user = get_user(self.db, user_id)
            if user:
                group = group_crud.add_user_to_group(self.db, group, user)
        logger.info(
            f"User {self.current_user.id} successfully CREATED group {group.id} with users"
        )
        return group
