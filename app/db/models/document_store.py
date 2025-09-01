from datetime import datetime

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Table,
                        UniqueConstraint)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.models.group import document_groups


class DocumentFolder(Base):
    __tablename__ = "document_folders"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(
        Integer, ForeignKey("document_folders.id", ondelete="CASCADE"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    parent = relationship("DocumentFolder", remote_side=[id], back_populates="children")
    children = relationship(
        "DocumentFolder",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    documents = relationship("Document", back_populates="folder")

    __table_args__ = (
        UniqueConstraint("parent_id", "name", name="uq_document_folders_parent_name"),
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    folder_id = Column(
        Integer, ForeignKey("document_folders.id", ondelete="SET NULL"), nullable=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_status = Column(String, nullable=False, default="Draft")
    review_notes = Column(String, nullable=True)
    review_date = Column(DateTime, nullable=True)
    review_frequency_months = Column(Integer, nullable=False, default=12)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="documents")
    folder = relationship("DocumentFolder", back_populates="documents")
    groups = relationship(
        "Group", secondary=document_groups, back_populates="documents"
    )
    versions = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number",
    )
    # Association to compliance controls via link object
    control_links = relationship(
        "ControlDocumentLink",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    # Convenience, read-only list of controls
    controls = relationship(
        "ComplianceControl",
        secondary="control_document_links",
        viewonly=True,
    )
    software = relationship(
        "Software", secondary="software_docs", back_populates="documents"
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True)
    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    version_number = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    checksum = Column(String, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="versions")


software_docs = Table(
    "software_docs",
    Base.metadata,
    Column("document_id", Integer, ForeignKey("documents.id"), primary_key=True),
    Column("software_id", Integer, ForeignKey("software.id"), primary_key=True),
)
