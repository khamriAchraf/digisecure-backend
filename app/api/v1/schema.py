from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_schema_service
from app.services.schema_service import PermissionError, SchemaService

router = APIRouter(prefix="/schemas", tags=["schemas"])


@router.get("/{resource_type}")
def get_resource_schema(
    resource_type: str,
    service: SchemaService = Depends(get_schema_service),
):
    """
    Get JSON schema for a specific resource type.
    Requires 'create' permission on the resource.
    """
    try:
        schema = service.get_resource_schema(resource_type)
        return schema
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def get_available_resources(
    service: SchemaService = Depends(get_schema_service),
):
    """
    Get list of available resource types that the user has create permission for.
    """
    try:
        resources = service.get_available_resources()
        return resources
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
