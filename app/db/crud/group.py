from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session, joinedload

from app.db.models.asset import Asset
from app.db.models.group import Group
from app.db.models.user import User
from app.schemas.group import GroupCreate, GroupList, GroupUpdate


def get_group(db: Session, group_id: int) -> Optional[Group]:
    return (
        db.query(Group)
        .options(joinedload(Group.users), joinedload(Group.assets))
        .filter(Group.id == group_id)
        .first()
    )


def get_group_by_name(db: Session, name: str) -> Optional[Group]:
    return db.query(Group).filter(Group.name == name).first()


def list_groups(db: Session, skip: int = 0, limit: int = 100) -> List[Group]:
    return db.query(Group).offset(skip).limit(limit).all()


def get_paginated_groups(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[GroupList], int]:
    query: Query = db.query(Group)

    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(Group, key) and value is not None and value != "":
                query = query.filter(getattr(Group, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Group.name.ilike(search_term),
                Group.description.ilike(search_term),
                Group.type.ilike(search_term),
            )
        )

    total = query.count()

    # Apply sorting
    if sort_by and hasattr(Group, sort_by):
        column = getattr(Group, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    groups = query.all()

    # For each group, count assets and users, and build GroupList
    group_list = []
    for group in groups:
        asset_count = (
            len(group.assets)
            if hasattr(group, "assets") and group.assets is not None
            else 0
        )
        user_count = (
            len(group.users)
            if hasattr(group, "users") and group.users is not None
            else 0
        )
        group_list.append(
            GroupList(
                id=group.id,
                name=group.name,
                type=getattr(group, "type", None),
                deleted_at=getattr(group, "deleted_at", None),
                created_at=group.created_at,
                updated_at=getattr(group, "updated_at", None),
                asset_count=asset_count,
                user_count=user_count,
            )
        )

    return group_list, total


def get_paginated_deleted_groups(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Group], int]:
    """
    Returns a paginated list of soft-deleted groups.
    """
    query: Query = (
        db.query(Group)
        .options(joinedload(Group.users), joinedload(Group.assets))
        .only_deleted()
    )

    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(Group, key) and value is not None and value != "":
                query = query.filter(getattr(Group, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Group.name.ilike(search_term),
                Group.description.ilike(search_term),
                Group.type.ilike(search_term),
            )
        )

    # Sorting (default by id asc)
    if sort_by and hasattr(Group, sort_by):
        column = getattr(Group, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    else:
        query = query.order_by(Group.id.asc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def create_group(db: Session, group_in: GroupCreate) -> Group:
    group = Group(
        name=group_in.name,
        description=group_in.description,
        type=group_in.type,
        contain_users=group_in.contain_users,
        contain_items=group_in.contain_items,
        comment=group_in.comment,
        parent_id=group_in.parent_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(group)
    try:
        db.commit()
        db.refresh(group)
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        if "unique constraint" in msg and "groups_name" in msg:
            raise ValueError(f"Group with name '{group_in.name}' already exists.")
        raise
    return group


def update_group(db: Session, group: Group, group_in: GroupUpdate) -> Group:
    for field, value in group_in.dict(exclude_unset=True).items():
        setattr(group, field, value)
    group.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, group: Group) -> None:
    group.soft_delete(db)
    db.commit()
    return None


def add_user_to_group(db: Session, group: Group, user: User) -> Group:
    if user not in group.users:
        group.users.append(user)
        group.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(group)
    return group


def remove_user_from_group(db: Session, group: Group, user: User) -> Group:
    if user in group.users:
        group.users.remove(user)
        group.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(group)
    return group


def add_asset_to_group(db: Session, group: Group, asset: Asset) -> Group:
    if asset not in group.assets:
        group.assets.append(asset)
        group.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(group)
    return group


def remove_asset_from_group(db: Session, group: Group, asset: Asset) -> Group:
    if asset in group.assets:
        group.assets.remove(asset)
        group.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(group)
    return group


def get_deleted_group(db: Session, group_id: int) -> Optional[Group]:
    """Return the group only if they are soft-deleted."""
    return db.query(Group).only_deleted().filter(Group.id == group_id).first()


def restore_group(db: Session, group_id: int) -> Optional[Group]:
    """Restore a soft-deleted group by id."""
    group = get_deleted_group(db, group_id)
    if group is None:
        return None
    group.restore()
    db.commit()
    db.refresh(group)
    return group


def purge_group(db: Session, group_id: int) -> Optional[Group]:
    """Permanently delete a group by id, only if already soft-deleted."""
    group = get_deleted_group(db, group_id)
    if group is None:
        return None
    db.delete(group)
    db.commit()
    return group
