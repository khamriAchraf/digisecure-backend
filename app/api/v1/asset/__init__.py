from fastapi import APIRouter, HTTPException

from app.api.v1.asset.certificate_key import router as certificate_key_router
# from app.api.v1.asset.analytics import router as analytics_router
# from app.api.v1.asset.bulk import router as bulk_router
from app.api.v1.asset.computer import router as computer_router
from app.api.v1.asset.network_device import router as network_device_router
from app.api.v1.asset.software import router as software_router
from app.api.v1.asset.utils import get_query_filters
from app.api.v1.asset.virtual_machine import router as virtual_machine_router
from app.schemas.asset import AssetList
from app.schemas.pagination import PaginatedResponse, create_paginated_response

router = APIRouter(prefix="/assets", tags=["assets"])
router.include_router(computer_router)
router.include_router(network_device_router)
router.include_router(software_router)
router.include_router(virtual_machine_router)
router.include_router(certificate_key_router)
# router.include_router(analytics_router)
# router.include_router(bulk_router)


from typing import List, Optional

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_asset_service, get_current_user, get_db
from app.db.models.user import User
from app.schemas.compliance_scope import (AssetComplianceScope,
                                          AssetComplianceScopeCreate,
                                          AssetComplianceScopeUpdate)
from app.services.asset_service import AssetService, PermissionError
from app.services.compliance_scope_service import ComplianceScopeService


@router.get(
    "/",
    summary="List all assets (all types)",
    response_model=PaginatedResponse[AssetList],
)
def list_all_assets(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    manufacturer_id: Optional[int] = Query(
        None, description="Filter by manufacturer ID"
    ),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """
    Fetch all assets regardless of type, with pagination, sorting, and search.

    Supports filtering by:
    - location_id: Filter assets by their location
    - manufacturer_id: Filter assets by their manufacturer
    - warranty_expired: Filter by warranty status (true/false)
    - Any other asset attribute can be used as a query parameter for filtering
    """
    try:
        assets, total = service.get_paginated_assets(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


def get_compliance_service(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ComplianceScopeService:
    return ComplianceScopeService(db, current_user)


@router.post("/{asset_id}/scopes/{scope_id}", response_model=AssetComplianceScope)
def tag_scope_to_asset(
    asset_id: int,
    scope_id: int,
    mapping_in: AssetComplianceScopeUpdate = None,
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        payload = mapping_in.dict() if mapping_in else {}
        base = AssetComplianceScopeCreate(
            asset_id=asset_id, scope_id=scope_id, **payload
        )
        return service.tag_asset_with_scope(base)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{asset_id}/scopes/{scope_id}", status_code=204)
def untag_scope_from_asset(
    asset_id: int,
    scope_id: int,
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        service.untag_asset_scope(asset_id, scope_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{asset_id}/scopes", status_code=204)
def replace_asset_scopes_endpoint(
    asset_id: int,
    scope_ids: List[int],
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        service.replace_asset_scopes(asset_id, scope_ids)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
