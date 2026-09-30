from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from app.db.models.role import Permission, Role


def get_role(db: Session, role_id: int) -> Optional[Role]:
    query= db.query(Role)
    query=exclude_system_roles(query)
    return query.filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    query= db.query(Role)
    query=exclude_system_roles(query)
    return query.filter(Role.name == name).first()


def list_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
    query= db.query(Role)
    query=exclude_system_roles(query)
    return query.offset(skip).limit(limit).all()


def get_paginated_roles(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Role], int]:
    query: Query = db.query(Role)
    query=exclude_system_roles(query)

    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(Role, key) and value is not None and value != "":
                query = query.filter(getattr(Role, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Role.name.ilike(search_term),
                Role.description.ilike(search_term),
            )
        )

    total = query.count()

    # Apply sorting
    if sort_by and hasattr(Role, sort_by):
        column = getattr(Role, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    roles = query.all()
    return roles, total


def get_paginated_roles_below_rank(
    db: Session,
    max_rank: int,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Role], int]:
    query: Query = db.query(Role).filter(Role.rank > max_rank)
    query = exclude_system_roles(query)
    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(Role, key) and value is not None and value != "":
                query = query.filter(getattr(Role, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Role.name.ilike(search_term),
                Role.description.ilike(search_term),
            )
        )

    total = query.count()

    # Apply sorting
    if sort_by and hasattr(Role, sort_by):
        column = getattr(Role, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    query = exclude_system_roles(query)
    roles = query.all()
    return roles, total


def get_paginated_deleted_roles(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Role], int]:
    """
    Returns a paginated list of soft-deleted roles.
    """
    query: Query = db.query(Role).only_deleted()

    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(Role, key) and value is not None and value != "":
                query = query.filter(getattr(Role, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Role.name.ilike(search_term),
                Role.description.ilike(search_term),
            )
        )

    # Apply sorting
    if sort_by and hasattr(Role, sort_by):
        column = getattr(Role, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    else:
        query = query.order_by(Role.id.asc())

    # Apply pagination
    total = query.count()
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    roles = query.all()
    return roles, total


def create_role(
    db: Session,
    name: str,
    rank: int,
    description: Optional[str] = None,
    is_builtin: bool = False,
) -> Role:
    role = Role(name=name, description=description, is_builtin=is_builtin, rank=rank)
    db.add(role)
    try:
        db.commit()
        db.refresh(role)
    except IntegrityError as e:
        db.rollback()
        if "unique constraint" in str(e.orig).lower() and "roles_name_key" in str(
            e.orig
        ):
            raise ValueError(f"Role with name '{name}' already exists.")
        raise
    return role


def update_role(
    db: Session,
    role: Role,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Role:
    if name is not None:
        setattr(role, "name", name)
    if description is not None:
        setattr(role, "description", description)
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role: Role) -> Role:
    role.soft_delete(db)
    db.commit()
    return role


def assign_permission(db: Session, role: Role, permission: Permission) -> Role:
    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()
        db.refresh(role)
    return role


def unassign_permission(db: Session, role: Role, permission: Permission) -> Role:
    if permission in role.permissions:
        role.permissions.remove(permission)
        db.commit()
        db.refresh(role)
    return role


def list_roles_below_rank(
    db: Session,
    max_rank: int,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> List[Role]:
    query: Query = db.query(Role).filter(Role.rank > max_rank)

    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(Role, key) and value is not None and value != "":
                query = query.filter(getattr(Role, key) == value)

    return query.offset(skip).limit(limit).all()

def exclude_system_roles(query: Query) -> Query:
    """Exclude roles whose name starts with 'system'."""
    return query.filter(~Role.name.ilike("system%"))
