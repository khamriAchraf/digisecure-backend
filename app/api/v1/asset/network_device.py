from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import (NetworkDevice, NetworkDeviceCreate,
                               NetworkDeviceUpdate)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/networkdevices", tags=["assets:network_devices"])


@router.get("/", response_model=PaginatedResponse[NetworkDevice])
def list_network_devices(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all network devices with optional filtering."""
    try:
        assets, total = service.get_paginated_network_devices(
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


@router.post("/", response_model=NetworkDevice, status_code=status.HTTP_201_CREATED)
def create_network_device(
    network_device_in: NetworkDeviceCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new network device."""
    try:
        return service.create_network_device(network_device_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{network_device_id}", response_model=NetworkDevice)
def get_network_device(
    network_device_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific network device by ID."""
    try:
        network_device = service.get_network_device(network_device_id)
        if not network_device:
            raise HTTPException(status_code=404, detail="Network device not found")
        return network_device
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{network_device_id}", response_model=NetworkDevice)
def update_network_device(
    network_device_id: int,
    network_device_in: NetworkDeviceUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a network device."""
    try:
        network_device = service.get_network_device(network_device_id)
        if not network_device:
            raise HTTPException(status_code=404, detail="Network device not found")
        return service.update_network_device(network_device, network_device_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{network_device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_network_device(
    network_device_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a network device."""
    try:
        network_device = service.get_network_device(network_device_id)
        if not network_device:
            raise HTTPException(status_code=404, detail="Network device not found")
        service.delete_network_device(network_device)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
