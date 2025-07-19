from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import get_current_user, get_user_service
from app.db.models.user import User
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import PermissionError, UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_query_filters(request: Request) -> dict:
    filters = {}
    for key, value in request.query_params.items():
        if key not in ["page", "per_page", "sort_by", "sort_order", "search"]:
            filters[key] = value
    return filters


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    try:
        user = service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{identifier}/permissions", response_model=List[dict])
def get_user_permissions(
    identifier: str,
    service: UserService = Depends(get_user_service),
):
    try:
        user = service.get_user_by_identifier(identifier)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return service.get_user_permissions(user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/", response_model=PaginatedResponse[UserResponse])
def list_users(
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: UserService = Depends(get_user_service),
    filters: dict = Depends(get_query_filters),
):
    try:
        users, total = service.get_paginated_users(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=users, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service),
):
    try:
        return service.create_user(user_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    service: UserService = Depends(get_user_service),
):
    try:
        user = service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return service.update_user(user, user_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    try:
        user = service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return service.soft_delete_user(user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
