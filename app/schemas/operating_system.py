from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OperatingSystemBase(BaseModel):
    name: str
    vendor: Optional[str] = None
    version: Optional[str] = None
    architecture: Optional[str] = None
    end_of_support_date: Optional[datetime] = None
    end_of_life_date: Optional[datetime] = None
    comment: Optional[str] = None


class OperatingSystemCreate(OperatingSystemBase):
    pass


class OperatingSystemUpdate(BaseModel):
    name: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None
    architecture: Optional[str] = None
    end_of_support_date: Optional[datetime] = None
    end_of_life_date: Optional[datetime] = None
    comment: Optional[str] = None


class OperatingSystemInDBBase(OperatingSystemBase):
    id: int

    class Config:
        from_attributes = True


class OperatingSystem(OperatingSystemInDBBase):
    pass


class OperatingSystemInDB(OperatingSystemInDBBase):
    pass
