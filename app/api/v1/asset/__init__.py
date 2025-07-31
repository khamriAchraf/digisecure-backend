from fastapi import APIRouter, HTTPException

from app.api.v1.asset.analytics import router as analytics_router
from app.api.v1.asset.bulk import router as bulk_router
from app.api.v1.asset.cable import router as cable_router
from app.api.v1.asset.computer import router as computer_router
from app.api.v1.asset.consumable import router as consumable_router
from app.api.v1.asset.network_device import router as network_device_router
from app.api.v1.asset.peripheral import router as peripheral_router
from app.api.v1.asset.phone import router as phone_router
from app.api.v1.asset.printer import router as printer_router
from app.api.v1.asset.rack import router as rack_router
from app.api.v1.asset.sim_card_item import router as sim_card_item_router
from app.api.v1.asset.software import router as software_router
from app.api.v1.asset.utils import get_query_filters
from app.api.v1.asset.virtual_machine import router as virtual_machine_router
from app.schemas.asset import Asset
from app.schemas.pagination import PaginatedResponse, create_paginated_response

router = APIRouter(prefix="/assets", tags=["assets"])
router.include_router(computer_router)
# router.include_router(printer_router)
router.include_router(network_device_router)
# router.include_router(phone_router)
# router.include_router(peripheral_router)
# router.include_router(consumable_router)
# router.include_router(rack_router)
# router.include_router(cable_router)
# router.include_router(sim_card_item_router)
router.include_router(software_router)
router.include_router(virtual_machine_router)
# router.include_router(analytics_router)
# router.include_router(bulk_router)


from typing import Optional

from fastapi import Depends, Query

from app.api.dependencies import get_asset_service
from app.services.asset_service import AssetService, PermissionError


@router.get(
    "/",
    summary="List all assets (all types)",
    response_model=PaginatedResponse[Asset],
)
def list_all_assets(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """
    Fetch all assets regardless of type, with pagination, sorting, and search.
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
