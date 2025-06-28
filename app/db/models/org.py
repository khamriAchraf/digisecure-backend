from sqlalchemy import Column, Integer, String

from app.db.base import Base


class Org(Base):
    __tablename__ = "orgs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    admin_email = Column(String, nullable=False)
    subdomain = Column(String, unique=True, nullable=False)
