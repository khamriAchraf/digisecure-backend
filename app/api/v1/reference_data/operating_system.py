from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import get_reference_data_service
from app.schemas.operating_system import (OperatingSystem,
                                          OperatingSystemCreate,
                                          OperatingSystemUpdate)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.reference_data_service import (PermissionError,
                                                 ReferenceDataService)

router = APIRouter(
    prefix="/operating_systems", tags=["reference_data:operating_systems"]
)


def get_query_filters(request: Request) -> dict:
    filters = {}
    for key, value in request.query_params.items():
        if key not in ["page", "per_page", "sort_by", "sort_order", "search"]:
            filters[key] = value
    return filters


@router.get("/", response_model=PaginatedResponse[OperatingSystem])
def list_operating_systems(
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: ReferenceDataService = Depends(get_reference_data_service),
    filters: dict = Depends(get_query_filters),
):
    try:
        items, total = service.get_paginated_operating_systems(
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


@router.post("/", response_model=OperatingSystem, status_code=status.HTTP_201_CREATED)
def create_operating_system(
    operating_system_in: OperatingSystemCreate,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        return service.create_operating_system(operating_system_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{operating_system_id}", response_model=OperatingSystem)
def get_operating_system(
    operating_system_id: int,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        operating_system = service.get_operating_system(operating_system_id)
        if not operating_system:
            raise HTTPException(status_code=404, detail="Operating system not found")
        return operating_system
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{operating_system_id}", response_model=OperatingSystem)
def update_operating_system(
    operating_system_id: int,
    operating_system_in: OperatingSystemUpdate,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        operating_system = service.get_operating_system(operating_system_id)
        if not operating_system:
            raise HTTPException(status_code=404, detail="Operating system not found")
        return service.update_operating_system(operating_system, operating_system_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{operating_system_id}", response_model=OperatingSystem)
def delete_operating_system(
    operating_system_id: int,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        operating_system = service.get_operating_system(operating_system_id)
        if not operating_system:
            raise HTTPException(status_code=404, detail="Operating system not found")
        service.delete_operating_system(operating_system)
        return operating_system
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
