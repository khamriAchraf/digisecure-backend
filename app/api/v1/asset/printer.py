from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import Printer, PrinterCreate, PrinterUpdate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/printers", tags=["assets:printers"])


@router.get("/", response_model=PaginatedResponse[Printer])
def list_printers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all printers with optional filtering."""
    try:
        assets, total = service.get_paginated_printers(
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


@router.post("/", response_model=Printer, status_code=status.HTTP_201_CREATED)
def create_printer(
    printer_in: PrinterCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new printer."""
    try:
        return service.create_printer(printer_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{printer_id}", response_model=Printer)
def get_printer(
    printer_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific printer by ID."""
    try:
        printer = service.get_printer(printer_id)
        if not printer:
            raise HTTPException(status_code=404, detail="Printer not found")
        return printer
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{printer_id}", response_model=Printer)
def update_printer(
    printer_id: int,
    printer_in: PrinterUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a printer."""
    try:
        printer = service.get_printer(printer_id)
        if not printer:
            raise HTTPException(status_code=404, detail="Printer not found")
        return service.update_printer(printer, printer_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_printer(
    printer_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a printer."""
    try:
        printer = service.get_printer(printer_id)
        if not printer:
            raise HTTPException(status_code=404, detail="Printer not found")
        service.delete_printer(printer)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
