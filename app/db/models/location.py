from sqlalchemy import Column, Float, Integer, String, Text

from app.db.base import Base


class Location(Base):
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
