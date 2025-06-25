from sqlalchemy import Column, Integer, String

from app.core.config import settings
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": settings.DB_SCHEMA}
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
