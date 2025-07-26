from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_reference_data_service
from app.schemas.location import Location, LocationCreate, LocationUpdate
from app.services.reference_data_service import (PermissionError,
                                                 ReferenceDataService)

router = APIRouter(prefix="/locations", tags=["reference_data:locations"])


@router.get("/", response_model=List[Location])
def list_locations(service: ReferenceDataService = Depends(get_reference_data_service)):
    try:
        return service.list_locations()
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
