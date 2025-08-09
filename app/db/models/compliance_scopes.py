from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class ComplianceScope(Base):
    __tablename__ = "compliance_scopes"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)  # e.g., 'PCI-DSS', 'ISO 27001'
    description = Column(Text, nullable=True)
    reference_url = Column(String, nullable=True)

    last_audit_date = Column(Date, nullable=True)
    last_audit_result = Column(String, nullable=True)
    next_audit_due = Column(Date, nullable=True)
    auditor = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    # Reverse relationship
    # Do not cascade deletes here; we want DB FK to block deletion when in use.
    # passive_deletes=True ensures ORM doesn't try to null-out PK FKs on children.
    asset_mappings = relationship(
        "AssetComplianceScope",
        back_populates="scope",
        passive_deletes=True,
    )
    
    @property
    def assets(self):
        """Get all assets associated with this compliance scope."""
        return [mapping.asset for mapping in self.asset_mappings]


class AssetComplianceScope(Base):
    __tablename__ = "asset_compliance_scopes"

    asset_id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    scope_id = Column(Integer, ForeignKey("compliance_scopes.id"), primary_key=True)

    justification = Column(Text, nullable=True)
    last_review_date = Column(Date, nullable=True)
    next_review_date = Column(Date, nullable=True)
    compliance_notes = Column(Text, nullable=True)

    # Relationships
    asset = relationship("Asset", backref="compliance_mappings", passive_deletes=True)
    scope = relationship("ComplianceScope", back_populates="asset_mappings", passive_deletes=True)
