from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import Peripheral, PeripheralCreate, PeripheralUpdate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/peripherals", tags=["assets:peripherals"])


@router.get("/", response_model=PaginatedResponse[Peripheral])
def list_peripherals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all peripherals with optional filtering."""
    try:
        assets, total = service.get_paginated_peripherals(
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


@router.post("/", response_model=Peripheral, status_code=status.HTTP_201_CREATED)
def create_peripheral(
    peripheral_in: PeripheralCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new peripheral."""
    try:
        return service.create_peripheral(peripheral_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{peripheral_id}", response_model=Peripheral)
def get_peripheral(
    peripheral_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific peripheral by ID."""
    try:
        peripheral = service.get_peripheral(peripheral_id)
        if not peripheral:
            raise HTTPException(status_code=404, detail="Peripheral not found")
        return peripheral
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{peripheral_id}", response_model=Peripheral)
def update_peripheral(
    peripheral_id: int,
    peripheral_in: PeripheralUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a peripheral."""
    try:
        peripheral = service.get_peripheral(peripheral_id)
        if not peripheral:
            raise HTTPException(status_code=404, detail="Peripheral not found")
        return service.update_peripheral(peripheral, peripheral_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{peripheral_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_peripheral(
    peripheral_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a peripheral."""
    try:
        peripheral = service.get_peripheral(peripheral_id)
        if not peripheral:
            raise HTTPException(status_code=404, detail="Peripheral not found")
        service.delete_peripheral(peripheral)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
