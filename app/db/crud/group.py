from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.group import Group
from app.db.models.user import User
from app.schemas.group import GroupCreate, GroupUpdate


def get_group(db: Session, group_id: int) -> Optional[Group]:
    return db.query(Group).filter(Group.id == group_id).first()


def get_group_by_name(db: Session, name: str) -> Optional[Group]:
    return db.query(Group).filter(Group.name == name).first()


def list_groups(db: Session, skip: int = 0, limit: int = 100) -> List[Group]:
    return db.query(Group).offset(skip).limit(limit).all()


def create_group(db: Session, group_in: GroupCreate) -> Group:
    group = Group(
        name=group_in.name,
        description=group_in.description,
        type=group_in.type,
        contain_users=group_in.contain_users,
        contain_items=group_in.contain_items,
        comment=group_in.comment,
        parent_id=group_in.parent_id,
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
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, group: Group) -> None:
    db.delete(group)
    db.commit()


def add_user_to_group(db: Session, group: Group, user: User) -> Group:
    if user not in group.users:
        group.users.append(user)
        db.commit()
        db.refresh(group)
    return group


def remove_user_from_group(db: Session, group: Group, user: User) -> Group:
    if user in group.users:
        group.users.remove(user)
        db.commit()
        db.refresh(group)
    return group
