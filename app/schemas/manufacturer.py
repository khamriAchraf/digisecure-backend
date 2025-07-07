from typing import Optional

from pydantic import BaseModel


class ManufacturerBase(BaseModel):
    name: str


class ManufacturerCreate(ManufacturerBase):
    pass


class ManufacturerUpdate(BaseModel):
    name: Optional[str] = None


class ManufacturerInDBBase(ManufacturerBase):
    id: int

    class Config:
        from_attributes = True


class Manufacturer(ManufacturerInDBBase):
    pass


class ManufacturerInDB(ManufacturerInDBBase):
    pass
