from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import (CertificateKey, CertificateKeyCreate,
                               CertificateKeyList, CertificateKeyUpdate)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/certificate_keys", tags=["assets:certificate_keys"])


@router.get("/", response_model=PaginatedResponse[CertificateKeyList])
def list_certificate_keys(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all certificate keys with optional filtering."""
    try:
        assets, total = service.get_paginated_certificate_keys(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/", response_model=CertificateKey, status_code=status.HTTP_201_CREATED)
def create_certificate_key(
    certificate_key_in: CertificateKeyCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new certificate key."""
    try:
        return service.create_certificate_key(certificate_key_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{certificate_key_id}", response_model=CertificateKey)
def get_certificate_key(
    certificate_key_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific certificate key by ID."""
    try:
        certificate_key = service.get_certificate_key(certificate_key_id)
        if not certificate_key:
            raise HTTPException(status_code=404, detail="Certificate key not found")
        return certificate_key
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{certificate_key_id}", response_model=CertificateKey)
def update_certificate_key(
    certificate_key_id: int,
    certificate_key_in: CertificateKeyUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a certificate key."""
    try:
        certificate_key = service.get_certificate_key(certificate_key_id)
        if not certificate_key:
            raise HTTPException(status_code=404, detail="Certificate key not found")
        return service.update_certificate_key(certificate_key, certificate_key_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{certificate_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificate_key(
    certificate_key_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a certificate key."""
    try:
        certificate_key = service.get_certificate_key(certificate_key_id)
        if not certificate_key:
            raise HTTPException(status_code=404, detail="Certificate key not found")
        service.delete_certificate_key(certificate_key)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
