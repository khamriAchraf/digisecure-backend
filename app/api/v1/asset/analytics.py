from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_asset_service
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/analytics", tags=["assets:analytics"])


@router.get("/counts/by-type")
def get_asset_counts_by_type(
    service: AssetService = Depends(get_asset_service),
):
    """Get count of assets grouped by type."""
    try:
        return service.get_asset_count_by_type()
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/counts/by-status")
def get_asset_counts_by_status(
    service: AssetService = Depends(get_asset_service),
):
    """Get count of assets grouped by status."""
    try:
        return service.get_asset_count_by_status()
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/counts/by-location")
def get_asset_counts_by_location(
    service: AssetService = Depends(get_asset_service),
):
    """Get count of assets grouped by location."""
    try:
        return service.get_asset_count_by_location()
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
