from datetime import date
from typing import Optional

from pydantic import BaseModel


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


class AssetComplianceScopeBase(BaseModel):
    asset_id: int
    scope_id: int
    justification: Optional[str] = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    compliance_notes: Optional[str] = None


class AssetComplianceScopeCreate(AssetComplianceScopeBase):
    pass


class AssetComplianceScopeUpdate(BaseModel):
    justification: Optional[str] = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    compliance_notes: Optional[str] = None


class AssetComplianceScope(BaseModel):
    asset_id: int
    scope_id: int
    justification: Optional[str] = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    compliance_notes: Optional[str] = None

    class Config:
        from_attributes = True


