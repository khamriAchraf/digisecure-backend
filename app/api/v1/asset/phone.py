from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import Phone, PhoneCreate, PhoneUpdate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/phones", tags=["assets:phones"])


@router.get("/", response_model=PaginatedResponse[Phone])
def list_phones(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all phones with optional filtering."""
    try:
        assets, total = service.get_paginated_phones(
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


@router.post("/", response_model=Phone, status_code=status.HTTP_201_CREATED)
def create_phone(
    phone_in: PhoneCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new phone."""
    try:
        return service.create_phone(phone_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{phone_id}", response_model=Phone)
def get_phone(
    phone_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific phone by ID."""
    try:
        phone = service.get_phone(phone_id)
        if not phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        return phone
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{phone_id}", response_model=Phone)
def update_phone(
    phone_id: int,
    phone_in: PhoneUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a phone."""
    try:
        phone = service.get_phone(phone_id)
        if not phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        return service.update_phone(phone, phone_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{phone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_phone(
    phone_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a phone."""
    try:
        phone = service.get_phone(phone_id)
        if not phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        service.delete_phone(phone)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
