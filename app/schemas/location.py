from typing import Optional

from pydantic import BaseModel


class LocationBase(BaseModel):
    name: str
    postal_code: Optional[str] = None
    building_number: Optional[str] = None
    latitude: Optional[float] = None
    altitude: Optional[float] = None
    comment: Optional[str] = None
    address: Optional[str] = None
    town: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    room_number: Optional[str] = None
    longitude: Optional[float] = None
    floor_number: Optional[str] = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    postal_code: Optional[str] = None
    building_number: Optional[str] = None
    latitude: Optional[float] = None
    altitude: Optional[float] = None
    comment: Optional[str] = None
    address: Optional[str] = None
    town: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    room_number: Optional[str] = None
    longitude: Optional[float] = None
    floor_number: Optional[str] = None


class LocationInDBBase(LocationBase):
    id: int

    class Config:
        from_attributes = True


class Location(LocationInDBBase):
    pass


class LocationInDB(LocationInDBBase):
    pass
