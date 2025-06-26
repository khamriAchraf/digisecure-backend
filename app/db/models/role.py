from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.db.base import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        Integer,
        ForeignKey(f"{settings.DB_SCHEMA}.roles.id"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey(f"{settings.DB_SCHEMA}.permissions.id"),
        primary_key=True,
    ),
    schema=settings.DB_SCHEMA,
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey(f"{settings.DB_SCHEMA}.users.id"),
        primary_key=True,
    ),
    Column(
        "role_id",
        Integer,
        ForeignKey(f"{settings.DB_SCHEMA}.roles.id"),
        primary_key=True,
    ),
    schema=settings.DB_SCHEMA,
)


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": settings.DB_SCHEMA}
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    is_builtin = Column(Boolean, default=False)
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )
    users = relationship("User", secondary=user_roles, back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {"schema": settings.DB_SCHEMA}
    id = Column(Integer, primary_key=True)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    description = Column(String)
    roles = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )
