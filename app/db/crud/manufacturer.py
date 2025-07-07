from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
    db.delete(manufacturer)
    db.commit()
