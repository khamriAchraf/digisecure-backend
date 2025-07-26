from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import role as role_crud
from app.db.models.role import Permission, Role
from app.db.models.user import User


class PermissionError(Exception):
    pass


class RoleService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def get_role(self, role_id: int) -> Role:
        logger.info(
            f"User {self.current_user.id} attempts to READ role {role_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "role"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to role {role_id}"
            )
            raise PermissionError("Not allowed to read roles.")
        role = role_crud.get_role(self.db, role_id)
        logger.info(f"User {self.current_user.id} successfully READ role {role_id}")
        return role

    def list_roles(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST roles at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "role"):
            logger.warning(f"User {self.current_user.id} denied LIST access to roles")
            raise PermissionError("Not allowed to list roles.")
        roles = role_crud.list_roles(self.db, skip=skip, limit=limit)
        logger.info(f"User {self.current_user.id} successfully LISTED roles")
        return roles

    def get_paginated_roles(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[Role], int]:
        logger.info(
            f"User {self.current_user.id} attempts to LIST roles at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "role"):
            logger.warning(f"User {self.current_user.id} denied LIST access to roles")
            raise PermissionError("Not allowed to list roles.")
        roles, total = role_crud.get_paginated_roles(
            self.db, page, per_page, sort_by, sort_order, search, filters
        )
        logger.info(f"User {self.current_user.id} successfully LISTED roles")
        return roles, total

    def create_role(
        self, name: str, description: Optional[str] = None, is_builtin: bool = False
    ) -> Role:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE role {name} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "role"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for role {name}"
            )
            raise PermissionError("Not allowed to create roles.")
        try:
            role = role_crud.create_role(self.db, name, description, is_builtin)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(f"User {self.current_user.id} successfully CREATED role {role.id}")
        return role

    def update_role(
        self, role: Role, name: Optional[str] = None, description: Optional[str] = None
    ) -> Role:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE role {role.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "role"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for role {role.id}"
            )
            raise PermissionError("Not allowed to update roles.")
        updated_role = role_crud.update_role(self.db, role, name, description)
        logger.info(f"User {self.current_user.id} successfully UPDATED role {role.id}")
        return updated_role

    def delete_role(self, role: Role) -> Role:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE role {role.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "role"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for role {role.id}"
            )
            raise PermissionError("Not allowed to delete roles.")
        deleted_role = role_crud.delete_role(self.db, role)
        logger.info(f"User {self.current_user.id} successfully DELETED role {role.id}")
        return deleted_role

    def assign_permission(self, role: Role, permission: Permission) -> Role:
        logger.info(
            f"User {self.current_user.id} attempts to ASSIGN permission {permission.id} to role {role.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "role"):
            logger.warning(
                f"User {self.current_user.id} denied ASSIGN permission for role {role.id}"
            )
            raise PermissionError("Not allowed to assign permissions to roles.")
        updated_role = role_crud.assign_permission(self.db, role, permission)
        logger.info(
            f"User {self.current_user.id} successfully ASSIGNED permission {permission.id} to role {role.id}"
        )
        return updated_role

    def unassign_permission(self, role: Role, permission: Permission) -> Role:
        logger.info(
            f"User {self.current_user.id} attempts to UNASSIGN permission {permission.id} from role {role.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "role"):
            logger.warning(
                f"User {self.current_user.id} denied UNASSIGN permission for role {role.id}"
            )
            raise PermissionError("Not allowed to unassign permissions from roles.")
        updated_role = role_crud.unassign_permission(self.db, role, permission)
        logger.info(
            f"User {self.current_user.id} successfully UNASSIGNED permission {permission.id} from role {role.id}"
        )
        return updated_role
