from datetime import datetime

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import asset as asset_crud
from app.db.models.asset import Asset
from app.db.models.user import User
from app.schemas.asset import AssetCreate, AssetUpdate


class PermissionError(Exception):
    pass


class AssetService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    # CRUD Operations
    def get_asset(self, asset_id: int) -> Asset:
        logger.info(
            f"User {self.current_user.id} attempts to READ asset {asset_id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to asset {asset_id}"
            )
            raise PermissionError("Not allowed to read assets.")
        asset = asset_crud.get_asset(self.db, asset_id)
        logger.info(f"User {self.current_user.id} successfully READ asset {asset_id}")
        return asset

    def list_assets(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST assets at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "asset"):
            logger.warning(f"User {self.current_user.id} denied LIST access to assets")
            raise PermissionError("Not allowed to list assets.")
        assets = asset_crud.list_assets(self.db, skip=skip, limit=limit)
        logger.info(f"User {self.current_user.id} successfully LISTED assets")
        return assets

    def create_asset(self, asset_in: AssetCreate) -> Asset:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE asset {asset_in.name} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "create", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for asset {asset_in.name}"
            )
            raise PermissionError("Not allowed to create assets.")
        try:
            asset = asset_crud.create_asset(self.db, asset_in)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(
            f"User {self.current_user.id} successfully CREATED asset {asset.id}"
        )
        return asset

    def update_asset(self, asset: Asset, asset_in: AssetUpdate) -> Asset:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE asset {asset.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "update", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for asset {asset.id}"
            )
            raise PermissionError("Not allowed to update assets.")
        updated_asset = asset_crud.update_asset(self.db, asset, asset_in)
        logger.info(
            f"User {self.current_user.id} successfully UPDATED asset {asset.id}"
        )
        return updated_asset

    def delete_asset(self, asset: Asset) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE asset {asset.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for asset {asset.id}"
            )
            raise PermissionError("Not allowed to delete assets.")
        asset_crud.delete_asset(self.db, asset)
        logger.info(
            f"User {self.current_user.id} successfully DELETED asset {asset.id}"
        )
