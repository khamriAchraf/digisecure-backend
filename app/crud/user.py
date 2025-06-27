from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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


def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return (
        db.query(User)
        .filter(User.status != UserStatus.deleted)
        .offset(skip)
        .limit(limit)
        .all()
    )


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
    except IntegrityError:
        db.rollback()
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


def search_users(
    db: Session,
    org_id: Optional[int] = None,
    profile: Optional[str] = None,
    status: Optional[UserStatus] = None,
    department: Optional[str] = None,
    query: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[User]:
    filters = [User.status != UserStatus.deleted]
    if org_id is not None:
        filters.append(User.org_id == org_id)
    if profile is not None:
        filters.append(User.profile == profile)
    if status is not None:
        filters.append(User.status == status)
    if department is not None and hasattr(User, "department"):
        filters.append(User.department == department)
    if query:
        search = f"%{query}%"
        filters.append(
            or_(
                User.full_name.ilike(search),
                User.email.ilike(search),
                User.username.ilike(search),
            )
        )
    return db.query(User).filter(and_(*filters)).offset(skip).limit(limit).all()
