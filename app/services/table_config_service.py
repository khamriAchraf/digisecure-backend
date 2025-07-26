from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.db.crud import table_config as table_config_crud
from app.db.models.table_config import TableConfig
from app.db.models.user import User


class PermissionError(Exception):
    pass


class TableConfigService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def get_table_config(self, table_key: str) -> Optional[TableConfig]:
        """Get a specific table config for the current user."""
        logger.info(
            f"User {self.current_user.id} attempts to READ table config for '{table_key}' at {datetime.now(timezone.utc).isoformat()}"
        )
        # Users can only access their own table configs
        table_config = table_config_crud.get_table_config(
            self.db, self.current_user.id, table_key
        )
        if table_config:
            logger.info(
                f"User {self.current_user.id} successfully READ table config for '{table_key}'"
            )
        return table_config

    def get_user_table_configs(self) -> List[TableConfig]:
        """Get all table configs for the current user."""
        logger.info(
            f"User {self.current_user.id} attempts to LIST table configs at {datetime.now(timezone.utc).isoformat()}"
        )
        table_configs = table_config_crud.get_user_table_configs(
            self.db, self.current_user.id
        )
        logger.info(
            f"User {self.current_user.id} successfully LISTED {len(table_configs)} table configs"
        )
        return table_configs

    def create_table_config(self, table_key: str, columns: List[str]) -> TableConfig:
        """Create a new table config for the current user."""
        logger.info(
            f"User {self.current_user.id} attempts to CREATE table config for '{table_key}' at {datetime.now(timezone.utc).isoformat()}"
        )
        try:
            table_config = table_config_crud.create_table_config(
                self.db, self.current_user.id, table_key, columns
            )
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))

        logger.info(
            f"User {self.current_user.id} successfully CREATED table config {table_config.id} for '{table_key}'"
        )
        return table_config

    def update_table_config(self, table_key: str, columns: List[str]) -> TableConfig:
        """Update an existing table config for the current user."""
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE table config for '{table_key}' at {datetime.now(timezone.utc).isoformat()}"
        )
        try:
            table_config = table_config_crud.update_table_config(
                self.db, self.current_user.id, table_key, columns
            )
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail=str(e))

        logger.info(
            f"User {self.current_user.id} successfully UPDATED table config for '{table_key}'"
        )
        return table_config

    def create_or_update_table_config(
        self, table_key: str, columns: List[str]
    ) -> TableConfig:
        """Create or update a table config for the current user (upsert operation)."""
        logger.info(
            f"User {self.current_user.id} attempts to UPSERT table config for '{table_key}' at {datetime.now(timezone.utc).isoformat()}"
        )
        try:
            table_config = table_config_crud.create_or_update_table_config(
                self.db, self.current_user.id, table_key, columns
            )
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))

        logger.info(
            f"User {self.current_user.id} successfully UPSERTED table config for '{table_key}'"
        )
        return table_config

    def delete_table_config(self, table_key: str) -> bool:
        """Delete a table config for the current user."""
        logger.info(
            f"User {self.current_user.id} attempts to DELETE table config for '{table_key}' at {datetime.now(timezone.utc).isoformat()}"
        )
        deleted = table_config_crud.delete_table_config(
            self.db, self.current_user.id, table_key
        )
        if deleted:
            logger.info(
                f"User {self.current_user.id} successfully DELETED table config for '{table_key}'"
            )
        return deleted
