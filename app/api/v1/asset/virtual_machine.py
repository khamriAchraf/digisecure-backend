from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import (VirtualMachine, VirtualMachineCreate,
                               VirtualMachineUpdate)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/virtual_machines", tags=["assets:virtual_machines"])


@router.get("/", response_model=PaginatedResponse[VirtualMachine])
def list_virtual_machines(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all virtual machines with optional filtering."""
    try:
        assets, total = service.get_paginated_virtual_machines(
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


@router.post("/", response_model=VirtualMachine, status_code=status.HTTP_201_CREATED)
def create_virtual_machine(
    virtual_machine_in: VirtualMachineCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new virtual machine."""
    try:
        return service.create_virtual_machine(virtual_machine_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{virtual_machine_id}", response_model=VirtualMachine)
def get_virtual_machine(
    virtual_machine_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific virtual machine by ID."""
    try:
        virtual_machine = service.get_virtual_machine(virtual_machine_id)
        if not virtual_machine:
            raise HTTPException(status_code=404, detail="Virtual machine not found")
        return virtual_machine
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{virtual_machine_id}", response_model=VirtualMachine)
def update_virtual_machine(
    virtual_machine_id: int,
    virtual_machine_in: VirtualMachineUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a virtual machine."""
    try:
        virtual_machine = service.get_virtual_machine(virtual_machine_id)
        if not virtual_machine:
            raise HTTPException(status_code=404, detail="Virtual machine not found")
        return service.update_virtual_machine(virtual_machine, virtual_machine_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{virtual_machine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_virtual_machine(
    virtual_machine_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a virtual machine."""
    try:
        virtual_machine = service.get_virtual_machine(virtual_machine_id)
        if not virtual_machine:
            raise HTTPException(status_code=404, detail="Virtual machine not found")
        service.delete_virtual_machine(virtual_machine)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
