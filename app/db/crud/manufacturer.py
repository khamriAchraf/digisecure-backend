from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from app.db.models.manufacturer import Manufacturer
from app.schemas.manufacturer import ManufacturerCreate, ManufacturerUpdate


def get_manufacturer(db: Session, manufacturer_id: int) -> Optional[Manufacturer]:
    return db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()


def get_manufacturer_by_name(db: Session, name: str) -> Optional[Manufacturer]:
    return db.query(Manufacturer).filter(Manufacturer.name == name).first()


def list_manufacturers(
    db: Session, skip: int = 0, limit: int = 100
) -> List[Manufacturer]:
    return db.query(Manufacturer).offset(skip).limit(limit).all()


def get_paginated_manufacturers(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Manufacturer], int]:
    query: Query = db.query(Manufacturer)

    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(Manufacturer, key) and value is not None and value != "":
                query = query.filter(getattr(Manufacturer, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Manufacturer.name.ilike(search_term),
                Manufacturer.comment.ilike(search_term),
            )
        )

    total = query.count()

    # Apply sorting
    if sort_by and hasattr(Manufacturer, sort_by):
        column = getattr(Manufacturer, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    return items, total


def create_manufacturer(
    db: Session, manufacturer_in: ManufacturerCreate
) -> Manufacturer:
    manufacturer = Manufacturer(name=manufacturer_in.name)
    db.add(manufacturer)
    try:
        db.commit()
        db.refresh(manufacturer)
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        if "unique constraint" in msg and "manufacturers_name" in msg:
            raise ValueError(
                f"Manufacturer with name '{manufacturer_in.name}' already exists."
            )
        raise
    return manufacturer


def update_manufacturer(
    db: Session, manufacturer: Manufacturer, manufacturer_in: ManufacturerUpdate
) -> Manufacturer:
    for field, value in manufacturer_in.dict(exclude_unset=True).items():
        setattr(manufacturer, field, value)
    db.commit()
    db.refresh(manufacturer)
    return manufacturer


def delete_manufacturer(db: Session, manufacturer: Manufacturer) -> None:
    manufacturer.soft_delete(db)
    db.commit()
