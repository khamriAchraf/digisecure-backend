from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.orm import Session

from app.db.base import Base, SoftDeleteMixin
from app.db.models.asset import Asset


class Location(Base, SoftDeleteMixin):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    postal_code = Column(String, nullable=True)
    building_number = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    comment = Column(Text, nullable=True)
    address = Column(String, nullable=True)
    town = Column(String, nullable=True)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    room_number = Column(String, nullable=True)
    longitude = Column(Float, nullable=True)
    floor_number = Column(String, nullable=True)

    def soft_delete(self, db: Session):
        db.query(Asset).filter(Asset.location_id == self.id).update(
            {"location_id": None}
        )
        super().soft_delete()
        return None
