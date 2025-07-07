from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate


def get_location(db: Session, location_id: int) -> Optional[Location]:
    return db.query(Location).filter(Location.id == location_id).first()


def get_location_by_name(db: Session, name: str) -> Optional[Location]:
    return db.query(Location).filter(Location.name == name).first()


def list_locations(db: Session, skip: int = 0, limit: int = 100) -> List[Location]:
    return db.query(Location).offset(skip).limit(limit).all()


def create_location(db: Session, location_in: LocationCreate) -> Location:
    location = Location(
        name=location_in.name,
        postal_code=location_in.postal_code,
        building_number=location_in.building_number,
        latitude=location_in.latitude,
        altitude=location_in.altitude,
        comment=location_in.comment,
        address=location_in.address,
        town=location_in.town,
        country=location_in.country,
        state=location_in.state,
        room_number=location_in.room_number,
        longitude=location_in.longitude,
        floor_number=location_in.floor_number,
    )
    db.add(location)
    try:
        db.commit()
        db.refresh(location)
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        if "unique constraint" in msg and "locations_name" in msg:
            raise ValueError(f"Location with name '{location_in.name}' already exists.")
        raise
    return location


def update_location(
    db: Session, location: Location, location_in: LocationUpdate
) -> Location:
    for field, value in location_in.dict(exclude_unset=True).items():
        setattr(location, field, value)
    db.commit()
    db.refresh(location)
    return location


def delete_location(db: Session, location: Location) -> None:
    db.delete(location)
    db.commit()
