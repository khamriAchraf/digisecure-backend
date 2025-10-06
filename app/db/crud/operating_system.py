from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from app.db.models.operating_system import OperatingSystem
from app.schemas.operating_system import (OperatingSystemCreate,
                                          OperatingSystemUpdate)


def get_operating_system(
    db: Session, operating_system_id: int
) -> Optional[OperatingSystem]:
    return (
        db.query(OperatingSystem)
        .filter(OperatingSystem.id == operating_system_id)
        .first()
    )


def get_operating_system_by_name(db: Session, name: str) -> Optional[OperatingSystem]:
    return db.query(OperatingSystem).filter(OperatingSystem.name == name).first()


def list_operating_systems(
    db: Session, skip: int = 0, limit: int = 100
) -> List[OperatingSystem]:
    return db.query(OperatingSystem).offset(skip).limit(limit).all()


def get_paginated_operating_systems(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[OperatingSystem], int]:
    query: Query = db.query(OperatingSystem)

    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(OperatingSystem, key) and value is not None and value != "":
                query = query.filter(getattr(OperatingSystem, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                OperatingSystem.name.ilike(search_term),
                OperatingSystem.comment.ilike(search_term),
            )
        )

    total = query.count()

    # Apply sorting
    if sort_by and hasattr(OperatingSystem, sort_by):
        column = getattr(OperatingSystem, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    return items, total


def create_operating_system(
    db: Session, operating_system_in: OperatingSystemCreate
) -> OperatingSystem:
    operating_system = OperatingSystem(
        name=operating_system_in.name,
        vendor=operating_system_in.vendor,
        version=operating_system_in.version,
        architecture=operating_system_in.architecture,
        end_of_support_date=operating_system_in.end_of_support_date,
        end_of_life_date=operating_system_in.end_of_life_date,
        comment=operating_system_in.comment,
    )
    db.add(operating_system)
    try:
        db.commit()
        db.refresh(operating_system)
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        # Handle unique constraint violations for (name, version)
        if ("unique constraint" in msg or "unique violation" in msg) and (
            "uq_operating_systems_name_version" in msg
            or "operating_systems_name_version_key" in msg
            or "operating_systems_name_version_uniq" in msg
        ):
            raise ValueError(
                f"OperatingSystem with name '{operating_system_in.name}' and version '{operating_system_in.version}' already exists."
            )
        raise
    return operating_system


def update_operating_system(
    db: Session,
    operating_system: OperatingSystem,
    operating_system_in: OperatingSystemUpdate,
) -> OperatingSystem:
    update_data = operating_system_in.dict(exclude_unset=True)

    for field, value in operating_system_in.dict(exclude_unset=True).items():
        setattr(operating_system, field, value)
    operating_system.updated_at = datetime.now(timezone.utc)

    # Check if name and version combination is being updated and if it conflicts with existing operating system
    if (
        "name" in update_data
        and "version" in update_data
        and update_data["name"] != operating_system.name
        and update_data["version"] != operating_system.version
    ):
        existing_operating_system = get_operating_system_by_name_and_version(
            db, update_data["name"], update_data["version"]
        )
        if existing_operating_system:
            raise ValueError(
                f"OperatingSystem with name '{update_data['name']}' and version '{update_data['version']}' already exists"
            )

    db.commit()
    db.refresh(operating_system)
    return operating_system


def delete_operating_system(db: Session, operating_system: OperatingSystem) -> None:
    db.delete(operating_system)
    db.commit()


def get_operating_system_by_name_and_version(
    db: Session, name: str, version: str
) -> Optional[OperatingSystem]:
    return (
        db.query(OperatingSystem)
        .filter(OperatingSystem.name == name, OperatingSystem.version == version)
        .first()
    )
