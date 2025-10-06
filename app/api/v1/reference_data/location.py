from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import get_reference_data_service
from app.schemas.location import Location, LocationCreate, LocationUpdate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.reference_data_service import (PermissionError,
                                                 ReferenceDataService)

router = APIRouter(prefix="/locations", tags=["reference_data:locations"])


def get_query_filters(request: Request) -> dict:
    filters = {}
    for key, value in request.query_params.items():
        if key not in ["page", "per_page", "sort_by", "sort_order", "search"]:
            filters[key] = value
    return filters


@router.get("/", response_model=PaginatedResponse[Location])
def list_locations(
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: ReferenceDataService = Depends(get_reference_data_service),
    filters: dict = Depends(get_query_filters),
):
    try:
        items, total = service.get_paginated_locations(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=items, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/", response_model=Location, status_code=status.HTTP_201_CREATED)
def create_location(
    location_in: LocationCreate,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        return service.create_location(location_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{location_id}", response_model=Location)
def get_location(
    location_id: int,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        location = service.get_location(location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        return location
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{location_id}", response_model=Location)
def update_location(
    location_id: int,
    location_in: LocationUpdate,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        location = service.get_location(location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        return service.update_location(location, location_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{location_id}", response_model=Location)
def delete_location(
    location_id: int,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        location = service.get_location(location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        service.delete_location(location)
        return location
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
