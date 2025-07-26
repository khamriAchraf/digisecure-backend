from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import Consumable, ConsumableCreate, ConsumableUpdate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/consumables", tags=["assets:consumables"])


@router.get("/", response_model=PaginatedResponse[Consumable])
def list_consumables(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all consumables with optional filtering."""
    try:
        assets, total = service.get_paginated_consumables(
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


@router.post("/", response_model=Consumable, status_code=status.HTTP_201_CREATED)
def create_consumable(
    consumable_in: ConsumableCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new consumable."""
    try:
        return service.create_consumable(consumable_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{consumable_id}", response_model=Consumable)
def get_consumable(
    consumable_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific consumable by ID."""
    try:
        consumable = service.get_consumable(consumable_id)
        if not consumable:
            raise HTTPException(status_code=404, detail="Consumable not found")
        return consumable
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{consumable_id}", response_model=Consumable)
def update_consumable(
    consumable_id: int,
    consumable_in: ConsumableUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a consumable."""
    try:
        consumable = service.get_consumable(consumable_id)
        if not consumable:
            raise HTTPException(status_code=404, detail="Consumable not found")
        return service.update_consumable(consumable, consumable_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{consumable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_consumable(
    consumable_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a consumable."""
    try:
        consumable = service.get_consumable(consumable_id)
        if not consumable:
            raise HTTPException(status_code=404, detail="Consumable not found")
        service.delete_consumable(consumable)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
