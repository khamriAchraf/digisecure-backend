from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Table)
from sqlalchemy.orm import Session, relationship

from app.db.base import Base, SoftDeleteMixin

user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id"), primary_key=True),
)

asset_groups = Table(
    "asset_groups",
    Base.metadata,
    Column("asset_id", Integer, ForeignKey("assets.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id"), primary_key=True),
)

document_groups = Table(
    "document_groups",
    Base.metadata,
    Column("document_id", Integer, ForeignKey("documents.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id"), primary_key=True),
)


class Group(Base, SoftDeleteMixin):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    type = Column(String, nullable=True)  # e.g., 'skill', 'org', 'notification'
    contain_users = Column(Boolean, default=True)
    contain_items = Column(Boolean, default=True)
    comment = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relationships
    users = relationship("User", secondary=user_groups, back_populates="groups")
    assets = relationship("Asset", secondary=asset_groups, back_populates="groups")
    parent = relationship("Group", remote_side=[id], backref="children")
    documents = relationship(
        "Document", secondary=document_groups, back_populates="groups"
    )

    def soft_delete(self, db: Session):
        super().soft_delete()
        db.query(user_groups).filter(user_groups.c.group_id == self.id).delete()
        db.query(asset_groups).filter(asset_groups.c.group_id == self.id).delete()
        db.query(Group).filter(Group.parent_id == self.id).update({"parent_id": None})
        db.commit()
        return None
