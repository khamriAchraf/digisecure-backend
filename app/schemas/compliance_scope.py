from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.document_store import Document


class AssetRef(BaseModel):
    id: int
    name: str
    type: str
    compliant: Optional[bool] = None

    class Config:
        from_attributes = True


class ComplianceScopeBase(BaseModel):
    name: str
    description: Optional[str] = None
    reference_url: Optional[str] = None
    last_audit_date: Optional[date] = None
    last_audit_result: Optional[str] = None
    next_audit_due: Optional[date] = None
    auditor: Optional[str] = None
    notes: Optional[str] = None


class ComplianceScopeCreate(ComplianceScopeBase):
    pass


class ComplianceScopeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    reference_url: Optional[str] = None
    last_audit_date: Optional[date] = None
    last_audit_result: Optional[str] = None
    next_audit_due: Optional[date] = None
    auditor: Optional[str] = None
    notes: Optional[str] = None


class ComplianceScope(ComplianceScopeBase):
    id: int

    class Config:
        from_attributes = True


# ----------------------------------------
# Schema to represent a compliance scope **for a specific asset**.
# Combines the core ComplianceScope fields with the asset-specific
# mapping attributes coming from `AssetComplianceScope`.
# ----------------------------------------


class ComplianceScopeForAsset(ComplianceScopeBase):
    """ComplianceScope tailored for inclusion inside an Asset response (no `assets` list)."""

    id: int
    compliant: Optional[bool] = None
    justification: Optional[str] = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    compliance_notes: Optional[str] = None

    class Config:
        from_attributes = True


class AssetComplianceScopeBase(BaseModel):
    asset_id: int
    scope_id: int
    compliant: Optional[bool] = None
    justification: Optional[str] = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    compliance_notes: Optional[str] = None


class AssetComplianceScopeCreate(AssetComplianceScopeBase):
    pass


class AssetComplianceScopeUpdate(BaseModel):
    compliant: Optional[bool] = None
    justification: Optional[str] = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    compliance_notes: Optional[str] = None


class AssetComplianceScope(BaseModel):
    asset_id: int
    scope_id: int
    compliant: Optional[bool] = None
    justification: Optional[str] = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    compliance_notes: Optional[str] = None

    class Config:
        from_attributes = True


# ----------------------------------------
# Combined view for assets within a scope
# ----------------------------------------


class ScopedAsset(BaseModel):
    """Representation of an asset listed under a compliance scope.

    Includes minimal asset identifiers and type, plus all mapping fields
    coming from `AssetComplianceScope`.
    """

    id: int
    name: str
    type: str
    compliant: Optional[bool] = None
    justification: Optional[str] = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    compliance_notes: Optional[str] = None

    class Config:
        from_attributes = True


# ----------------------------------------
# Compliance controls
# ----------------------------------------


class ComplianceControl(BaseModel):
    id: int
    scope_id: int
    code: str
    title: str
    description: str | None = None
    required_document_name: str | None = None
    required_document_description: str | None = None
    required_document_type: str | None = None
    last_audit_date: datetime | None = None
    last_audit_result: str | None = None
    # moved metadata to control
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: Optional[str] = None
    compliance_notes: Optional[str] = None
    documents: List[Document] = []

    class Config:
        from_attributes = True


# A lightweight view for listing controls with document_count instead of documents
class ComplianceControlListItem(BaseModel):
    id: int
    scope_id: int
    code: str
    title: str
    description: str | None = None
    required_document_name: str | None = None
    required_document_description: str | None = None
    required_document_type: str | None = None
    last_audit_date: datetime | None = None
    last_audit_result: str | None = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: Optional[str] = None
    compliance_notes: Optional[str] = None
    document_count: int

    class Config:
        from_attributes = True


# ----------------------------------------
# Control-Document link payloads
# ----------------------------------------


class ControlDocumentLinkCreate(BaseModel):
    document_ids: List[int]


class ControlDocumentLinkDelete(BaseModel):
    document_ids: List[int]


class ControlDocumentLink(BaseModel):
    control_id: int
    document_id: int
