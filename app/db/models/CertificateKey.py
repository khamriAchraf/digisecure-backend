from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base


class CertificateComplianceScope(Base):
    __tablename__ = "certificate_compliance_scopes"

    id = Column(Integer, primary_key=True)
    certificate_key_id = Column(
        Integer, ForeignKey("certificate_keys.id"), nullable=False
    )
    scope_id = Column(Integer, ForeignKey("compliance_scopes.id"), nullable=False)

    certificate_key = relationship("CertificateKey", back_populates="compliance_links")
    scope = relationship("ComplianceScope", back_populates="certificate_links")
