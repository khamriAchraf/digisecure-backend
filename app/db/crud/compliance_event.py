from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session, joinedload

from app.db.models.compliance_event import ComplianceEvent
from app.db.models.group import Group
from app.db.models.user import User
from app.schemas.compliance_event import (ComplianceEventCreate,
                                          ComplianceEventList,
                                          ComplianceEventUpdate)


def get_event(db: Session, event_id: int) -> Optional[ComplianceEvent]:
    return (
        db.query(ComplianceEvent)
        .options(
            joinedload(ComplianceEvent.notify_users),
            joinedload(ComplianceEvent.notify_groups),
        )
        .filter(ComplianceEvent.id == event_id)
        .first()
    )


def get_event_by_name_and_scope(
    db: Session, name: str, scope_id: int
) -> Optional[ComplianceEvent]:
    return (
        db.query(ComplianceEvent)
        .filter(ComplianceEvent.name == name, ComplianceEvent.scope_id == scope_id)
        .first()
    )


def list_events(db: Session, skip: int = 0, limit: int = 100) -> List[ComplianceEvent]:
    return db.query(ComplianceEvent).offset(skip).limit(limit).all()


def list_events_by_scope(
    db: Session, scope_id: int, skip: int = 0, limit: int = 100
) -> List[ComplianceEvent]:
    events = (
        db.query(ComplianceEvent)
        .filter(ComplianceEvent.scope_id == scope_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    for event in events:
        user_count = len(event.notify_users)
        group_count = len(event.notify_groups)
        event.notify_user_count = user_count
        event.notify_group_count = group_count
    return events


def get_paginated_events(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[ComplianceEventList], int]:
    query: Query = db.query(ComplianceEvent)

    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(ComplianceEvent, key) and value is not None and value != "":
                query = query.filter(getattr(ComplianceEvent, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                ComplianceEvent.name.ilike(search_term),
                ComplianceEvent.description.ilike(search_term),
                ComplianceEvent.frequency.ilike(search_term),
                ComplianceEvent.notes.ilike(search_term),
            )
        )

    total = query.count()

    # Apply sorting
    if sort_by and hasattr(ComplianceEvent, sort_by):
        column = getattr(ComplianceEvent, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    events = query.all()

    # For each event, count users and groups, and build ComplianceEventList
    event_list = []
    for event in events:
        user_count = (
            len(event.notify_users)
            if hasattr(event, "notify_users") and event.notify_users is not None
            else 0
        )
        group_count = (
            len(event.notify_groups)
            if hasattr(event, "notify_groups") and event.notify_groups is not None
            else 0
        )
        event_list.append(
            ComplianceEventList(
                id=event.id,
                scope_id=event.scope_id,
                name=event.name,
                description=event.description,
                frequency=event.frequency,
                next_due_date=event.next_due_date,
                last_done_date=event.last_done_date,
                notify=event.notify,
                remind_before_days=event.remind_before_days,
                notify_user_count=user_count,
                notify_group_count=group_count,
            )
        )

    return event_list, total


def create_event(db: Session, event_in: ComplianceEventCreate) -> ComplianceEvent:
    # Create the event without the many-to-many relationships
    event_data = event_in.dict(exclude={"notify_user_ids", "notify_group_ids"})
    event = ComplianceEvent(**event_data)

    db.add(event)
    try:
        db.commit()
        db.refresh(event)

        # Add users if provided
        if event_in.notify_user_ids:
            users = db.query(User).filter(User.id.in_(event_in.notify_user_ids)).all()
            event.notify_users = users
            db.commit()
            db.refresh(event)

        # Add groups if provided
        if event_in.notify_group_ids:
            groups = (
                db.query(Group).filter(Group.id.in_(event_in.notify_group_ids)).all()
            )
            event.notify_groups = groups
            db.commit()
            db.refresh(event)

    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        if "unique constraint" in msg and "uq_compliance_events_name_scope" in msg:
            raise ValueError(
                f"Compliance event with name '{event_in.name}' already exists in this scope."
            )
        raise

    return event


def update_event(
    db: Session, event: ComplianceEvent, event_in: ComplianceEventUpdate
) -> ComplianceEvent:
    # Update basic fields
    update_data = event_in.dict(
        exclude_unset=True, exclude={"notify_user_ids", "notify_group_ids"}
    )
    for field, value in update_data.items():
        setattr(event, field, value)

    # Update notify_users if provided
    if event_in.notify_user_ids is not None:
        users = db.query(User).filter(User.id.in_(event_in.notify_user_ids)).all()
        event.notify_users = users

    # Update notify_groups if provided
    if event_in.notify_group_ids is not None:
        groups = db.query(Group).filter(Group.id.in_(event_in.notify_group_ids)).all()
        event.notify_groups = groups

    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event: ComplianceEvent) -> None:
    db.delete(event)
    db.commit()
    return None


def add_user_to_event(
    db: Session, event: ComplianceEvent, user: User
) -> ComplianceEvent:
    if user not in event.notify_users:
        event.notify_users.append(user)
        db.commit()
        db.refresh(event)
    return event


def remove_user_from_event(
    db: Session, event: ComplianceEvent, user: User
) -> ComplianceEvent:
    if user in event.notify_users:
        event.notify_users.remove(user)
        db.commit()
        db.refresh(event)
    return event


def add_group_to_event(
    db: Session, event: ComplianceEvent, group: Group
) -> ComplianceEvent:
    if group not in event.notify_groups:
        event.notify_groups.append(group)
        db.commit()
        db.refresh(event)
    return event


def remove_group_from_event(
    db: Session, event: ComplianceEvent, group: Group
) -> ComplianceEvent:
    if group in event.notify_groups:
        event.notify_groups.remove(group)
        db.commit()
        db.refresh(event)
    return event
