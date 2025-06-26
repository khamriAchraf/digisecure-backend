from sqlalchemy import Column, Integer, String

from app.core.config import settings
from app.db.base import Base


class Org(Base):
    __tablename__ = "orgs"
    __table_args__ = {"schema": settings.DB_SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    admin_email = Column(String, nullable=False)
    subdomain = Column(String, unique=True, nullable=False)
