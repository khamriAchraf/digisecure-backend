from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.role import Permission, Role


def get_role(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == name).first()


def list_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
    return db.query(Role).offset(skip).limit(limit).all()


def create_role(
    db: Session, name: str, description: Optional[str] = None, is_builtin: bool = False
) -> Role:
    role = Role(name=name, description=description, is_builtin=is_builtin)
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
    db.delete(role)
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
