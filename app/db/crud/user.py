from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from app.db.models.role import Role
from app.db.models.user import User, UserStatus
from app.schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> Optional[User]:
    return (
        db.query(User)
        .filter(User.id == user_id, User.status != UserStatus.deleted)
        .first()
    )


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return (
        db.query(User)
        .filter(User.email == email, User.status != UserStatus.deleted)
        .first()
    )


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return (
        db.query(User)
        .filter(User.username == username, User.status != UserStatus.deleted)
        .first()
    )


def get_paginated_users(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[User], int]:
    query: Query = db.query(User).filter(User.status != UserStatus.deleted)

    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(User, key) and value is not None and value != "":
                query = query.filter(getattr(User, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.username.ilike(search_term),
            )
        )

    total = query.count()

    # Apply sorting
    if sort_by and hasattr(User, sort_by):
        column = getattr(User, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    users = query.all()
    return users, total


def create_user(db: Session, user_in: UserCreate, hashed_password: str) -> User:
    roles = []
    if user_in.roles:
        roles = db.query(Role).filter(Role.id.in_(user_in.roles)).all()
    user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        roles=roles,
        language=user_in.language,
        theme=user_in.theme,
        status=user_in.status or UserStatus.active,
        location=user_in.location,
        phone=user_in.phone,
        secondary_phone=user_in.secondary_phone,
        timezone=user_in.timezone,
        valid_from=user_in.valid_from,
        valid_until=user_in.valid_until,
        administartive_number=user_in.administartive_number,
        hashed_password=hashed_password,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        if "unique constraint" in msg:
            if "users_email" in msg:
                raise ValueError(f"User with email '{user_in.email}' already exists.")
            if "users_username" in msg:
                raise ValueError(
                    f"User with username '{user_in.username}' already exists."
                )
            if "users_administartive_number" in msg:
                raise ValueError(
                    f"User with administrative number '{user_in.administartive_number}' already exists."
                )
        raise
    return user


def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    for field, value in user_in.dict(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def soft_delete_user(db: Session, user: User) -> User:
    user.status = UserStatus.deleted  # type: ignore
    db.commit()
    db.refresh(user)
    return user
