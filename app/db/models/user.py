import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.models.group import user_groups
from app.db.models.role import user_roles


class UserStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    deleted = "deleted"


class UserRole(enum.Enum):
    super_admin = "Super-Admin"
    admin = "Admin"
    supervisor = "Supervisor"
    technician = "Technician"
    hotliner = "Hotliner"
    observer = "Observer"
    self_service = "Self-Service"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    administartive_number = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    secondary_phone = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    language = Column(String, nullable=True, default="en")
    theme = Column(String, nullable=True, default="light")
    status = Column(Enum(UserStatus), default=UserStatus.active, nullable=False)
    valid_until = Column(DateTime, nullable=True)
    valid_from = Column(DateTime, nullable=True)

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    groups = relationship("Group", secondary=user_groups, back_populates="users")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    table_configs = relationship(
        "TableConfig", back_populates="user", cascade="all, delete-orphan"
    )
