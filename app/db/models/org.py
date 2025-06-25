from sqlalchemy import Column, Integer, String

from app.db.base import Base


class Org(Base):
    __tablename__ = "orgs"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    schema_name = Column(String, unique=True, nullable=False)
    db_user = Column(String, unique=True, nullable=False)
    db_password = Column(String, nullable=False)
    admin_email = Column(String, nullable=False)
    subdomain = Column(String, unique=True, nullable=False)
