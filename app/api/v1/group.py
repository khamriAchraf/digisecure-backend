from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import get_group_service
from app.schemas.group import (GroupCreate, GroupCreateWithUsers, GroupList,
                               GroupResponse, GroupUpdate)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.group_service import GroupService, PermissionError

router = APIRouter(prefix="/groups", tags=["groups"])


def get_query_filters(request: Request) -> dict:
    filters = {}
    for key, value in request.query_params.items():
        if key not in ["page", "per_page", "sort_by", "sort_order", "search"]:
            filters[key] = value
    return filters


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: int,
    service: GroupService = Depends(get_group_service),
):
    try:
        group = service.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return group
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/", response_model=PaginatedResponse[GroupList])
def list_groups(
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: GroupService = Depends(get_group_service),
    filters: dict = Depends(get_query_filters),
):
    try:
        groups, total = service.get_paginated_groups(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=groups, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    group_in: GroupCreate,
    service: GroupService = Depends(get_group_service),
):
    try:
        return service.create_group(group_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int,
    group_in: GroupUpdate,
    service: GroupService = Depends(get_group_service),
):
    try:
        group = service.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return service.update_group(group, group_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    service: GroupService = Depends(get_group_service),
):
    try:
        group = service.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        service.delete_group(group)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{group_id}/users/{user_id}", response_model=GroupResponse)
def add_user_to_group(
    group_id: int,
    user_id: int,
    service: GroupService = Depends(get_group_service),
):
    from app.db.crud.user import get_user

    user = get_user(service.db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return service.add_user_to_group(group_id, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{group_id}/users/{user_id}", response_model=GroupResponse)
def remove_user_from_group(
    group_id: int,
    user_id: int,
    service: GroupService = Depends(get_group_service),
):
    from app.db.crud.user import get_user

    user = get_user(service.db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return service.remove_user_from_group(group_id, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/with-users", response_model=GroupResponse, status_code=status.HTTP_201_CREATED
)
def create_group_with_users(
    group_in: GroupCreateWithUsers,
    service: GroupService = Depends(get_group_service),
):
    try:
        return service.create_group_with_users(group_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{group_id}/assets/{asset_id}", response_model=GroupResponse)
def add_asset_to_group(
    group_id: int,
    asset_id: int,
    service: GroupService = Depends(get_group_service),
):
    from app.db.crud.asset import get_asset

    asset = get_asset(service.db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    try:
        return service.add_asset_to_group(group_id, asset)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{group_id}/assets/{asset_id}", response_model=GroupResponse)
def remove_asset_from_group(
    group_id: int,
    asset_id: int,
    service: GroupService = Depends(get_group_service),
):
    from app.db.crud.asset import get_asset

    asset = get_asset(service.db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    try:
        return service.remove_asset_from_group(group_id, asset)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
