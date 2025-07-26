from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import Rack, RackCreate, RackUpdate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/racks", tags=["assets:racks"])


@router.get("/", response_model=PaginatedResponse[Rack])
def list_racks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all racks with optional filtering."""
    try:
        assets, total = service.get_paginated_racks(
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


@router.post("/", response_model=Rack, status_code=status.HTTP_201_CREATED)
def create_rack(
    rack_in: RackCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new rack."""
    try:
        return service.create_rack(rack_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{rack_id}", response_model=Rack)
def get_rack(
    rack_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific rack by ID."""
    try:
        rack = service.get_rack(rack_id)
        if not rack:
            raise HTTPException(status_code=404, detail="Rack not found")
        return rack
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{rack_id}", response_model=Rack)
def update_rack(
    rack_id: int,
    rack_in: RackUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a rack."""
    try:
        rack = service.get_rack(rack_id)
        if not rack:
            raise HTTPException(status_code=404, detail="Rack not found")
        return service.update_rack(rack, rack_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{rack_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rack(
    rack_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a rack."""
    try:
        rack = service.get_rack(rack_id)
        if not rack:
            raise HTTPException(status_code=404, detail="Rack not found")
        service.delete_rack(rack)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
