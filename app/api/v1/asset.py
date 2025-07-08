from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_asset_service
from app.schemas.asset import Asset, AssetCreate, AssetUpdate
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/{asset_id}", response_model=Asset)
def get_asset(
    asset_id: int,
    service: AssetService = Depends(get_asset_service),
):
    try:
        asset = service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/", response_model=List[Asset])
def list_assets(
    skip: int = 0,
    limit: int = 100,
    service: AssetService = Depends(get_asset_service),
):
    try:
        return service.list_assets(skip=skip, limit=limit)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/", response_model=Asset, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset_in: AssetCreate,
    service: AssetService = Depends(get_asset_service),
):
    try:
        return service.create_asset(asset_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{asset_id}", response_model=Asset)
def update_asset(
    asset_id: int,
    asset_in: AssetUpdate,
    service: AssetService = Depends(get_asset_service),
):
    try:
        asset = service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        return service.update_asset(asset, asset_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: int,
    service: AssetService = Depends(get_asset_service),
):
    try:
        asset = service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        service.delete_asset(asset)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
