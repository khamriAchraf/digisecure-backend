from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import get_reference_data_service
from app.schemas.manufacturer import (Manufacturer, ManufacturerCreate,
                                      ManufacturerUpdate)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.reference_data_service import (PermissionError,
                                                 ReferenceDataService)

router = APIRouter(prefix="/manufacturers", tags=["reference_data:manufacturers"])


def get_query_filters(request: Request) -> dict:
    filters = {}
    for key, value in request.query_params.items():
        if key not in ["page", "per_page", "sort_by", "sort_order", "search"]:
            filters[key] = value
    return filters


@router.get("/", response_model=PaginatedResponse[Manufacturer])
def list_manufacturers(
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: ReferenceDataService = Depends(get_reference_data_service),
    filters: dict = Depends(get_query_filters),
):
    try:
        items, total = service.get_paginated_manufacturers(
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


@router.post("/", response_model=Manufacturer, status_code=status.HTTP_201_CREATED)
def create_manufacturer(
    manufacturer_in: ManufacturerCreate,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        return service.create_manufacturer(manufacturer_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{manufacturer_id}", response_model=Manufacturer)
def get_manufacturer(
    manufacturer_id: int,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        manufacturer = service.get_manufacturer(manufacturer_id)
        if not manufacturer:
            raise HTTPException(status_code=404, detail="Manufacturer not found")
        return manufacturer
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{manufacturer_id}", response_model=Manufacturer)
def update_manufacturer(
    manufacturer_id: int,
    manufacturer_in: ManufacturerUpdate,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        manufacturer = service.get_manufacturer(manufacturer_id)
        if not manufacturer:
            raise HTTPException(status_code=404, detail="Manufacturer not found")
        return service.update_manufacturer(manufacturer, manufacturer_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{manufacturer_id}", response_model=Manufacturer)
def delete_manufacturer(
    manufacturer_id: int,
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    try:
        manufacturer = service.get_manufacturer(manufacturer_id)
        if not manufacturer:
            raise HTTPException(status_code=404, detail="Manufacturer not found")
        service.delete_manufacturer(manufacturer)
        return manufacturer
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
