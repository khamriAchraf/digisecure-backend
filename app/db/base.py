from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy.orm import declarative_base


class SoftDeleteMixin:
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    restored_at = Column(DateTime, nullable=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

    def restore(self):
        self.is_deleted = False
        self.restored_at = datetime.now(UTC)


Base = declarative_base(cls=SoftDeleteMixin)
