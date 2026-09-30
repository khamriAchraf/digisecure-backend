from sqlalchemy.orm import Session

from app.core.security import has_permission
from app.db.models.compliance_scopes import ComplianceScope
from app.db.models.user import User
from app.services.compliance_scope_service import ComplianceScopeService
from app.services.compliance_event_service import ComplianceEventService
from app.schemas.analytics import UpcomingEvent
from app.db.crud import compliance_event as compliance_event_crud
from app.core.config import settings



class PermissionError(Exception):
    pass


class AnalyticsService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def _ensure_permission(self):
        if not has_permission(self.current_user, "list", "analytics"):
            raise PermissionError("Not allowed to list analytics.")

    def get_active_compliance_scopes_count(self) -> int:
        self._ensure_permission()
        return self.db.query(ComplianceScope).count()

    def get_scope_document_progress_percentages(self) -> dict[int, float]:
        self._ensure_permission()
        return get_scope_document_progress_percentages(self.db, self.current_user)

    def get_scope_asset_compliance_percentages(self) -> dict[int, float]:
        self._ensure_permission()
        return get_scope_asset_compliance_percentages(self.db, self.current_user)

    def get_scopes_compliance_summary(self) -> dict:
        self._ensure_permission()
        return get_scopes_compliance_summary(self.db, self.current_user)
    
    def get_events_needing_reminder(self) -> list[UpcomingEvent] | None: 
        events=compliance_event_crud.get_events_needing_reminder(self.db)
        return events, settings.EVENT_NOTIFICATION_CALLBACK_URL


def get_active_compliance_scopes_count(db: Session) -> int:
    """Return the number of active (non-deleted) compliance scopes."""
    return db.query(ComplianceScope).count()


def get_scope_document_progress_percentages(
    db: Session, current_user: User
) -> dict[int, float]:
    """Return document requirement satisfaction percentage for each active scope.

    For each scope, progress is the percentage of controls that have at least
    one linked document.
    """
    service = ComplianceScopeService(db, current_user)
    scopes = service.list_scopes(skip=0, limit=10000)

    progress_by_scope: dict[int, float] = {}

    for scope in scopes:
        controls = service.list_scope_controls(scope.id)
        total_controls = len(controls)
        if total_controls == 0:
            progress_by_scope[scope.id] = 0.0
            continue

        satisfied = sum(1 for c in controls if getattr(c, "document_count", 0) > 0)
        progress = (satisfied / total_controls) * 100.0

        progress_by_scope[scope.id] = round(progress, 2)

    return progress_by_scope


def get_scope_asset_compliance_percentages(
    db: Session, current_user: User
) -> dict[int, float]:
    """Return asset compliance percentage for each active scope.

    For each scope, percentage is the share of attached assets whose mapping
    has compliant == True out of all attached assets.
    """
    service = ComplianceScopeService(db, current_user)
    scopes = service.list_scopes(skip=0, limit=10000)

    percentages_by_scope: dict[int, float] = {}
    for scope in scopes:
        total_attached = len(scope.asset_mappings or [])
        if total_attached == 0:
            percentages_by_scope[scope.id] = 0.0
            continue

        compliant_count = sum(
            1 for m in scope.asset_mappings if bool(getattr(m, "compliant", False))
        )
        percentage = (compliant_count / total_attached) * 100.0
        percentages_by_scope[scope.id] = round(percentage, 2)

    return percentages_by_scope


def get_scopes_compliance_summary(db: Session, current_user: User) -> dict:
    """Combine document control and asset compliance percentages per scope.

    Returns a dict with:
    - scopes: { scope_id: { document_control_percentage, asset_compliance_percentage, total_compliance_percentage } }
    - overall_progress_percentage: average of total_compliance across active scopes
    """
    doc_pct_by_scope = get_scope_document_progress_percentages(db, current_user)
    asset_pct_by_scope = get_scope_asset_compliance_percentages(db, current_user)

    scope_ids = set(doc_pct_by_scope.keys()) | set(asset_pct_by_scope.keys())

    scopes_summary: dict[int, dict[str, float | str]] = {}
    # Build id->name map once
    scope_service = ComplianceScopeService(db, current_user)
    scopes = scope_service.list_scopes(skip=0, limit=10000)
    scope_id_to_name = {s.id: s.name for s in scopes}
    totals: list[float] = []

    for scope_id in scope_ids:
        doc_pct = float(doc_pct_by_scope.get(scope_id, 0.0))
        asset_pct = float(asset_pct_by_scope.get(scope_id, 0.0))
        total_pct = round((doc_pct + asset_pct) / 2.0, 2)

        scopes_summary[scope_id] = {
            "scope_name": scope_id_to_name.get(scope_id, str(scope_id)),
            "document_control_percentage": doc_pct,
            "asset_compliance_percentage": asset_pct,
            "total_compliance_percentage": total_pct,
        }
        totals.append(total_pct)

    overall_progress = round(sum(totals) / len(totals), 2) if totals else 0.0

    return {
        "scopes": scopes_summary,
        "overall_progress_percentage": overall_progress,
    }

