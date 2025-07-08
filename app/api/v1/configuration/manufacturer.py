from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_configuration_service
from app.schemas.manufacturer import (Manufacturer, ManufacturerCreate,
                                      ManufacturerUpdate)
from app.services.configuration_service import (ConfigurationService,
                                                PermissionError)

router = APIRouter(prefix="/manufacturer", tags=["configuration:manufacturer"])


@router.get("/", response_model=List[Manufacturer])
def list_manufacturers(
    skip: int = 0,
    limit: int = 100,
    service: ConfigurationService = Depends(get_configuration_service),
):
    try:
        return service.list_manufacturers(skip=skip, limit=limit)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/", response_model=Manufacturer, status_code=status.HTTP_201_CREATED)
def create_manufacturer(
    manufacturer_in: ManufacturerCreate,
    service: ConfigurationService = Depends(get_configuration_service),
):
    try:
        return service.create_manufacturer(manufacturer_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{manufacturer_id}", response_model=Manufacturer)
def get_manufacturer(
    manufacturer_id: int,
    service: ConfigurationService = Depends(get_configuration_service),
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
    service: ConfigurationService = Depends(get_configuration_service),
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
    service: ConfigurationService = Depends(get_configuration_service),
):
    try:
        manufacturer = service.get_manufacturer(manufacturer_id)
        if not manufacturer:
            raise HTTPException(status_code=404, detail="Manufacturer not found")
        service.delete_manufacturer(manufacturer)
        return manufacturer
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
