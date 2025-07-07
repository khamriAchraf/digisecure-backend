from sqlalchemy import Boolean, Column, Integer, String

from app.db.base import Base


class AssetType(Base):
    __tablename__ = "asset_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    is_builtin = Column(Boolean, default=False)
