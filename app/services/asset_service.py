from datetime import datetime, timezone
from typing import List, Optional, Tuple, Union

from sqlalchemy.orm import Session, joinedload

from app.core.logger import logger
from app.core.security import access_filters, can_access, has_permission
from app.db.crud import asset as asset_crud
from app.db.models.asset import Asset
from app.db.models.user import User
from app.schemas.asset import (ComputerCreate, ComputerUpdate,
                               NetworkDeviceCreate, NetworkDeviceUpdate,
                               SoftwareCreate, SoftwareUpdate,
                               SoftwareVersionCreate, VirtualMachineCreate,
                               VirtualMachineUpdate)


class PermissionError(Exception):
    pass


class AssetService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def _get_asset_by_type(self, asset_id: int, asset_type: str) -> Asset:
        """Generic method to get an asset by type with access control."""
        logger.info(
            f"User {self.current_user.id} attempts to READ {asset_type} {asset_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", asset_type):
            logger.warning(
                f"User {self.current_user.id} denied READ access to {asset_type} {asset_id}"
            )
            raise PermissionError(f"Not allowed to read {asset_type}s.")

        asset = asset_crud.get_asset_by_type(self.db, asset_id, asset_type)

        if not can_access(self.current_user, asset):
            logger.warning(
                f"User {self.current_user.id} denied access to {asset_type} {asset_id} due to access control"
            )
            raise PermissionError(f"Not allowed to access this {asset_type}.")

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
    ) -> Tuple[list, int]:
        """
        Returns assets with pagination, permission control, and access control.
        Only returns assets that the user has read permissions for and can access.
        """
        logger.info(
            f"User {self.current_user.id} attempts to LIST assets with pagination at {datetime.now(timezone.utc).isoformat()}"
        )

        # Define all asset types and their permission names
        asset_types = {
            "computer": "computer",
            "network_device": "network_device",
            "virtual_machine": "virtual_machine",
            "software": "software",
        }

        # Check which asset types the user has read permissions for
        accessible_asset_types = []
        for asset_type, permission_name in asset_types.items():
            if has_permission(self.current_user, "read", permission_name):
                accessible_asset_types.append(asset_type)

        if not accessible_asset_types:
            logger.warning(
                f"User {self.current_user.id} has no read permissions for any asset types"
            )
            raise PermissionError("Not allowed to read any asset types.")

        # Get access filters for the user
        access_conditions = access_filters(self.current_user, Asset)

        # Build query with polymorphic assets
        from sqlalchemy.orm import with_polymorphic

        # Get the asset classes for accessible types
        accessible_asset_classes = []
        for asset_type in accessible_asset_types:
            if asset_type in asset_crud.ASSET_TYPE_MAPPING:
                accessible_asset_classes.append(
                    asset_crud.ASSET_TYPE_MAPPING[asset_type][0]
                )

        if not accessible_asset_classes:
            logger.warning(
                f"User {self.current_user.id} has no accessible asset classes"
            )
            return [], 0

        # Create polymorphic query with only accessible asset types
        AssetPoly = with_polymorphic(Asset, accessible_asset_classes)
        query = self.db.query(AssetPoly).options(
            joinedload(AssetPoly.manufacturer),
            joinedload(AssetPoly.location),
            joinedload(AssetPoly.groups),
            joinedload(AssetPoly.assigned_user),
        )

        # Apply access filters if not super admin
        if access_conditions is not None:
            for condition in access_conditions:
                query = query.filter(condition)

        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(AssetPoly, key) and value is not None and value != "":
                    query = query.filter(getattr(AssetPoly, key) == value)

        # Apply search
        if search:
            search_term = f"%{search}%"
            query = query.filter(AssetPoly.name.ilike(search_term))

        # Get total count
        total = query.count()

        # Apply sorting
        if sort_by and hasattr(AssetPoly, sort_by):
            column = getattr(AssetPoly, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        assets = query.all()

        logger.info(
            f"User {self.current_user.id} successfully LISTED {len(assets)} assets from {len(accessible_asset_types)} accessible types"
        )

        return assets, total

    def _get_paginated_assets_by_type(
        self,
        asset_type: str,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[Asset], int]:
        """Generic method to get paginated assets by type with access control."""
        logger.info(
            f"User {self.current_user.id} attempts to LIST {asset_type}s with pagination at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", asset_type):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to {asset_type}s"
            )
            raise PermissionError(f"Not allowed to list {asset_type}s.")

        if filters is None:
            filters = {}
        filters["type"] = asset_type

        access_conditions = access_filters(self.current_user, Asset)

        if access_conditions is None:
            assets, total = asset_crud.get_paginated_assets(
                self.db, page, per_page, sort_by, sort_order, search, filters
            )
        else:
            from sqlalchemy.orm import with_polymorphic

            AssetPoly = with_polymorphic(Asset, asset_crud.ALL_ASSET_TYPES)

            query = self.db.query(AssetPoly).options(
                joinedload(AssetPoly.manufacturer),
                joinedload(AssetPoly.location),
                joinedload(AssetPoly.groups),
                joinedload(AssetPoly.assigned_user),
            )

            for condition in access_conditions:
                query = query.filter(condition)

            if filters:
                if "warranty_expired" in filters:
                    from datetime import date

                    today = date.today()
                    if filters["warranty_expired"]:
                        query = query.filter(
                            Asset.warranty_expiry.isnot(None),
                            Asset.warranty_expiry < today,
                        )
                    else:
                        query = query.filter(
                            Asset.warranty_expiry.isnot(None),
                            Asset.warranty_expiry >= today,
                        )
                    del filters["warranty_expired"]

                for key, value in filters.items():
                    if hasattr(Asset, key) and value is not None and value != "":
                        query = query.filter(getattr(Asset, key) == value)

            if search:
                search_term = f"%{search}%"
                from sqlalchemy import or_

                query = query.filter(
                    or_(
                        Asset.name.ilike(search_term),
                        Asset.serial_number.ilike(search_term),
                        Asset.inventory_number.ilike(search_term),
                    )
                )

            total = query.count()

            if sort_by and hasattr(Asset, sort_by):
                column = getattr(Asset, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())

            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)

            assets = query.all()

        logger.info(f"User {self.current_user.id} successfully LISTED {asset_type}s")
        return assets, total

    def _create_asset_by_type(self, asset_in, asset_type: str) -> Asset:
        """Generic method to create an asset by type."""
        logger.info(
            f"User {self.current_user.id} attempts to CREATE {asset_type} {asset_in.name} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", asset_type):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for {asset_type} {asset_in.name}"
            )
            raise PermissionError(f"Not allowed to create {asset_type}s.")
        try:
            asset = asset_crud.create_asset(self.db, asset_in)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(
            f"User {self.current_user.id} successfully CREATED {asset_type} {asset.id}"
        )
        return asset

    def _update_asset_by_type(self, asset: Asset, asset_in, asset_type: str) -> Asset:
        """Generic method to update an asset by type."""
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE {asset_type} {asset.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", asset_type):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for {asset_type} {asset.id}"
            )
            raise PermissionError(f"Not allowed to update {asset_type}s.")

        if not can_access(self.current_user, asset):
            logger.warning(
                f"User {self.current_user.id} denied access to {asset_type} {asset.id} due to access control"
            )
            raise PermissionError(f"Not allowed to access this {asset_type}.")

        updated_asset = asset_crud.update_asset(self.db, asset, asset_in)
        logger.info(
            f"User {self.current_user.id} successfully UPDATED {asset_type} {asset.id}"
        )
        return updated_asset

    def _delete_asset_by_type(self, asset: Asset, asset_type: str) -> None:
        """Generic method to delete an asset by type."""
        logger.info(
            f"User {self.current_user.id} attempts to DELETE {asset_type} {asset.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", asset_type):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for {asset_type} {asset.id}"
            )
            raise PermissionError(f"Not allowed to delete {asset_type}s.")

        if not can_access(self.current_user, asset):
            logger.warning(
                f"User {self.current_user.id} denied access to {asset_type} {asset.id} due to access control"
            )
            raise PermissionError(f"Not allowed to access this {asset_type}.")

        asset_crud.delete_asset(self.db, asset)
        logger.info(
            f"User {self.current_user.id} successfully DELETED {asset_type} {asset.id}"
        )

    # Computer methods
    def get_computer(self, computer_id: int) -> Asset:
        return self._get_asset_by_type(computer_id, "computer")

    def get_paginated_computers(self, **kwargs) -> Tuple[List[Asset], int]:
        return self._get_paginated_assets_by_type("computer", **kwargs)

    def create_computer(self, computer_in: ComputerCreate) -> Asset:
        return self._create_asset_by_type(computer_in, "computer")

    def update_computer(self, computer: Asset, computer_in: ComputerUpdate) -> Asset:
        return self._update_asset_by_type(computer, computer_in, "computer")

    def delete_computer(self, computer: Asset) -> None:
        return self._delete_asset_by_type(computer, "computer")

    # Network Device methods
    def get_network_device(self, network_device_id: int) -> Asset:
        return self._get_asset_by_type(network_device_id, "network_device")

    def get_paginated_network_devices(self, **kwargs) -> Tuple[List[Asset], int]:
        return self._get_paginated_assets_by_type("network_device", **kwargs)

    def create_network_device(self, network_device_in: NetworkDeviceCreate) -> Asset:
        return self._create_asset_by_type(network_device_in, "network_device")

    def update_network_device(
        self, network_device: Asset, network_device_in: NetworkDeviceUpdate
    ) -> Asset:
        return self._update_asset_by_type(
            network_device, network_device_in, "network_device"
        )

    def delete_network_device(self, network_device: Asset) -> None:
        return self._delete_asset_by_type(network_device, "network_device")

    # VirtualMachine methods
    def get_virtual_machine(self, virtual_machine_id: int) -> Asset:
        return self._get_asset_by_type(virtual_machine_id, "virtual_machine")

    def get_paginated_virtual_machines(self, **kwargs) -> Tuple[List[Asset], int]:
        return self._get_paginated_assets_by_type("virtual_machine", **kwargs)

    def create_virtual_machine(self, virtual_machine_in: VirtualMachineCreate) -> Asset:
        return self._create_asset_by_type(virtual_machine_in, "virtual_machine")

    def update_virtual_machine(
        self, virtual_machine: Asset, virtual_machine_in: VirtualMachineUpdate
    ) -> Asset:
        return self._update_asset_by_type(
            virtual_machine, virtual_machine_in, "virtual_machine"
        )

    def delete_virtual_machine(self, virtual_machine: Asset) -> None:
        return self._delete_asset_by_type(virtual_machine, "virtual_machine")

    # Analytics operations
    def get_asset_count_by_type(self):
        """Get count of assets grouped by type."""
        logger.info(
            f"User {self.current_user.id} attempts to GET asset counts by type at {datetime.now(timezone.utc).isoformat()}"
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
            f"User {self.current_user.id} attempts to GET asset counts by status at {datetime.now(timezone.utc).isoformat()}"
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
            f"User {self.current_user.id} attempts to GET asset counts by location at {datetime.now(timezone.utc).isoformat()}"
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
                ComputerCreate,
                NetworkDeviceCreate,
                VirtualMachineCreate,
            ]
        ],
    ):
        """Bulk create multiple assets."""
        logger.info(
            f"User {self.current_user.id} attempts to BULK CREATE {len(assets_in)} assets at {datetime.now(timezone.utc).isoformat()}"
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

    # Software methods
    def get_software(self, software_id: int):
        """Get a software by ID with access control."""
        logger.info(
            f"User {self.current_user.id} attempts to READ software {software_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "software"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to software {software_id}"
            )
            raise PermissionError("Not allowed to read software.")

        # Import here to avoid circular imports
        from app.db.crud import software as software_crud

        software = software_crud.get_software(self.db, software_id)

        if not software:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software not found")

        logger.info(
            f"User {self.current_user.id} successfully READ software {software_id}"
        )
        return software

    def get_paginated_software(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List, int]:
        """Get paginated software with access control."""
        logger.info(
            f"User {self.current_user.id} attempts to LIST software with pagination at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "software"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to software"
            )
            raise PermissionError("Not allowed to list software.")

        # Import here to avoid circular imports
        from app.db.crud import software as software_crud

        software_list, total = software_crud.get_paginated_software(
            self.db, page, per_page, sort_by, sort_order, search, filters
        )

        logger.info(
            f"User {self.current_user.id} successfully LISTED {len(software_list)} software items"
        )
        return software_list, total

    def create_software(self, software_in: SoftwareCreate):
        return self._create_asset_by_type(software_in, "software")

    def update_software(self, software: Asset, software_in: SoftwareUpdate):
        return self._update_asset_by_type(software, software_in, "software")

    def delete_software(self, software: Asset):
        return self._delete_asset_by_type(software, "software")

    # Software Version methods
    def create_software_version(self, version_in: SoftwareVersionCreate):
        """Create a new software version."""
        logger.info(
            f"User {self.current_user.id} attempts to CREATE software version {version_in.version} for software {version_in.software_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "software"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for software version"
            )
            raise PermissionError("Not allowed to create software versions.")

        # Import here to avoid circular imports
        from app.db.crud import software as software_crud

        try:
            version = software_crud.create_software_version(self.db, version_in)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))

        logger.info(
            f"User {self.current_user.id} successfully CREATED software version {version.id}"
        )
        return version

    def delete_software_version(self, version_id: int):
        """Delete a software version."""
        logger.info(
            f"User {self.current_user.id} attempts to DELETE software version {version_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "software"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for software version {version_id}"
            )
            raise PermissionError("Not allowed to delete software versions.")

        # Import here to avoid circular imports
        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        software_crud.delete_software_version(self.db, version)
        logger.info(
            f"User {self.current_user.id} successfully DELETED software version {version_id}"
        )
