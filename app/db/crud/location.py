from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from app.db.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate


def get_location(db: Session, location_id: int) -> Optional[Location]:
    return db.query(Location).filter(Location.id == location_id).first()


def get_location_by_name(db: Session, name: str) -> Optional[Location]:
    return db.query(Location).filter(Location.name == name).first()


def list_locations(db: Session, skip: int = 0, limit: int = 100) -> List[Location]:
    return db.query(Location).offset(skip).limit(limit).all()


def get_paginated_locations(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Location], int]:
    query: Query = db.query(Location)

    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(Location, key) and value is not None and value != "":
                query = query.filter(getattr(Location, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Location.name.ilike(search_term),
                Location.address.ilike(search_term),
                Location.town.ilike(search_term),
                Location.country.ilike(search_term),
                Location.state.ilike(search_term),
                Location.postal_code.ilike(search_term),
            )
        )

    total = query.count()

    # Apply sorting
    if sort_by and hasattr(Location, sort_by):
        column = getattr(Location, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    return items, total


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
    location.soft_delete(db)
    db.commit()
