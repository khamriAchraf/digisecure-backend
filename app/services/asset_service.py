from datetime import datetime
from typing import List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import asset as asset_crud
from app.db.models.asset import Asset
from app.db.models.user import User
from app.schemas.asset import (AssetCreate, AssetUpdate, CableCreate,
                               CableUpdate, ComputerCreate, ComputerUpdate,
                               ConsumableCreate, ConsumableUpdate,
                               NetworkDeviceCreate, NetworkDeviceUpdate,
                               PeripheralCreate, PeripheralUpdate, PhoneCreate,
                               PhoneUpdate, PrinterCreate, PrinterUpdate,
                               RackCreate, RackUpdate, SimCardItemCreate,
                               SimCardItemUpdate)


class PermissionError(Exception):
    pass


class AssetService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

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

    def get_asset_by_type(self, asset_id: int, asset_type: str) -> Asset:
        """Get a specific asset type by ID."""
        logger.info(
            f"User {self.current_user.id} attempts to READ {asset_type} {asset_id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to {asset_type} {asset_id}"
            )
            raise PermissionError("Not allowed to read assets.")
        asset = asset_crud.get_asset_by_type(self.db, asset_id, asset_type)
        logger.info(
            f"User {self.current_user.id} successfully READ {asset_type} {asset_id}"
        )
        return asset

    def get_paginated_assets(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[Asset], int]:
        logger.info(
            f"User {self.current_user.id} attempts to LIST assets with pagination at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "asset"):
            logger.warning(f"User {self.current_user.id} denied LIST access to assets")
            raise PermissionError("Not allowed to list assets.")

        assets, total = asset_crud.get_paginated_assets(
            self.db, page, per_page, sort_by, sort_order, search, filters
        )
        logger.info(f"User {self.current_user.id} successfully LISTED assets")
        return assets, total

    def create_asset(
        self,
        asset_in: Union[
            AssetCreate,
            ComputerCreate,
            PrinterCreate,
            NetworkDeviceCreate,
            PhoneCreate,
            PeripheralCreate,
            ConsumableCreate,
            RackCreate,
            CableCreate,
            SimCardItemCreate,
        ],
    ) -> Asset:
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

    def update_asset(
        self,
        asset: Asset,
        asset_in: Union[
            AssetUpdate,
            ComputerUpdate,
            PrinterUpdate,
            NetworkDeviceUpdate,
            PhoneUpdate,
            PeripheralUpdate,
            ConsumableUpdate,
            RackUpdate,
            CableUpdate,
            SimCardItemUpdate,
        ],
    ) -> Asset:
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

    # Analytics operations
    def get_asset_count_by_type(self):
        """Get count of assets grouped by type."""
        logger.info(
            f"User {self.current_user.id} attempts to GET asset counts by type at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied access to asset analytics"
            )
            raise PermissionError("Not allowed to access asset analytics.")
        counts = asset_crud.get_asset_count_by_type(self.db)
        logger.info(
            f"User {self.current_user.id} successfully GOT asset counts by type"
        )
        return counts

    def get_asset_count_by_status(self):
        """Get count of assets grouped by status."""
        logger.info(
            f"User {self.current_user.id} attempts to GET asset counts by status at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied access to asset analytics"
            )
            raise PermissionError("Not allowed to access asset analytics.")
        counts = asset_crud.get_asset_count_by_status(self.db)
        logger.info(
            f"User {self.current_user.id} successfully GOT asset counts by status"
        )
        return counts

    def get_asset_count_by_location(self):
        """Get count of assets grouped by location."""
        logger.info(
            f"User {self.current_user.id} attempts to GET asset counts by location at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied access to asset analytics"
            )
            raise PermissionError("Not allowed to access asset analytics.")
        counts = asset_crud.get_asset_count_by_location(self.db)
        logger.info(
            f"User {self.current_user.id} successfully GOT asset counts by location"
        )
        return counts

    # Bulk operations
    def bulk_create_assets(
        self,
        assets_in: List[
            Union[
                AssetCreate,
                ComputerCreate,
                PrinterCreate,
                NetworkDeviceCreate,
                PhoneCreate,
                PeripheralCreate,
                ConsumableCreate,
                RackCreate,
                CableCreate,
                SimCardItemCreate,
            ]
        ],
    ):
        """Bulk create multiple assets."""
        logger.info(
            f"User {self.current_user.id} attempts to BULK CREATE {len(assets_in)} assets at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "create", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied BULK CREATE access for assets"
            )
            raise PermissionError("Not allowed to create assets.")
        try:
            assets = asset_crud.bulk_create_assets(self.db, assets_in)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(
            f"User {self.current_user.id} successfully BULK CREATED {len(assets)} assets"
        )
        return assets
