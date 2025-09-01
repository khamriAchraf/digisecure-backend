from typing import Dict

from pydantic import BaseModel


class ScopeComplianceBreakdown(BaseModel):
    scope_name: str
    document_control_percentage: float
    asset_compliance_percentage: float
    total_compliance_percentage: float


class ScopesComplianceSummary(BaseModel):
    scopes: Dict[int, ScopeComplianceBreakdown]
    overall_progress_percentage: float
