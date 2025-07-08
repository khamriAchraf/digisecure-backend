from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_configuration_service
from app.schemas.asset_type import AssetType, AssetTypeCreate, AssetTypeUpdate
from app.services.configuration_service import (ConfigurationService,
                                                PermissionError)

router = APIRouter(prefix="/asset_type", tags=["configuration:asset_type"])


@router.get("/", response_model=List[AssetType])
def list_asset_types(
    skip: int = 0,
    limit: int = 100,
    service: ConfigurationService = Depends(get_configuration_service),
):
    try:
        return service.list_asset_types(skip=skip, limit=limit)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/", response_model=AssetType, status_code=status.HTTP_201_CREATED)
def create_asset_type(
    asset_type_in: AssetTypeCreate,
    service: ConfigurationService = Depends(get_configuration_service),
):
    try:
        return service.create_asset_type(asset_type_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{asset_type_id}", response_model=AssetType)
def get_asset_type(
    asset_type_id: int,
    service: ConfigurationService = Depends(get_configuration_service),
):
    try:
        asset_type = service.get_asset_type(asset_type_id)
        if not asset_type:
            raise HTTPException(status_code=404, detail="Asset type not found")
        return asset_type
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{asset_type_id}", response_model=AssetType)
def update_asset_type(
    asset_type_id: int,
    asset_type_in: AssetTypeUpdate,
    service: ConfigurationService = Depends(get_configuration_service),
):
    try:
        asset_type = service.get_asset_type(asset_type_id)
        if not asset_type:
            raise HTTPException(status_code=404, detail="Asset type not found")
        return service.update_asset_type(asset_type, asset_type_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{asset_type_id}", response_model=AssetType)
def delete_asset_type(
    asset_type_id: int,
    service: ConfigurationService = Depends(get_configuration_service),
):
    try:
        asset_type = service.get_asset_type(asset_type_id)
        if not asset_type:
            raise HTTPException(status_code=404, detail="Asset type not found")
        service.delete_asset_type(asset_type)
        return asset_type
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
