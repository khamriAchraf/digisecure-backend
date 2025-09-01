from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.analytics import ScopesComplianceSummary
from app.services.analytics_service import AnalyticsService, PermissionError

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/scopes/compliance", response_model=ScopesComplianceSummary)
def get_scopes_compliance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalyticsService(db, current_user)
    try:
        return service.get_scopes_compliance_summary()
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
