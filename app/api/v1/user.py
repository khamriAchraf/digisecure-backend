from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user, get_user_service
from app.db.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import PermissionError, UserService

router = APIRouter(prefix="/users", tags=["users"])


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


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service),
):
    try:
        return service.list_users(skip=skip, limit=limit)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service),
):
    from app.core.security import get_password_hash

    try:
        hashed_password = get_password_hash(user_in.password)
        return service.create_user(user_in, hashed_password)
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


@router.get("/search/", response_model=List[UserResponse])
def search_users(
    query: str = Query(None),
    org_id: int = Query(None),
    status: str = Query(None),
    department: str = Query(None),
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service),
):
    try:
        return service.search_users(
            query=query,
            org_id=org_id,
            status=status,
            department=department,
            skip=skip,
            limit=limit,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
