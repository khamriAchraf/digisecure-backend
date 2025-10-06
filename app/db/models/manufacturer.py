from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session

from app.db.base import Base, SoftDeleteMixin
from app.db.models.asset import Asset


class Manufacturer(Base, SoftDeleteMixin):
    __tablename__ = "manufacturers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    comment = Column(String, nullable=True)

    def soft_delete(self, db: Session):
        db.query(Asset).filter(Asset.manufacturer_id == self.id).update(
            {"manufacturer_id": None}
        )
        super().soft_delete()
        return None
