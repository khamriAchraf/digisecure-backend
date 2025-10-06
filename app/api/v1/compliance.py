from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.models.user import User
from app.schemas.compliance_event import (ComplianceEvent,
                                          ComplianceEventCreate,
                                          ComplianceEventList,
                                          ComplianceEventUpdate)
from app.schemas.compliance_scope import (AssetComplianceScope,
                                          AssetComplianceScopeCreate,
                                          AssetComplianceScopeUpdate)
from app.schemas.compliance_scope import \
    ComplianceControl as ComplianceControlSchema
from app.schemas.compliance_scope import (ComplianceControlListItem,
                                          ComplianceScope,
                                          ComplianceScopeCreate,
                                          ComplianceScopeUpdate)
from app.schemas.compliance_scope import \
    ControlDocumentLink as ControlDocumentLinkSchema
from app.schemas.compliance_scope import (ControlDocumentLinkCreate,
                                          ControlDocumentLinkDelete,
                                          ScopedAsset)
from app.schemas.pagination import PaginatedResponse
from app.services.compliance_event_service import ComplianceEventService
from app.services.compliance_scope_service import (ComplianceScopeService,
                                                   PermissionError)

router = APIRouter(prefix="/compliance", tags=["compliance"])


def get_compliance_service(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ComplianceScopeService:
    return ComplianceScopeService(db, current_user)


def get_compliance_event_service(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ComplianceEventService:
    return ComplianceEventService(db, current_user)


def get_query_filters(request: Request) -> dict:
    filters = {}
    for key, value in request.query_params.items():
        if key not in [
            "page",
            "per_page",
            "sort_by",
            "sort_order",
            "search",
            "cursor",
            "type",
        ]:
            filters[key] = value
    return filters


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


@router.post(
    "/scopes", response_model=ComplianceScope, status_code=status.HTTP_201_CREATED
)
def create_scope(
    scope_in: ComplianceScopeCreate,
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        return service.create_scope(scope_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/scopes/{scope_id}", response_model=ComplianceScope)
def get_scope(
    scope_id: int, service: ComplianceScopeService = Depends(get_compliance_service)
):
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
def delete_scope(
    scope_id: int, service: ComplianceScopeService = Depends(get_compliance_service)
):
    try:
        scope = service.get_scope(scope_id)
        if not scope:
            raise HTTPException(status_code=404, detail="Scope not found")
        service.delete_scope(scope)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Asset tagging endpoints
@router.post(
    "/assets/{asset_id}/scopes/{scope_id}",
    response_model=AssetComplianceScope,
    status_code=status.HTTP_201_CREATED,
)
def tag_asset_scope(
    asset_id: int,
    scope_id: int,
    mapping_in: Optional[AssetComplianceScopeUpdate] = None,
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        payload = mapping_in.dict() if mapping_in else {}
        base = AssetComplianceScopeCreate(
            asset_id=asset_id, scope_id=scope_id, **payload
        )
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


@router.get(
    "/scopes/{scope_id}/assets",
    response_model=PaginatedResponse[ScopedAsset],
)
def list_scope_assets(
    scope_id: int,
    page: Optional[int] = Query(
        None, ge=1, description="Page number (mutually exclusive with cursor)"
    ),
    per_page: int = Query(20, ge=1, le=1000),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    cursor: Optional[int] = Query(
        None, description="Cursor for infinite scroll (mutually exclusive with page)"
    ),
    asset_type: Optional[str] = Query(
        None,
        alias="type",
        description="Filter by asset type (e.g., computer, software, network_device, virtual_machine)",
    ),
    filters: dict = Depends(get_query_filters),
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    # Ensure only one pagination strategy is used
    if page is not None and cursor is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'page' or 'cursor', not both.",
        )

    try:
        effective_filters = dict(filters) if filters else {}
        if asset_type is not None:
            effective_filters["type"] = asset_type
        if cursor is not None:
            return service.get_cursor_scope_assets(
                scope_id=scope_id,
                cursor=cursor,
                per_page=per_page,
                sort_by=sort_by,
                sort_order=sort_order,
                search=search,
                filters=effective_filters,
            )
        else:
            page_number = page or 1
            return service.get_paginated_scope_assets(
                scope_id=scope_id,
                page=page_number,
                per_page=per_page,
                sort_by=sort_by,
                sort_order=sort_order,
                search=search,
                filters=effective_filters,
            )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/scopes/{scope_id}/controls", response_model=List[ComplianceControlListItem]
)
def list_scope_controls(
    scope_id: int,
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        return service.list_scope_controls(scope_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/scopes/{scope_id}/controls/{control_id}",
    response_model=ComplianceControlSchema,
)
def get_scope_control(
    scope_id: int,
    control_id: int,
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        control = service.get_scope_control(scope_id, control_id)
        if control is None:
            raise HTTPException(status_code=404, detail="Control not found")
        return control
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/scopes/{scope_id}/controls/{control_id}/documents",
    response_model=List[ControlDocumentLinkSchema],
    status_code=status.HTTP_201_CREATED,
)
def link_documents_to_control(
    scope_id: int,
    control_id: int,
    payload: ControlDocumentLinkCreate,
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        return service.link_documents_to_control(scope_id, control_id, payload)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/scopes/{scope_id}/controls/{control_id}/documents",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_documents_from_control(
    scope_id: int,
    control_id: int,
    payload: ControlDocumentLinkDelete,
    service: ComplianceScopeService = Depends(get_compliance_service),
):
    try:
        service.unlink_documents_from_control(scope_id, control_id, payload)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/assets/{asset_id}/scopes/{scope_id}", status_code=status.HTTP_204_NO_CONTENT
)
def untag_asset_scope(
    asset_id: int,
    scope_id: int,
    service: ComplianceScopeService = Depends(get_compliance_service),
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


# ============================================================================
# Compliance Events Endpoints
# ============================================================================


@router.get("/events", response_model=PaginatedResponse[ComplianceEventList])
def list_events_paginated(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=1000),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    filters: dict = Depends(get_query_filters),
    service: ComplianceEventService = Depends(get_compliance_event_service),
):
    """List all compliance events with pagination, filtering, and search."""
    try:
        return service.get_paginated_events(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/scopes/{scope_id}/events", response_model=List[ComplianceEventList])
def list_events_by_scope(
    scope_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ComplianceEventService = Depends(get_compliance_event_service),
):
    """List all compliance events for a specific scope."""
    try:
        return service.list_events_by_scope(scope_id=scope_id, skip=skip, limit=limit)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/events", response_model=ComplianceEvent, status_code=status.HTTP_201_CREATED
)
def create_event(
    event_in: ComplianceEventCreate,
    service: ComplianceEventService = Depends(get_compliance_event_service),
):
    """Create a new compliance event."""
    try:
        return service.create_event(event_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/events/{event_id}", response_model=ComplianceEvent)
def get_event(
    event_id: int,
    service: ComplianceEventService = Depends(get_compliance_event_service),
):
    """Get a specific compliance event by ID."""
    try:
        event = service.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/events/{event_id}", response_model=ComplianceEvent)
def update_event(
    event_id: int,
    event_in: ComplianceEventUpdate,
    service: ComplianceEventService = Depends(get_compliance_event_service),
):
    """Update a compliance event."""
    try:
        event = service.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return service.update_event(event, event_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    service: ComplianceEventService = Depends(get_compliance_event_service),
):
    """Delete a compliance event."""
    try:
        event = service.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        service.delete_event(event)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ============================================================================
# Event User Management Endpoints
# ============================================================================


@router.post(
    "/events/{event_id}/users/{user_id}",
    response_model=ComplianceEvent,
    status_code=status.HTTP_201_CREATED,
)
def add_user_to_event(
    event_id: int,
    user_id: int,
    service: ComplianceEventService = Depends(get_compliance_event_service),
):
    """Add a user to an event's notification list."""
    try:
        return service.add_user_to_event(event_id, user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/events/{event_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_user_from_event(
    event_id: int,
    user_id: int,
    service: ComplianceEventService = Depends(get_compliance_event_service),
):
    """Remove a user from an event's notification list."""
    try:
        service.remove_user_from_event(event_id, user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ============================================================================
# Event Group Management Endpoints
# ============================================================================


@router.post(
    "/events/{event_id}/groups/{group_id}",
    response_model=ComplianceEvent,
    status_code=status.HTTP_201_CREATED,
)
def add_group_to_event(
    event_id: int,
    group_id: int,
    service: ComplianceEventService = Depends(get_compliance_event_service),
):
    """Add a group to an event's notification list."""
    try:
        return service.add_group_to_event(event_id, group_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/events/{event_id}/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_group_from_event(
    event_id: int,
    group_id: int,
    service: ComplianceEventService = Depends(get_compliance_event_service),
):
    """Remove a group from an event's notification list."""
    try:
        service.remove_group_from_event(event_id, group_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
