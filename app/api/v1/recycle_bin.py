from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_recycle_bin_service
from app.api.v1.user import get_query_filters
from app.schemas.asset import Asset as AssetSchema
from app.schemas.asset import DeletedAssetList
from app.schemas.group import GroupList
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.schemas.user import UserResponse
from app.services.recycle_bin_service import RecycleBinService
from app.services.user_service import PermissionError

router = APIRouter(prefix="/recycle_bin", tags=["recycle_bin"])


@router.get("/users", response_model=PaginatedResponse[UserResponse])
def list_deleted_users(
    page: Optional[int] = Query(
        None, ge=1, description="Page number (mutually exclusive with cursor)"
    ),
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    cursor: Optional[int] = Query(
        None, description="Cursor for infinite scroll (mutually exclusive with page)"
    ),
    service: RecycleBinService = Depends(get_recycle_bin_service),
    filters: dict = Depends(get_query_filters),
):
    if page is not None and cursor is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'page' or 'cursor', not both.",
        )
    try:
        page_number = page or 1
        users, total = service.get_paginated_deleted_users(
            page=page_number,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=users, total=total, page=page_number, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/users/{user_id}/purge",
    status_code=status.HTTP_204_NO_CONTENT,
)
def purge_user(
    user_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        purged = service.purge_user(user_id)
        if not purged:
            raise HTTPException(status_code=404, detail="User not found or not deleted")
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/users/{user_id}/restore",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
)
def restore_user(
    user_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        restored = service.restore_user(user_id)
        if not restored:
            raise HTTPException(status_code=404, detail="User not found or not deleted")
        return restored
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/groups", response_model=PaginatedResponse[GroupList])
def list_deleted_groups(
    page: Optional[int] = Query(None, ge=1),
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: RecycleBinService = Depends(get_recycle_bin_service),
    filters: dict = Depends(get_query_filters),
):
    page_number = page or 1
    try:
        groups, total = service._get_paginated_deleted_groups(
            page=page_number,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=groups, total=total, page=page_number, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/assets/{asset_id}/restore",
    status_code=status.HTTP_200_OK,
    response_model=AssetSchema,
)
def restore_asset(
    asset_id: int,
    asset_type: str = Query(..., description="Type of asset to restore"),
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        restored = service.restore_asset(asset_id=asset_id, asset_type=asset_type)
        if not restored:
            raise HTTPException(
                status_code=404, detail="Asset not found or not deleted"
            )
        return restored
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/assets/computers/{asset_id}/restore",
    status_code=status.HTTP_200_OK,
    response_model=AssetSchema,
)
def restore_computer(
    asset_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        restored = service.restore_asset(asset_id=asset_id, asset_type="computer")
        if not restored:
            raise HTTPException(
                status_code=404, detail="Asset not found or not deleted"
            )
        return restored
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/assets/network_devices/{asset_id}/restore",
    status_code=status.HTTP_200_OK,
    response_model=AssetSchema,
)
def restore_network_device(
    asset_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        restored = service.restore_asset(asset_id=asset_id, asset_type="network_device")
        if not restored:
            raise HTTPException(
                status_code=404, detail="Asset not found or not deleted"
            )
        return restored
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/assets/virtual_machines/{asset_id}/restore",
    status_code=status.HTTP_200_OK,
    response_model=AssetSchema,
)
def restore_virtual_machine(
    asset_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        restored = service.restore_asset(
            asset_id=asset_id, asset_type="virtual_machine"
        )
        if not restored:
            raise HTTPException(
                status_code=404, detail="Asset not found or not deleted"
            )
        return restored
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/assets/software/{asset_id}/restore",
    status_code=status.HTTP_200_OK,
    response_model=AssetSchema,
)
def restore_software(
    asset_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        restored = service.restore_asset(asset_id=asset_id, asset_type="software")
        if not restored:
            raise HTTPException(
                status_code=404, detail="Asset not found or not deleted"
            )
        return restored
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/assets/certificate_keys/{asset_id}/restore",
    status_code=status.HTTP_200_OK,
    response_model=AssetSchema,
)
def restore_certificate_key(
    asset_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        restored = service.restore_asset(
            asset_id=asset_id, asset_type="certificate_key"
        )
        if not restored:
            raise HTTPException(
                status_code=404, detail="Asset not found or not deleted"
            )
        return restored
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/assets/computers/{asset_id}/purge",
    status_code=status.HTTP_200_OK,
    response_model=AssetSchema,
)
def purge_computer(
    asset_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        purged = service.purge_asset(asset_id=asset_id, asset_type="computer")
        if not purged:
            raise HTTPException(
                status_code=404, detail="Asset not found or not deleted"
            )
        return purged
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/assets/network_devices/{asset_id}/purge",
    status_code=status.HTTP_200_OK,
    response_model=AssetSchema,
)
def purge_network_device(
    asset_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        purged = service.purge_asset(asset_id=asset_id, asset_type="network_device")
        if not purged:
            raise HTTPException(
                status_code=404, detail="Asset not found or not deleted"
            )
        return purged
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/assets/virtual_machines/{asset_id}/purge",
    status_code=status.HTTP_200_OK,
    response_model=AssetSchema,
)
def purge_virtual_machine(
    asset_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        purged = service.purge_asset(asset_id=asset_id, asset_type="virtual_machine")
        if not purged:
            raise HTTPException(
                status_code=404, detail="Asset not found or not deleted"
            )
        return purged
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/assets/software/{asset_id}/purge",
    status_code=status.HTTP_200_OK,
    response_model=AssetSchema,
)
def purge_software(
    asset_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        purged = service.purge_asset(asset_id=asset_id, asset_type="software")
        if not purged:
            raise HTTPException(
                status_code=404, detail="Asset not found or not deleted"
            )
        return purged
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/assets/certificate_keys/{asset_id}/purge",
    status_code=status.HTTP_200_OK,
    response_model=AssetSchema,
)
def purge_certificate_key(
    asset_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        purged = service.purge_asset(asset_id=asset_id, asset_type="certificate_key")
        if not purged:
            raise HTTPException(
                status_code=404, detail="Asset not found or not deleted"
            )
        return purged
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/assets/computers", response_model=PaginatedResponse[DeletedAssetList])
def list_deleted_computers(
    page: Optional[int] = Query(None, ge=1),
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: RecycleBinService = Depends(get_recycle_bin_service),
    filters: dict = Depends(get_query_filters),
):
    page_number = page or 1
    try:
        assets, total = service._get_paginated_deleted_assets_by_type(
            asset_type="computer",
            page=page_number,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page_number, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/assets/network_devices", response_model=PaginatedResponse[DeletedAssetList]
)
def list_deleted_network_devices(
    page: Optional[int] = Query(None, ge=1),
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: RecycleBinService = Depends(get_recycle_bin_service),
    filters: dict = Depends(get_query_filters),
):
    page_number = page or 1
    try:
        assets, total = service._get_paginated_deleted_assets_by_type(
            asset_type="network_device",
            page=page_number,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page_number, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/assets/virtual_machines", response_model=PaginatedResponse[DeletedAssetList]
)
def list_deleted_virtual_machines(
    page: Optional[int] = Query(None, ge=1),
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: RecycleBinService = Depends(get_recycle_bin_service),
    filters: dict = Depends(get_query_filters),
):
    page_number = page or 1
    try:
        assets, total = service._get_paginated_deleted_assets_by_type(
            asset_type="virtual_machine",
            page=page_number,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page_number, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/assets/software", response_model=PaginatedResponse[DeletedAssetList])
def list_deleted_software(
    page: Optional[int] = Query(None, ge=1),
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: RecycleBinService = Depends(get_recycle_bin_service),
    filters: dict = Depends(get_query_filters),
):
    page_number = page or 1
    try:
        assets, total = service._get_paginated_deleted_assets_by_type(
            asset_type="software",
            page=page_number,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page_number, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/assets/certificate_keys", response_model=PaginatedResponse[DeletedAssetList]
)
def list_deleted_certificate_keys(
    page: Optional[int] = Query(None, ge=1),
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: RecycleBinService = Depends(get_recycle_bin_service),
    filters: dict = Depends(get_query_filters),
):
    page_number = page or 1
    try:
        assets, total = service._get_paginated_deleted_assets_by_type(
            asset_type="certificate_key",
            page=page_number,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page_number, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/assets", response_model=PaginatedResponse[DeletedAssetList])
def list_deleted_assets(
    page: Optional[int] = Query(
        None, ge=1, description="Page number (mutually exclusive with cursor)"
    ),
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(
        None,
        description="Filter by asset type: computer, network_device, virtual_machine, software, certificate_key",
    ),
    service: RecycleBinService = Depends(get_recycle_bin_service),
    filters: dict = Depends(get_query_filters),
):
    if page is not None:
        page_number = page or 1
    else:
        page_number = 1
    try:
        # Merge asset_type into filters for the service helper
        merged_filters = dict(filters or {})
        if asset_type:
            merged_filters["type"] = asset_type

        assets, total = service._get_paginated_deleted_assets_by_type(
            page=page_number,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=merged_filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page_number, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/groups/{group_id}/purge", status_code=status.HTTP_200_OK, response_model=GroupList
)
def purge_group(
    group_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        purged = service.purge_group(group_id)
        if not purged:
            raise HTTPException(
                status_code=404, detail="Group not found or not deleted"
            )
        return purged
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/groups/{group_id}/restore",
    status_code=status.HTTP_200_OK,
    response_model=GroupList,
)
def restore_group(
    group_id: int,
    service: RecycleBinService = Depends(get_recycle_bin_service),
):
    try:
        restored = service.restore_group(group_id)
        if not restored:
            raise HTTPException(
                status_code=404, detail="Group not found or not deleted"
            )
        return restored
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
