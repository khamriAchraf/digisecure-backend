from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db.models.asset import Software, SoftwareVersion
from app.schemas.asset import (SoftwareCreate, SoftwareUpdate,
                               SoftwareVersionCreate)


def get_software(db: Session, software_id: int) -> Optional[Software]:
    """Get a software by ID."""
    return db.query(Software).filter(Software.id == software_id).first()


def get_software_by_name(db: Session, name: str) -> Optional[Software]:
    """Get a software by name."""
    return db.query(Software).filter(Software.name == name).first()


def get_paginated_software(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Software], int]:
    """Get paginated software with optional search and filters."""
    query = db.query(Software)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Software.name.ilike(search_term),
                Software.vendor.ilike(search_term),
                Software.description.ilike(search_term),
            )
        )

    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(Software, key) and value is not None and value != "":
                query = query.filter(getattr(Software, key) == value)

    # Get total count
    total = query.count()

    # Apply sorting
    if sort_by and hasattr(Software, sort_by):
        column = getattr(Software, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    else:
        # Default sorting by name
        query = query.order_by(Software.name.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    return query.all(), total


def create_software(db: Session, software_in: SoftwareCreate) -> Software:
    """Create a new software."""
    # Check if software with same name already exists
    existing_software = get_software_by_name(db, software_in.name)
    if existing_software:
        raise ValueError(f"Software with name '{software_in.name}' already exists")

    software_data = software_in.model_dump()
    software_data["created_at"] = datetime.now(timezone.utc)
    software_data["updated_at"] = datetime.now(timezone.utc)

    software = Software(**software_data)
    db.add(software)
    db.commit()
    db.refresh(software)
    return software


def update_software(
    db: Session, software: Software, software_in: SoftwareUpdate
) -> Software:
    """Update a software."""
    update_data = software_in.model_dump(exclude_unset=True)

    # Check if name is being updated and if it conflicts with existing software
    if "name" in update_data and update_data["name"] != software.name:
        existing_software = get_software_by_name(db, update_data["name"])
        if existing_software:
            raise ValueError(
                f"Software with name '{update_data['name']}' already exists"
            )

    update_data["updated_at"] = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(software, field, value)

    db.commit()
    db.refresh(software)
    return software


def delete_software(db: Session, software: Software) -> None:
    """Delete a software."""
    db.delete(software)
    db.commit()


def get_software_version(db: Session, version_id: int) -> Optional[SoftwareVersion]:
    """Get a software version by ID."""
    return db.query(SoftwareVersion).filter(SoftwareVersion.id == version_id).first()


def get_software_versions_by_software(
    db: Session, software_id: int
) -> List[SoftwareVersion]:
    """Get all versions for a specific software."""
    return (
        db.query(SoftwareVersion)
        .filter(SoftwareVersion.software_id == software_id)
        .all()
    )


def get_software_version_by_version_and_software(
    db: Session, software_id: int, version: str
) -> Optional[SoftwareVersion]:
    """Get a software version by software ID and version string."""
    return (
        db.query(SoftwareVersion)
        .filter(
            and_(
                SoftwareVersion.software_id == software_id,
                SoftwareVersion.version == version,
            )
        )
        .first()
    )


def create_software_version(
    db: Session, version_in: SoftwareVersionCreate
) -> SoftwareVersion:
    """Create a new software version."""
    # Check if software exists
    software = get_software(db, version_in.software_id)
    if not software:
        raise ValueError(f"Software with ID {version_in.software_id} does not exist")

    # Check if version already exists for this software
    existing_version = get_software_version_by_version_and_software(
        db, version_in.software_id, version_in.version
    )
    if existing_version:
        raise ValueError(
            f"Version '{version_in.version}' already exists for software ID {version_in.software_id}"
        )

    version_data = version_in.model_dump()
    version_data["created_at"] = datetime.now(timezone.utc)
    version_data["updated_at"] = datetime.now(timezone.utc)

    version = SoftwareVersion(**version_data)
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def update_software_version(
    db: Session, version: SoftwareVersion, version_in: dict
) -> SoftwareVersion:
    """Update a software version."""
    update_data = version_in.copy()

    # Check if version is being updated and if it conflicts with existing version
    if "version" in update_data and update_data["version"] != version.version:
        existing_version = get_software_version_by_version_and_software(
            db, version.software_id, update_data["version"]
        )
        if existing_version:
            raise ValueError(
                f"Version '{update_data['version']}' already exists for software ID {version.software_id}"
            )

    update_data["updated_at"] = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(version, field, value)

    db.commit()
    db.refresh(version)
    return version


def delete_software_version(db: Session, version: SoftwareVersion) -> None:
    """Delete a software version."""
    db.delete(version)
    db.commit()


def get_software_with_versions(db: Session, software_id: int) -> Optional[Software]:
    """Get a software with all its versions."""
    return db.query(Software).filter(Software.id == software_id).first()
