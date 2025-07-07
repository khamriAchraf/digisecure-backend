from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import user as user_crud
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class PermissionError(Exception):
    pass


class UserService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def get_own_user(self) -> User:
        logger.info(
            f"User {self.current_user.id} accessed their own data at {datetime.utcnow().isoformat()}"
        )
        return self.current_user

    def get_user(self, user_id: int) -> User:
        logger.info(
            f"User {self.current_user.id} attempts to READ user {user_id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "user"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to user {user_id}"
            )
            raise PermissionError("Not allowed to read users.")
        user = user_crud.get_user(self.db, user_id)
        logger.info(f"User {self.current_user.id} successfully READ user {user_id}")
        return user

    def list_users(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST users at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "user"):
            logger.warning(f"User {self.current_user.id} denied LIST access to users")
            raise PermissionError("Not allowed to list users.")
        users = user_crud.list_users(self.db, skip=skip, limit=limit)
        logger.info(f"User {self.current_user.id} successfully LISTED users")
        return users

    def create_user(self, user_in: UserCreate, hashed_password: str) -> User:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE user {user_in.email} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "create", "user"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for user {user_in.email}"
            )
            raise PermissionError("Not allowed to create users.")
        try:
            user = user_crud.create_user(self.db, user_in, hashed_password)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(f"User {self.current_user.id} successfully CREATED user {user.id}")
        return user

    def update_user(self, user: User, user_in: UserUpdate) -> User:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE user {user.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "update", "user"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for user {user.id}"
            )
            raise PermissionError("Not allowed to update users.")
        updated_user = user_crud.update_user(self.db, user, user_in)
        logger.info(f"User {self.current_user.id} successfully UPDATED user {user.id}")
        return updated_user

    def soft_delete_user(self, user: User) -> User:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE user {user.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "user"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for user {user.id}"
            )
            raise PermissionError("Not allowed to delete users.")
        deleted_user = user_crud.soft_delete_user(self.db, user)
        logger.info(f"User {self.current_user.id} successfully DELETED user {user.id}")
        return deleted_user

    def search_users(self, **kwargs):
        logger.info(
            f"User {self.current_user.id} attempts to SEARCH users at {datetime.utcnow().isoformat()} with filters {kwargs}"
        )
        if not has_permission(self.current_user, "read", "user"):
            logger.warning(f"User {self.current_user.id} denied SEARCH access to users")
            raise PermissionError("Not allowed to search users.")
        users = user_crud.search_users(self.db, **kwargs)
        logger.info(f"User {self.current_user.id} successfully SEARCHED users")
        return users

    def get_user_permissions(self, user: User) -> list[dict]:
        """
        Returns all permissions of the user in the format {'action': ..., 'resource': ...}
        """
        permissions = set()
        for role in user.roles:
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
