from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import (Software, SoftwareCreate, SoftwareUpdate,
                               SoftwareVersion, SoftwareVersionCreate,
                               SoftwareWithVersions)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/software", tags=["assets:software"])


@router.get("/", response_model=PaginatedResponse[Software])
def list_software(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all software with optional filtering."""
    try:
        software_list, total = service.get_paginated_software(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=software_list, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/", response_model=Software, status_code=status.HTTP_201_CREATED)
def create_software(
    software_in: SoftwareCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new software."""
    try:
        return service.create_software(software_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{software_id}", response_model=Software)
def get_software(
    software_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific software by ID."""
    try:
        software = service.get_software(software_id)
        if not software:
            raise HTTPException(status_code=404, detail="Software not found")
        return software
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{software_id}/with-versions", response_model=SoftwareWithVersions)
def get_software_with_versions(
    software_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific software by ID with all its versions."""
    try:
        software = service.get_software(software_id)
        if not software:
            raise HTTPException(status_code=404, detail="Software not found")
        return software
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{software_id}", response_model=Software)
def update_software(
    software_id: int,
    software_in: SoftwareUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a software."""
    try:
        software = service.get_software(software_id)
        if not software:
            raise HTTPException(status_code=404, detail="Software not found")
        return service.update_software(software_id, software_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{software_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_software(
    software_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a software."""
    try:
        software = service.get_software(software_id)
        if not software:
            raise HTTPException(status_code=404, detail="Software not found")
        service.delete_software(software_id)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Software Version endpoints
@router.post(
    "/versions", response_model=SoftwareVersion, status_code=status.HTTP_201_CREATED
)
def create_software_version(
    version_in: SoftwareVersionCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new software version."""
    try:
        return service.create_software_version(version_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_software_version(
    version_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a software version."""
    try:
        service.delete_software_version(version_id)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
