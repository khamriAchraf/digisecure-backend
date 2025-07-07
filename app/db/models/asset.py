from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    asset_type = Column(Integer, ForeignKey("asset_types.id"), nullable=False)
    serial_number = Column(String, nullable=True)
    inventory_number = Column(String, nullable=True)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=True)
    status = Column(String, nullable=False)
    purchase_date = Column(Date, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    asset_type_rel = relationship("AssetType")
    manufacturer = relationship("Manufacturer")
    location = relationship("Location")
    group = relationship("Group")
    assigned_user = relationship("User")
