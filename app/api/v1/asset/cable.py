from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import Cable, CableCreate, CableUpdate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/cables", tags=["assets:cables"])


@router.get("/", response_model=PaginatedResponse[Cable])
def list_cables(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all cables with optional filtering."""
    try:
        assets, total = service.get_paginated_cables(
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


@router.post("/", response_model=Cable, status_code=status.HTTP_201_CREATED)
def create_cable(
    cable_in: CableCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new cable."""
    try:
        return service.create_cable(cable_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{cable_id}", response_model=Cable)
def get_cable(
    cable_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific cable by ID."""
    try:
        cable = service.get_cable(cable_id)
        if not cable:
            raise HTTPException(status_code=404, detail="Cable not found")
        return cable
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{cable_id}", response_model=Cable)
def update_cable(
    cable_id: int,
    cable_in: CableUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a cable."""
    try:
        cable = service.get_cable(cable_id)
        if not cable:
            raise HTTPException(status_code=404, detail="Cable not found")
        return service.update_cable(cable, cable_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{cable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cable(
    cable_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a cable."""
    try:
        cable = service.get_cable(cable_id)
        if not cable:
            raise HTTPException(status_code=404, detail="Cable not found")
        service.delete_cable(cable)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
