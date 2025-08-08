from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.models.user import User
from app.schemas.compliance_scope import (
    AssetComplianceScope,
    AssetComplianceScopeCreate,
    AssetComplianceScopeUpdate,
    ComplianceScope,
    ComplianceScopeCreate,
    ComplianceScopeUpdate,
)
from app.services.compliance_scope_service import (
    ComplianceScopeService,
    PermissionError,
)


router = APIRouter(prefix="/compliance", tags=["compliance"]) 


def get_compliance_service(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ComplianceScopeService:
    return ComplianceScopeService(db, current_user)


@router.get("/scopes", response_model=List[ComplianceScope])
def list_scopes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        return service.list_scopes(skip=skip, limit=limit)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/scopes", response_model=ComplianceScope, status_code=status.HTTP_201_CREATED)
def create_scope(
    scope_in: ComplianceScopeCreate, service: ComplianceScopeService = Depends(get_compliance_service)
):
    try:
        return service.create_scope(scope_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/scopes/{scope_id}", response_model=ComplianceScope)
def get_scope(scope_id: int, service: ComplianceScopeService = Depends(get_compliance_service)):
    try:
        scope = service.get_scope(scope_id)
        if not scope:
            raise HTTPException(status_code=404, detail="Scope not found")
        return scope
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/scopes/{scope_id}", response_model=ComplianceScope)
def update_scope(
    scope_id: int,
    scope_in: ComplianceScopeUpdate,
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        scope = service.get_scope(scope_id)
        if not scope:
            raise HTTPException(status_code=404, detail="Scope not found")
        return service.update_scope(scope, scope_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/scopes/{scope_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scope(scope_id: int, service: ComplianceScopeService = Depends(get_compliance_service)):
    try:
        scope = service.get_scope(scope_id)
        if not scope:
            raise HTTPException(status_code=404, detail="Scope not found")
        service.delete_scope(scope)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Asset tagging endpoints
@router.post("/assets/{asset_id}/scopes/{scope_id}", response_model=AssetComplianceScope, status_code=status.HTTP_201_CREATED)
def tag_asset_scope(
    asset_id: int,
    scope_id: int,
    mapping_in: Optional[AssetComplianceScopeUpdate] = None,
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        payload = mapping_in.dict() if mapping_in else {}
        base = AssetComplianceScopeCreate(asset_id=asset_id, scope_id=scope_id, **payload)
        return service.tag_asset_with_scope(base)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/assets/{asset_id}/scopes/{scope_id}", response_model=AssetComplianceScope)
def update_asset_scope(
    asset_id: int,
    scope_id: int,
    mapping_in: AssetComplianceScopeUpdate,
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        return service.update_asset_scope(asset_id, scope_id, mapping_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/assets/{asset_id}/scopes/{scope_id}", status_code=status.HTTP_204_NO_CONTENT)
def untag_asset_scope(
    asset_id: int, scope_id: int, service: ComplianceScopeService = Depends(get_compliance_service)
):
    try:
        service.untag_asset_scope(asset_id, scope_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/assets/{asset_id}/scopes", status_code=status.HTTP_204_NO_CONTENT)
def replace_asset_scopes(
    asset_id: int,
    scope_ids: List[int],
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        service.replace_asset_scopes(asset_id, scope_ids)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


