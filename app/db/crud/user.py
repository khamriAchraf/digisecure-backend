from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from app.db.models.role import Role
from app.db.models.user import User, UserStatus
from app.schemas.user import UserCreate, UserList, UserUpdate


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_paginated_users(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[UserList], int]:
    # Only select the fields required by UserList: id, username, role, status
    # Join Role to return a proper Role instance for Pydantic (instead of a boolean expression)
    query: Query = db.query(
        User.id,
        User.username,
        Role,
        User.status,
    ).outerjoin(Role, User.role_id == Role.id)

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

    # For total, count on the base User query (not the projection)
    total_query = db.query(User.id)
    if filters:
        for key, value in filters.items():
            if hasattr(User, key) and value is not None and value != "":
                total_query = total_query.filter(getattr(User, key) == value)
    if search:
        search_term = f"%{search}%"
        total_query = total_query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.username.ilike(search_term),
            )
        )
    total = total_query.count()

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

    results = query.all()

    # Convert results to UserList Pydantic models
    user_lists = []
    for row in results:
        # row: (id, username, role (Role model or None), status (UserStatus))
        user_dict = {
            "id": row[0],
            "username": row[1],
            "role": row[2],
            "status": row[3].value if hasattr(row[3], "value") else row[3],
        }
        user_lists.append(UserList(**user_dict))

    return user_lists, total


# Deleted users pagination
def get_paginated_deleted_users(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[User], int]:
    """
    Returns a paginated list of soft-deleted users.
    Uses the custom SoftDeleteQuery.only_deleted to include only rows with is_deleted=True.
    """
    query: Query = db.query(User).only_deleted()

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
    else:
        query = query.order_by(User.id.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    users = query.all()
    return users, total


# New cursor-based pagination helper
def get_cursor_users(
    db: Session,
    cursor: Optional[int] = None,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[UserList], int]:
    """Return users for infinite scrolling based on an integer cursor.

    Returns minimal fields aligned with UserList: id, username, role, status.
    """

    # Base query selecting minimal fields and joining role
    base_query: Query = db.query(
        User.id,
        User.username,
        Role,
        User.status,
    ).outerjoin(Role, User.role_id == Role.id)

    # Apply filters (reuse logic from get_paginated_users)
    if filters:
        for key, value in filters.items():
            if hasattr(User, key) and value is not None and value != "":
                base_query = base_query.filter(getattr(User, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        base_query = base_query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.username.ilike(search_term),
            )
        )

    # Apply cursor filtering BEFORE counting total to ensure total reflects remaining items
    if cursor is not None:
        if sort_order.lower() == "desc":
            base_query = base_query.filter(User.id < cursor)
        else:
            base_query = base_query.filter(User.id > cursor)

    # Total after cursor filter
    total = base_query.count()

    # Apply sorting (fallback to id)
    if sort_by and hasattr(User, sort_by):
        column = getattr(User, sort_by)
    else:
        column = User.id

    if sort_order.lower() == "desc":
        base_query = base_query.order_by(column.desc())
    else:
        base_query = base_query.order_by(column.asc())

    # Limit results for infinite scroll
    base_query = base_query.limit(per_page)

    rows = base_query.all()

    users_list: List[UserList] = []
    for row in rows:
        users_list.append(
            UserList(
                id=row[0],
                username=row[1],
                role=row[2],
                status=row[3].value if hasattr(row[3], "value") else row[3],
            )
        )

    return users_list, total


def create_user(db: Session, user_in: UserCreate, hashed_password: str) -> User:
    role = None
    if user_in.role_id:
        role = db.query(Role).filter(Role.id == user_in.role_id).first()
    user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        role=role,
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
    if role.rank < user.role.rank:
        raise ValueError("User role is higher than the role of the current user.")
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
    update_data = user_in.dict(exclude_unset=True)

    if "role_id" in update_data:
        role_id = update_data.pop("role_id")
        if role_id is not None:
            role = db.query(Role).filter(Role.id == role_id).first()
            user.role = role
        else:
            user.role = None

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> User:
    user.soft_delete(db)
    db.commit()


def get_deleted_user(db: Session, user_id: int) -> Optional[User]:
    """
    Return the user only if they are soft-deleted.
    """
    return db.query(User).only_deleted().filter(User.id == user_id).first()


def restore_user(db: Session, user_id: int) -> Optional[User]:
    """
    Restores a soft-deleted user by setting deleted_at to None.
    """
    user = get_deleted_user(db, user_id)
    if user:
        user.restore()
        db.commit()
        db.refresh(user)
        return user
    return None


def purge_user(db: Session, user_id: int) -> Optional[User]:
    """
    Permanently deletes a user by id, only if already soft-deleted.
    """
    user = get_deleted_user(db, user_id)
    if user is None:
        return None
    db.delete(user)
    db.commit()
    return user
