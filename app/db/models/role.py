from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.db.base import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        Integer,
        ForeignKey(f"roles.id"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey(f"permissions.id"),
        primary_key=True,
    ),
)


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    is_builtin = Column(Boolean, default=False)
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )
    users = relationship("User", back_populates="role")


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    description = Column(String)
    roles = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )
