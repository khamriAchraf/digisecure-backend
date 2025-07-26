from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import SimCardItem, SimCardItemCreate, SimCardItemUpdate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/simcarditems", tags=["assets:sim_card_items"])


@router.get("/", response_model=PaginatedResponse[SimCardItem])
def list_sim_card_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all SIM card items with optional filtering."""
    try:
        assets, total = service.get_paginated_sim_card_items(
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


@router.post("/", response_model=SimCardItem, status_code=status.HTTP_201_CREATED)
def create_sim_card_item(
    sim_card_item_in: SimCardItemCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new SIM card item."""
    try:
        return service.create_sim_card_item(sim_card_item_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{sim_card_item_id}", response_model=SimCardItem)
def get_sim_card_item(
    sim_card_item_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific SIM card item by ID."""
    try:
        sim_card_item = service.get_sim_card_item(sim_card_item_id)
        if not sim_card_item:
            raise HTTPException(status_code=404, detail="SIM card item not found")
        return sim_card_item
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{sim_card_item_id}", response_model=SimCardItem)
def update_sim_card_item(
    sim_card_item_id: int,
    sim_card_item_in: SimCardItemUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a SIM card item."""
    try:
        sim_card_item = service.get_sim_card_item(sim_card_item_id)
        if not sim_card_item:
            raise HTTPException(status_code=404, detail="SIM card item not found")
        return service.update_sim_card_item(sim_card_item, sim_card_item_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{sim_card_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sim_card_item(
    sim_card_item_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a SIM card item."""
    try:
        sim_card_item = service.get_sim_card_item(sim_card_item_id)
        if not sim_card_item:
            raise HTTPException(status_code=404, detail="SIM card item not found")
        service.delete_sim_card_item(sim_card_item)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
