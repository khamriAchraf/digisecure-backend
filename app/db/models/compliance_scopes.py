from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import Session, relationship

from app.db.base import Base, SoftDeleteMixin


class ControlDocumentLink(Base):
    __tablename__ = "control_document_links"
    control_id = Column(
        Integer,
        ForeignKey("compliance_controls.id", ondelete="CASCADE"),
        primary_key=True,
    )
    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )

    control = relationship("ComplianceControl", back_populates="document_links")
    document = relationship("Document", back_populates="control_links")


class ComplianceScope(Base, SoftDeleteMixin):
    __tablename__ = "compliance_scopes"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    reference_url = Column(String, nullable=True)

    last_audit_date = Column(Date, nullable=True)
    last_audit_result = Column(String, nullable=True)
    next_audit_due = Column(Date, nullable=True)
    auditor = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    asset_mappings = relationship(
        "AssetComplianceScope",
        back_populates="scope",
        passive_deletes=True,
    )
    controls = relationship(
        "ComplianceControl",
        back_populates="scope",
        passive_deletes=True,
    )

    @property
    def assets(self):
        """Get all assets associated with this compliance scope.

        Ensures each returned asset carries mapping-specific attributes
        (e.g. `compliant`) so downstream schemas like `AssetRef` can
        serialize them via Pydantic's `from_attributes`.
        """
        assets_with_mapping_fields = []
        for mapping in self.asset_mappings:
            asset_obj = mapping.asset
            # Attach mapping-specific attributes on the asset instance
            # so that `AssetRef.compliant` is populated during serialization.
            asset_obj.compliant = mapping.compliant
            assets_with_mapping_fields.append(asset_obj)

        return assets_with_mapping_fields

    def soft_delete(self, db: Session):
        super().soft_delete()
        db.query(AssetComplianceScope).filter(
            AssetComplianceScope.scope_id == self.id
        ).delete()
        return None


class AssetComplianceScope(Base):
    __tablename__ = "asset_compliance_scopes"

    asset_id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    scope_id = Column(Integer, ForeignKey("compliance_scopes.id"), primary_key=True)
    compliant = Column(Boolean, nullable=False, default=False)

    justification = Column(Text, nullable=True)
    last_review_date = Column(Date, nullable=True)
    next_review_date = Column(Date, nullable=True)
    compliance_notes = Column(Text, nullable=True)

    # Relationships
    asset = relationship("Asset", backref="compliance_mappings", passive_deletes=True)
    scope = relationship(
        "ComplianceScope", back_populates="asset_mappings", passive_deletes=True
    )


class ComplianceControl(Base):
    __tablename__ = "compliance_controls"

    id = Column(Integer, primary_key=True)
    scope_id = Column(Integer, ForeignKey("compliance_scopes.id", ondelete="CASCADE"))
    code = Column(String, nullable=False)  # e.g., '1.1', 'A.5.1'
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # NEW: helps guide the company on what to upload
    required_document_name = Column(String, nullable=True)
    required_document_description = Column(Text, nullable=True)
    required_document_type = Column(
        String, nullable=True
    )  # e.g., 'policy', 'procedure', 'diagram'

    last_audit_date = Column(DateTime, nullable=True)
    last_audit_result = Column(String, nullable=True)  # 'PASS', 'FAIL', 'NEEDS_REVIEW'

    # Moved from association: metadata now managed per control
    last_review_date = Column(Date, nullable=True)
    review_frequency_months = Column(Integer, nullable=False, default=12)
    next_review_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    status = Column(String, nullable=True)
    compliance_notes = Column(Text, nullable=True)

    scope = relationship("ComplianceScope", back_populates="controls")
    # Association object links with metadata
    document_links = relationship(
        "ControlDocumentLink",
        back_populates="control",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    # Convenience, read-only list of documents via the link table
    documents = relationship(
        "Document",
        secondary="control_document_links",
        viewonly=True,
    )
