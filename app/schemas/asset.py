from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class AssetBase(BaseModel):
    name: str
    asset_type: int
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: str
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_id: Optional[int] = None
    assigned_to: Optional[int] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[int] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_id: Optional[int] = None
    assigned_to: Optional[int] = None


class AssetInDBBase(AssetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Asset(AssetInDBBase):
    pass


class AssetInDB(AssetInDBBase):
    pass
