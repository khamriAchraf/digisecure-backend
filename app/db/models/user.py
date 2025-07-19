import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.models.group import user_groups


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
    role_id = Column(Integer, ForeignKey("roles.id"))

    role = relationship("Role", back_populates="users")
    groups = relationship("Group", secondary=user_groups, back_populates="users")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    table_configs = relationship(
        "TableConfig", back_populates="user", cascade="all, delete-orphan"
    )

    class Config:
        schema_extra = {
            "examples": [
                {
                    "email": "user@example.com",
                    "username": "john_doe",
                    "full_name": "John Doe",
                    "role": "user",
                    "groups": ["group1", "group2"],
                    "status": "active",
                    "valid_until": "2025-01-01T00:00:00Z",
                    "valid_from": "2024-01-01T00:00:00Z",
                    "administartive_number": "1234567890",
                    "phone": "+1234567890",
                    "secondary_phone": "+1234567890",
                    "timezone": "UTC",
                    "location": "New York",
                    "language": "en",
                    "theme": "light",
                }
            ]
        }

    def __repr__(self):
        return f"<User {self.username}>"
