from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.api.dependencies import get_current_user, get_db
from app.db.models.user import User
from app.schemas.table_config import TableConfigResponse, TableConfigUpdate
from app.services.table_config_service import TableConfigService

router = APIRouter(prefix="/table-configs", tags=["table-configs"])


def get_table_config_service(
    db=Depends(get_db), current_user: User = Depends(get_current_user)
):
    return TableConfigService(db, current_user)


@router.get(
    "/{table_key}",
    response_model=TableConfigResponse,
    summary="Get table config for a specific table",
    description="Retrieve the table configuration for a specific table key for the current user.",
)
def get_table_config(
    table_key: str = Path(
        ..., description="The table key (e.g., 'groups', 'users', 'tickets')"
    ),
    service: TableConfigService = Depends(get_table_config_service),
):
    """Get a specific table config for the current user."""
    table_config = service.get_table_config(table_key)
    if not table_config:
        raise HTTPException(status_code=404, detail="Table config not found")
    return table_config


@router.get(
    "/",
    response_model=List[TableConfigResponse],
    summary="List all table configs for the current user",
    description="Retrieve all table configurations for the current user.",
)
def list_table_configs(
    service: TableConfigService = Depends(get_table_config_service),
):
    """List all table configs for the current user."""
    return service.get_user_table_configs()


@router.put(
    "/{table_key}",
    response_model=TableConfigResponse,
    summary="Create or update table config",
    description="Create or update the table configuration for a specific table key for the current user.",
)
def upsert_table_config(
    table_key: str = Path(
        ..., description="The table key (e.g., 'groups', 'users', 'tickets')"
    ),
    body: TableConfigUpdate = None,
    service: TableConfigService = Depends(get_table_config_service),
):
    """Create or update a table config for the current user."""
    return service.create_or_update_table_config(table_key, body.columns)


@router.delete(
    "/{table_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete table config",
    description="Delete the table configuration for a specific table key for the current user.",
)
def delete_table_config(
    table_key: str = Path(
        ..., description="The table key (e.g., 'groups', 'users', 'tickets')"
    ),
    service: TableConfigService = Depends(get_table_config_service),
):
    """Delete a table config for the current user."""
    deleted = service.delete_table_config(table_key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Table config not found")
    return None
