from datetime import datetime

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String,
                        UniqueConstraint)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class TableConfig(Base):
    __tablename__ = "user_table_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    table_key = Column(String(64), nullable=False)  # e.g., 'groups', 'tickets', 'users'
    columns = Column(JSONB, nullable=False)  # Array of column keys to display
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship
    user = relationship("User", back_populates="table_configs")

    # Unique constraint to ensure one config per user per table
    __table_args__ = (
        UniqueConstraint("user_id", "table_key", name="uq_user_table_config"),
    )
