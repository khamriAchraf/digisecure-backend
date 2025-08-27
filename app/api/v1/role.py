from typing import List, Optional, Union

from fastapi import (APIRouter, Depends, HTTPException, Path, Query, Request,
                     status)
from pydantic import BaseModel

from app.api.dependencies import get_current_user, get_db
from app.db.models.role import Permission
from app.db.models.user import User
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.schemas.role import (PermissionResponse, RoleCreate, RoleResponse,
                              RoleUpdate)
from app.services.role_service import PermissionError, RoleService

router = APIRouter(prefix="/roles", tags=["roles"])


def get_query_filters(request: Request) -> dict:
    filters = {}
    for key, value in request.query_params.items():
        if key not in ["page", "per_page", "sort_by", "sort_order", "search"]:
            filters[key] = value
    return filters


def get_role_service(
    db=Depends(get_db), current_user: User = Depends(get_current_user)
):
    return RoleService(db, current_user)


@router.get(
    "/",
    response_model=PaginatedResponse[RoleResponse],
    summary="List all roles",
    description="Retrieve a paginated list of all roles with support for sorting, searching, and filtering.",
)
def list_roles(
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: RoleService = Depends(get_role_service),
    filters: dict = Depends(get_query_filters),
):
    """List all roles with pagination, sorting, search, and filtering."""
    try:
        roles, total = service.get_paginated_roles(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=roles, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/permissions",
    response_model=List[PermissionResponse],
    summary="List all permissions",
    description="Retrieve a list of all permissions.",
)
def list_permissions(current_user: User = Depends(get_current_user)):
    """List all permissions."""
    from app.core.security import has_permission

    if not has_permission(current_user, "read", "role"):
        raise HTTPException(status_code=403, detail="Not allowed to list permissions.")
    from app.main import permissions_cache

    return permissions_cache


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Get a role by ID",
    description="Retrieve a role by its ID.",
)
def get_role(role_id: int, service: RoleService = Depends(get_role_service)):
    """Get a role by ID."""
    try:
        role = service.get_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
    description="Create a new role.",
)
def create_role(role_in: RoleCreate, service: RoleService = Depends(get_role_service)):
    """Create a new role."""
    try:
        return service.create_role(
            role_in.name, role_in.description, role_in.is_builtin or False
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Update a role",
    description="Update an existing role.",
)
def update_role(
    role_id: int, role_in: RoleUpdate, service: RoleService = Depends(get_role_service)
):
    """Update a role. This is only for updating the name and description of the role.
    To update the permissions of a role:
    - Use the bulk_update_permissions
    - Use the assign_permission
    - Use the unassign_permission
    """
    try:
        role = service.get_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return service.update_role(role, role_in.name, role_in.description)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a role",
    description="Delete a role by its ID.",
)
def delete_role(role_id: int, service: RoleService = Depends(get_role_service)):
    """Delete a role by ID."""
    try:
        role = service.get_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        service.delete_role(role)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/{role_id}/permissions/{permission_id}",
    response_model=RoleResponse,
    summary="Assign a permission to a role",
    description="Assign a permission to a role by permission ID or slug.\n\nYou can use either:\n- The integer ID of the permission (e.g., 1)\n- A slug in the form 'resource:action' (e.g., 'user:read')\n\nIf a slug is provided, the API will look up the permission by resource and action.",
)
def assign_permission(
    role_id: int,
    permission_id: str = Path(
        ...,
        description="Permission ID (int) or slug (resource:action, e.g., 'user:read')",
    ),
    service: RoleService = Depends(get_role_service),
):
    """
    Assign a permission to a role by permission ID or slug.
    You can use either:
    - The integer ID of the permission (e.g., 1)
    - A slug in the form 'resource:action' (e.g., 'user:read')
    If a slug is provided, the API will look up the permission by resource and action.
    """
    try:
        role = service.get_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        try:
            perm_id = int(permission_id)
            permission = service.db.query(Permission).get(perm_id)
        except ValueError:
            if ":" not in permission_id:
                raise HTTPException(
                    status_code=400,
                    detail="Permission slug must be in the form 'resource:action'",
                )
            resource, action = permission_id.split(":", 1)
            permission = (
                service.db.query(Permission)
                .filter_by(resource=resource, action=action)
                .first()
            )
        if not permission:
            raise HTTPException(status_code=404, detail="Permission not found")
        return service.assign_permission(role, permission)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    response_model=RoleResponse,
    summary="Unassign a permission from a role",
    description="Unassign a permission from a role by permission ID or slug.\n\nYou can use either:\n- The integer ID of the permission (e.g., 1)\n- A slug in the form 'resource:action' (e.g., 'user:read')\n\nIf a slug is provided, the API will look up the permission by resource and action.",
)
def unassign_permission(
    role_id: int,
    permission_id: str = Path(
        ...,
        description="Permission ID (int) or slug (resource:action, e.g., 'user:read')",
    ),
    service: RoleService = Depends(get_role_service),
):
    """
    Unassign a permission from a role by permission ID or slug.
    You can use either:
    - The integer ID of the permission (e.g., 1)
    - A slug in the form 'resource:action' (e.g., 'user:read')
    If a slug is provided, the API will look up the permission by resource and action.
    """
    try:
        role = service.get_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        try:
            perm_id = int(permission_id)
            permission = service.db.query(Permission).get(perm_id)
        except ValueError:
            if ":" not in permission_id:
                raise HTTPException(
                    status_code=400,
                    detail="Permission slug must be in the form 'resource:action'",
                )
            resource, action = permission_id.split(":", 1)
            permission = (
                service.db.query(Permission)
                .filter_by(resource=resource, action=action)
                .first()
            )
        if not permission:
            raise HTTPException(status_code=404, detail="Permission not found")
        return service.unassign_permission(role, permission)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


class BulkPermissionsUpdate(BaseModel):
    permissions: list[Union[int, str]]


@router.put(
    "/{role_id}/permissions",
    response_model=RoleResponse,
    summary="Bulk update role permissions",
    description='Bulk update a role\'s permissions.\n\nRequest body should be a JSON object with a \'permissions\' field containing a list of either permission IDs (ints) or slugs (strings in the form \'resource:action\').\n\nExample:\n{\n  "permissions": [1, 2, "user:read", "role:create"]\n}\n\nAll previous permissions will be replaced by the provided set.',
)
def bulk_update_permissions(
    role_id: int,
    body: BulkPermissionsUpdate,
    service: RoleService = Depends(get_role_service),
):
    """
    Bulk update a role's permissions.
    Request body should be a JSON object with a 'permissions' field containing a list of either permission IDs (ints) or slugs (strings in the form 'resource:action').
    All previous permissions will be replaced by the provided set.
    """
    try:
        role = service.get_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        # Resolve all permissions
        resolved_permissions = []
        for perm in body.permissions:
            if isinstance(perm, int):
                permission = service.db.query(Permission).get(perm)
            elif isinstance(perm, str):
                if ":" not in perm:
                    raise HTTPException(
                        status_code=400,
                        detail="Permission slug must be in the form 'resource:action'",
                    )
                resource, action = perm.split(":", 1)
                permission = (
                    service.db.query(Permission)
                    .filter_by(resource=resource, action=action)
                    .first()
                )
            else:
                raise HTTPException(
                    status_code=400, detail="Invalid permission identifier"
                )
            if not permission:
                raise HTTPException(
                    status_code=404, detail=f"Permission not found: {perm}"
                )
            resolved_permissions.append(permission)
        # Replace role's permissions
        role.permissions = resolved_permissions
        service.db.commit()
        service.db.refresh(role)
        return role
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
