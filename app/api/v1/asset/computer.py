from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import (Computer, ComputerCreate, ComputerList,
                               ComputerUpdate)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/computers", tags=["assets:computers"])


@router.get("/", response_model=PaginatedResponse[ComputerList])
def list_computers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all computers with optional filtering."""
    try:
        assets, total = service.get_paginated_computers(
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


@router.post("/", response_model=Computer, status_code=status.HTTP_201_CREATED)
def create_computer(
    computer_in: ComputerCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new computer."""
    try:
        return service.create_computer(computer_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{computer_id}", response_model=Computer)
def get_computer(
    computer_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific computer by ID."""
    try:
        computer = service.get_computer(computer_id)
        if not computer:
            raise HTTPException(status_code=404, detail="Computer not found")
        return computer
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{computer_id}", response_model=Computer)
def update_computer(
    computer_id: int,
    computer_in: ComputerUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a computer."""
    try:
        computer = service.get_computer(computer_id)
        if not computer:
            raise HTTPException(status_code=404, detail="Computer not found")
        return service.update_computer(computer, computer_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{computer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_computer(
    computer_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a computer."""
    try:
        computer = service.get_computer(computer_id)
        if not computer:
            raise HTTPException(status_code=404, detail="Computer not found")
        service.delete_computer(computer)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
