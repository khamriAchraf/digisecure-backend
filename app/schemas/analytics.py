from typing import Dict, List
from datetime import date

from pydantic import BaseModel


class ScopeComplianceBreakdown(BaseModel):
    scope_name: str
    document_control_percentage: float
    asset_compliance_percentage: float
    total_compliance_percentage: float


class ScopesComplianceSummary(BaseModel):
    scopes: Dict[int, ScopeComplianceBreakdown]
    overall_progress_percentage: float

class UpcomingEvent(BaseModel):
    id: int
    name: str
    scope_name: str
    next_due_date: date
    notify_list: List[str]
    
class UpcomingEventsResponse(BaseModel):
    events: List[UpcomingEvent]
    callback_url: str
