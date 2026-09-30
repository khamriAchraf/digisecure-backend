import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Session, relationship

from app.db.base import Base, SoftDeleteMixin
from app.db.models.asset import Asset
from app.db.models.group import user_groups
from app.db.models.password_reset_token import PasswordResetToken
from app.db.models.refresh_token import RefreshToken
from app.db.models.table_config import TableConfig


class UserStatus(enum.Enum):
    active = "active"
    inactive = "inactive"


class UserRole(enum.Enum):
    super_admin = "Super-Admin"
    admin = "Admin"
    supervisor = "Supervisor"
    technician = "Technician"
    hotliner = "Hotliner"
    observer = "Observer"
    self_service = "Self-Service"


class User(Base, SoftDeleteMixin):
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
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)

    api_keys = relationship("ApiKey", back_populates="owner")
    role = relationship("Role", back_populates="users")
    groups = relationship("Group", secondary=user_groups, back_populates="users")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )
    table_configs = relationship(
        "TableConfig", back_populates="user", cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def soft_delete(self, db: Session):
        super().soft_delete()
        db.query(Asset).filter(Asset.assigned_to == self.id).update(
            {"assigned_to": None}
        )
        db.query(RefreshToken).filter(RefreshToken.user_id == self.id).delete()
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == self.id
        ).delete()
        db.query(TableConfig).filter(TableConfig.user_id == self.id).delete()
        db.query(user_groups).filter(user_groups.c.user_id == self.id).delete()
