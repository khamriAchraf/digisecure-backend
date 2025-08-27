from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Session, relationship

from app.db.base import Base, SoftDeleteMixin
from app.db.models.user import User

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


class Role(Base, SoftDeleteMixin):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    is_builtin = Column(Boolean, default=False)
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )
    users = relationship("User", back_populates="role")
    rank = Column(Integer, nullable=False)

    def soft_delete(self, db: Session):
        super().soft_delete()
        db.query(role_permissions).filter(
            role_permissions.c.role_id == self.id
        ).delete()
        db.query(User).filter(User.role_id == self.id).update({"role_id": None})
        return None


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    description = Column(String)
    roles = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )
