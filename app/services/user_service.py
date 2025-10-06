from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import can_access, get_password_hash, has_permission
from app.db.crud import user as user_crud
from app.db.models.user import User
from app.schemas.user import UserCreate, UserList, UserUpdate
from app.services.email_service import send_welcome_email


class PermissionError(Exception):
    pass


class UserService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def get_own_user(self) -> User:
        logger.info(
            f"User {self.current_user.id} accessed their own data at {datetime.now(timezone.utc).isoformat()}"
        )
        return self.current_user

    def get_user(self, user_id: int) -> User:
        logger.info(
            f"User {self.current_user.id} attempts to READ user {user_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "user"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to user {user_id}"
            )
            raise PermissionError("Not allowed to read users.")
        user = user_crud.get_user(self.db, user_id)
        if not can_access(self.current_user, user):
            logger.warning(
                f"User {self.current_user.id} denied READ access to user {user_id}"
            )
            raise PermissionError("Not allowed to read this user (hierarchy issue).")
        logger.info(f"User {self.current_user.id} successfully READ user {user_id}")
        return user

    def get_paginated_users(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[UserList], int]:
        logger.info(
            f"User {self.current_user.id} attempts to LIST users at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "user"):
            logger.warning(f"User {self.current_user.id} denied LIST access to users")
            raise PermissionError("Not allowed to list users.")
        users, total = user_crud.get_paginated_users(
            self.db, page, per_page, sort_by, sort_order, search, filters
        )
        logger.info(f"User {self.current_user.id} successfully LISTED users")
        return users, total

    # ---------------------------------------------------------------------
    # Cursor-based pagination (infinite scrolling)
    # ---------------------------------------------------------------------

    def get_cursor_users(
        self,
        cursor: Optional[int] = None,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[User], int]:
        """Return a slice of users suitable for cursor-based infinite scrolling."""

        logger.info(
            f"User {self.current_user.id} attempts to LIST users with cursor at {datetime.now(timezone.utc).isoformat()}"
        )

        if not has_permission(self.current_user, "list", "user"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to users (cursor)"
            )
            raise PermissionError("Not allowed to list users.")

        users, total = user_crud.get_cursor_users(
            self.db,
            cursor,
            per_page,
            sort_by,
            sort_order,
            search,
            filters,
        )

        logger.info(f"User {self.current_user.id} successfully LISTED users via cursor")
        return users, total

    def create_user(self, user_in: UserCreate) -> User:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE user {user_in.email} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "user"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for user {user_in.email}"
            )
            raise PermissionError("Not allowed to create users.")
        try:
            # Store the plain password before hashing (for email)
            plain_password = user_in.password
            hashed_password = get_password_hash(user_in.password)
            user = user_crud.create_user(self.db, user_in, hashed_password)

            # Send welcome email with credentials
            email_sent = send_welcome_email(
                email=user.email,
                username=user.username,
                password=plain_password,
                user_full_name=user.full_name,
            )

            if email_sent:
                logger.info(
                    f"Welcome email with credentials sent to {user.email} for user {user.id}"
                )
            else:
                logger.warning(
                    f"Failed to send welcome email to {user.email} for user {user.id}. "
                    f"User created successfully but should be notified manually."
                )
                # Don't fail user creation if email fails

        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(f"User {self.current_user.id} successfully CREATED user {user.id}")
        return user

    def update_user(self, user: User, user_in: UserUpdate) -> User:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE user {user.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "user"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for user {user.id}"
            )
            raise PermissionError("Not allowed to update users.")
        updated_user = user_crud.update_user(self.db, user, user_in)
        logger.info(f"User {self.current_user.id} successfully UPDATED user {user.id}")
        return updated_user

    def delete_user(self, user: User) -> User:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE user {user.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "user"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for user {user.id}"
            )
            raise PermissionError("Not allowed to delete users.")
        if not can_access(self.current_user, user):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access to user {user.id}"
            )
            raise PermissionError("Not allowed to delete this user (hierarchy issue).")
        user_crud.delete_user(self.db, user)
        logger.info(f"User {self.current_user.id} successfully DELETED user {user.id}")
        return None

    def get_user_permissions(self, user: User) -> list[dict]:
        """
        Returns all permissions of the user in the format {'action': ..., 'resource': ...}
        """
        logger.info(
            f"User {self.current_user.id} attempts to GET permissions for user {user.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "user"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to user {user.id}"
            )
            raise PermissionError("Not allowed to read user permissions.")
        permissions = set()
        role = user.role
        for perm in role.permissions:
            permissions.add((perm.action, perm.resource))
        # Return as list of dicts
        return [
            {"action": action, "resource": resource} for action, resource in permissions
        ]

    def get_user_by_identifier(self, identifier: str) -> User:
        """
        Fetch a user by id (int), username, or email.
        """
        logger.info(
            f"User {self.current_user.id} attempts to GET user {identifier} by identifier at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "user"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to user {identifier}"
            )
            raise PermissionError("Not allowed to read user.")
        query = self.db.query(User)
        if identifier.isdigit():
            user = query.filter(User.id == int(identifier)).first()
            if user:
                return user
        # Try username or email
        user = query.filter(
            or_(User.username == identifier, User.email == identifier)
        ).first()
        return user
