from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import compliance_event as event_crud
from app.db.models.compliance_event import \
    ComplianceEvent as ComplianceEventModel
from app.db.models.group import Group
from app.db.models.user import User
from app.schemas.compliance_event import (ComplianceEventCreate,
                                          ComplianceEventUpdate)
from app.schemas.pagination import create_paginated_response


class PermissionError(Exception):
    pass


class ComplianceEventService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    # Events CRUD
    def get_event(self, event_id: int) -> ComplianceEventModel:
        logger.info(
            f"User {self.current_user.id} attempts to READ compliance event {event_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to compliance event {event_id}"
            )
            raise PermissionError("Not allowed to read compliance events.")
        event = event_crud.get_event(self.db, event_id)
        return event

    def list_events(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST compliance events at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to compliance events"
            )
            raise PermissionError("Not allowed to list compliance events.")
        return event_crud.list_events(self.db, skip=skip, limit=limit)

    def list_events_by_scope(self, scope_id: int, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST compliance events for scope {scope_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to compliance events for scope {scope_id}"
            )
            raise PermissionError("Not allowed to list compliance events.")
        return event_crud.list_events_by_scope(
            self.db, scope_id=scope_id, skip=skip, limit=limit
        )

    def get_paginated_events(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: str | None = None,
        sort_order: str = "asc",
        search: str | None = None,
        filters: dict | None = None,
    ):
        logger.info(
            f"User {self.current_user.id} attempts to LIST paginated compliance events at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to paginated compliance events"
            )
            raise PermissionError("Not allowed to list compliance events.")

        items, total = event_crud.get_paginated_events(
            self.db,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )

        return create_paginated_response(
            data=items, total=total, page=page, per_page=per_page
        )

    def create_event(self, event_in: ComplianceEventCreate):
        logger.info(
            f"User {self.current_user.id} attempts to CREATE compliance event {event_in.name} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for compliance event {event_in.name}"
            )
            raise PermissionError("Not allowed to create compliance events.")
        try:
            return event_crud.create_event(self.db, event_in)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail=str(e))

    def update_event(
        self, event: ComplianceEventModel, event_in: ComplianceEventUpdate
    ):
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE compliance event {event.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for compliance event {event.id}"
            )
            raise PermissionError("Not allowed to update compliance events.")
        return event_crud.update_event(self.db, event, event_in)

    def delete_event(self, event: ComplianceEventModel) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE compliance event {event.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for compliance event {event.id}"
            )
            raise PermissionError("Not allowed to delete compliance events.")
        try:
            event_crud.delete_event(self.db, event)
        except IntegrityError:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=409,
                detail="Compliance event is in use and cannot be deleted",
            )

    # User management for events
    def add_user_to_event(self, event_id: int, user_id: int):
        logger.info(
            f"User {self.current_user.id} attempts to ADD user {user_id} to event {event_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access to add user to event {event_id}"
            )
            raise PermissionError("Not allowed to update compliance events.")

        event = event_crud.get_event(self.db, event_id)
        if event is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Event not found")

        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="User not found")

        return event_crud.add_user_to_event(self.db, event, user)

    def remove_user_from_event(self, event_id: int, user_id: int):
        logger.info(
            f"User {self.current_user.id} attempts to REMOVE user {user_id} from event {event_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access to remove user from event {event_id}"
            )
            raise PermissionError("Not allowed to update compliance events.")

        event = event_crud.get_event(self.db, event_id)
        if event is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Event not found")

        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="User not found")

        return event_crud.remove_user_from_event(self.db, event, user)

    # Group management for events
    def add_group_to_event(self, event_id: int, group_id: int):
        logger.info(
            f"User {self.current_user.id} attempts to ADD group {group_id} to event {event_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access to add group to event {event_id}"
            )
            raise PermissionError("Not allowed to update compliance events.")

        event = event_crud.get_event(self.db, event_id)
        if event is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Event not found")

        group = self.db.query(Group).filter(Group.id == group_id).first()
        if group is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Group not found")

        return event_crud.add_group_to_event(self.db, event, group)

    def remove_group_from_event(self, event_id: int, group_id: int):
        logger.info(
            f"User {self.current_user.id} attempts to REMOVE group {group_id} from event {event_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access to remove group from event {event_id}"
            )
            raise PermissionError("Not allowed to update compliance events.")

        event = event_crud.get_event(self.db, event_id)
        if event is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Event not found")

        group = self.db.query(Group).filter(Group.id == group_id).first()
        if group is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Group not found")

        return event_crud.remove_group_from_event(self.db, event, group)
    
    def get_event_groups_and_users(self, event_id: int):
        logger.info(
            f"User {self.current_user.id} attempts to GET groups and users for event {event_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "compliance_event"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to get groups and users for event {event_id}"
            )
            raise PermissionError("Not allowed to read compliance events.")

        event = event_crud.get_event(self.db, event_id)
        if event is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Event not found")

        return {
            "notify_users": event.notify_users,
            "notify_groups": event.notify_groups,
        }
