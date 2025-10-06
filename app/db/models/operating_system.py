from sqlalchemy import Column, Date, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Session

from app.db.base import Base, SoftDeleteMixin
from app.schemas.asset import Computer, VirtualMachine


class OperatingSystem(Base, SoftDeleteMixin):
    __tablename__ = "operating_systems"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_operating_systems_name_version"),
    )
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    vendor = Column(String, nullable=True)
    version = Column(String, nullable=True)
    architecture = Column(String, nullable=True)
    end_of_support_date = Column(Date, nullable=True)
    end_of_life_date = Column(Date, nullable=True)
    comment = Column(Text, nullable=True)

    def soft_delete(self, db: Session):
        db.query(VirtualMachine).filter(
            VirtualMachine.operating_system_id == self.id
        ).update({"operating_system_id": None})
        db.query(Computer).filter(Computer.operating_system_id == self.id).update(
            {"operating_system_id": None}
        )
        super().soft_delete()

        return None
