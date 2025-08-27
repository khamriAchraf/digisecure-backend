from datetime import datetime, timezone
from typing import List, Optional, Tuple, Union

from sqlalchemy.orm import Session, joinedload

from app.core.logger import logger
from app.core.security import access_filters, can_access, has_permission
from app.db.crud import asset as asset_crud
from app.db.models.asset import Asset, Computer, NetworkDevice, VirtualMachine
from app.db.models.document_store import Document as DocumentModel
from app.db.models.user import User
from app.schemas.asset import (CertificateKeyCreate, CertificateKeyList,
                               CertificateKeyUpdate, ComputerCreate,
                               ComputerList, ComputerUpdate,
                               NetworkDeviceCreate, NetworkDeviceUpdate,
                               SoftwareCreate, SoftwareUpdate,
                               SoftwareVersionCreate, SoftwareVersionUpdate,
                               VirtualMachineCreate, VirtualMachineUpdate)


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

        accessible_asset_types = []
        for asset_type, permission_name in asset_types.items():
            if has_permission(self.current_user, "list", permission_name):
                accessible_asset_types.append(asset_type)

        if not accessible_asset_types:
            logger.warning(
                f"User {self.current_user.id} has no list permissions for any asset types"
            )
            raise PermissionError("Not allowed to list any asset types.")

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
        if not has_permission(self.current_user, "list", asset_type):
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

    def get_paginated_computers(self, **kwargs) -> Tuple[List[ComputerList], int]:
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

    # Certificate Key methods
    def get_certificate_key(self, certificate_key_id: int) -> Asset:
        return self._get_asset_by_type(certificate_key_id, "certificate_key")

    def get_paginated_certificate_keys(
        self, **kwargs
    ) -> Tuple[List[CertificateKeyList], int]:
        return self._get_paginated_assets_by_type("certificate_key", **kwargs)

    def create_certificate_key(self, certificate_key_in: CertificateKeyCreate) -> Asset:
        return self._create_asset_by_type(certificate_key_in, "certificate_key")

    def update_certificate_key(
        self, certificate_key: Asset, certificate_key_in: CertificateKeyUpdate
    ) -> Asset:
        return self._update_asset_by_type(
            certificate_key, certificate_key_in, "certificate_key"
        )

    def delete_certificate_key(self, certificate_key: Asset) -> None:
        return self._delete_asset_by_type(certificate_key, "certificate_key")

    # Analytics operations
    def get_asset_count_by_type(self):
        """Get count of assets grouped by type."""
        logger.info(
            f"User {self.current_user.id} attempts to GET asset counts by type at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied access to asset analytics"
            )
            raise PermissionError("Not allowed to access asset analytics.")
        counts = asset_crud.get_asset_count_by_type(self.db)
        logger.info(
            f"User {self.current_user.id} successfully GOT asset counts by type"
        )
        return counts

    def get_paginated_deleted_assets_by_time(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
        asset_type: Optional[str] = None,
    ) -> Tuple[List[Asset], int]:
        """List soft-deleted assets ordered by deletion time.

        Defaults to sorting by deleted_at desc unless sort_by provided.
        Allows optional filtering by asset type via `asset_type` or `filters["type"]`.
        """
        logger.info(
            f"User {self.current_user.id} attempts to LIST deleted {asset_type} at {datetime.now(timezone.utc).isoformat()}"
        )
        # Permission to access recycle bin for assets
        if not has_permission(self.current_user, "list", f"recycle_bin_{asset_type}"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to recycle bin({asset_type})"
            )
            raise PermissionError(f"Not allowed to list recycle bin({asset_type}).")

        effective_filters = dict(filters or {})
        if asset_type:
            effective_filters["type"] = asset_type

        # Default sort to deleted_at DESC if not explicitly set
        effective_sort_by = sort_by or "deleted_at"

        from app.db.crud import asset as asset_crud

        assets, total = asset_crud.get_paginated_deleted_assets(
            self.db,
            page=page,
            per_page=per_page,
            sort_by=effective_sort_by,
            sort_order=sort_order,
            search=search,
            filters=effective_filters,
        )

        logger.info(
            f"User {self.current_user.id} successfully LISTED {len(assets)} deleted {asset_type}"
        )
        return assets, total

    def get_asset_count_by_status(self):
        """Get count of assets grouped by status."""
        logger.info(
            f"User {self.current_user.id} attempts to GET asset counts by status at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "asset"):
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
        if not has_permission(self.current_user, "list", "asset"):
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

    def get_documents_for_software(self, software_id: int):
        """List documents attached to a software."""
        logger.info(
            f"User {self.current_user.id} attempts to READ software {software_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "software"):
            logger.warning(
                f"User {self.current_user.id} denied READ access for software {software_id}"
            )
            raise PermissionError("Not allowed to read software.")

        # Import here to avoid circular imports
        from app.db.crud import software as software_crud

        software = software_crud.get_software(self.db, software_id)
        if not software:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software not found")

        # Accessing relationship will load attached documents
        documents: list[DocumentModel] = list(software.documents or [])
        logger.info(
            f"User {self.current_user.id} successfully LISTED {len(documents)} documents for software {software_id}"
        )
        return documents

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
        if not has_permission(self.current_user, "list", "software"):
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

    def update_software_version(
        self, version_id: int, version_in: SoftwareVersionUpdate
    ):
        """Update fields of a software version."""
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE software version {version_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "software"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for software version {version_id}"
            )
            raise PermissionError("Not allowed to update software versions.")

        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        # Use asset CRUD for update logic including uniqueness enforcement
        from app.db.crud import asset as asset_crud

        try:
            updated = asset_crud.update_software_version_fields(
                self.db, version, version_in
            )
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))

        logger.info(
            f"User {self.current_user.id} successfully UPDATED software version {version_id}"
        )
        return updated

    def soft_delete_software_version(self, version_id: int) -> None:
        """Soft delete a software version."""
        logger.info(
            f"User {self.current_user.id} attempts to SOFT DELETE software version {version_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "software"):
            logger.warning(
                f"User {self.current_user.id} denied SOFT DELETE access for software version {version_id}"
            )
            raise PermissionError("Not allowed to delete software versions.")

        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        from app.db.crud import asset as asset_crud

        asset_crud.soft_delete_software_version(self.db, version)

        logger.info(
            f"User {self.current_user.id} successfully SOFT DELETED software version {version_id}"
        )
        return None

    def attach_software_version_to_computer(self, version_id: int, computer_id: int):
        """Attach a software version to a computer (mark as installed)."""
        logger.info(
            f"User {self.current_user.id} attempts to ATTACH version {version_id} to computer {computer_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "computer"):
            logger.warning(
                f"User {self.current_user.id} denied ATTACH access for version {version_id} to computer {computer_id}"
            )
            raise PermissionError("Not allowed to update computers.")

        # Ensure computer exists and user can access it
        computer: Computer = self.get_computer(computer_id)
        if not can_access(self.current_user, computer):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for computer {computer_id}"
            )
            raise PermissionError("Not allowed to update this computer.")

        # Fetch version
        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        if version not in computer.software_versions:
            computer.software_versions.append(version)
            self.db.add(computer)
            self.db.commit()
            self.db.refresh(computer)

        logger.info(
            f"User {self.current_user.id} successfully ATTACHED version {version_id} to computer {computer_id}"
        )
        return computer

    def detach_software_version_from_computer(
        self, version_id: int, computer_id: int
    ) -> None:
        """Detach a software version from a computer (mark as uninstalled)."""
        logger.info(
            f"User {self.current_user.id} attempts to DETACH version {version_id} from computer {computer_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "computer"):
            logger.warning(
                f"User {self.current_user.id} denied DETACH access for version {version_id} from computer {computer_id}"
            )
            raise PermissionError("Not allowed to update computers.")

        computer: Computer = self.get_computer(computer_id)
        if not can_access(self.current_user, computer):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for computer {computer_id}"
            )
            raise PermissionError("Not allowed to update this computer.")

        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        if version in computer.software_versions:
            computer.software_versions.remove(version)
            self.db.add(computer)
            self.db.commit()
            self.db.refresh(computer)

        logger.info(
            f"User {self.current_user.id} successfully DETACHED version {version_id} from computer {computer_id}"
        )
        return None

    def list_computers_for_software_version(self, version_id: int) -> List[Computer]:
        """List computers that have the given software version, filtered by access and update permission."""
        logger.info(
            f"User {self.current_user.id} attempts to LIST computers for version {version_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "computer"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to computers for version {version_id}"
            )
            raise PermissionError("Not allowed to update computers.")

        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        computers: List[Computer] = [
            computer
            for computer in (version.computers or [])
            if can_access(self.current_user, computer)
        ]

        logger.info(
            f"User {self.current_user.id} successfully LISTED {len(computers)} computers for version {version_id}"
        )
        return computers

    def attach_software_version_to_virtual_machine(
        self, version_id: int, virtual_machine_id: int
    ):
        """Attach a software version to a virtual machine (mark as installed)."""
        logger.info(
            f"User {self.current_user.id} attempts to ATTACH version {version_id} to virtual machine {virtual_machine_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "virtual_machine"):
            logger.warning(
                f"User {self.current_user.id} denied ATTACH access for version {version_id} to virtual machine {virtual_machine_id}"
            )
            raise PermissionError("Not allowed to update virtual machines.")

        vm: VirtualMachine = self.get_virtual_machine(virtual_machine_id)
        if not can_access(self.current_user, vm):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for virtual machine {virtual_machine_id}"
            )
            raise PermissionError("Not allowed to update this virtual machine.")

        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        if version not in vm.software_versions:
            vm.software_versions.append(version)
            self.db.add(vm)
            self.db.commit()
            self.db.refresh(vm)

        logger.info(
            f"User {self.current_user.id} successfully ATTACHED version {version_id} to virtual machine {virtual_machine_id}"
        )
        return vm

    def detach_software_version_from_virtual_machine(
        self, version_id: int, virtual_machine_id: int
    ) -> None:
        """Detach a software version from a virtual machine (mark as uninstalled)."""
        logger.info(
            f"User {self.current_user.id} attempts to DETACH version {version_id} from virtual machine {virtual_machine_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "virtual_machine"):
            logger.warning(
                f"User {self.current_user.id} denied DETACH access for version {version_id} from virtual machine {virtual_machine_id}"
            )
            raise PermissionError("Not allowed to update virtual machines.")

        vm: VirtualMachine = self.get_virtual_machine(virtual_machine_id)
        if not can_access(self.current_user, vm):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for virtual machine {virtual_machine_id}"
            )
            raise PermissionError("Not allowed to update this virtual machine.")

        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        if version in vm.software_versions:
            vm.software_versions.remove(version)
            self.db.add(vm)
            self.db.commit()
            self.db.refresh(vm)

        logger.info(
            f"User {self.current_user.id} successfully DETACHED version {version_id} from virtual machine {virtual_machine_id}"
        )
        return None

    def list_virtual_machines_for_software_version(
        self, version_id: int
    ) -> List[VirtualMachine]:
        """List virtual machines that have the given software version, filtered by access and update permission."""
        logger.info(
            f"User {self.current_user.id} attempts to LIST virtual machines for version {version_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "virtual_machine"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to virtual machines for version {version_id}"
            )
            raise PermissionError("Not allowed to update virtual machines.")

        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        vms: List[VirtualMachine] = [
            vm
            for vm in (version.virtual_machines or [])
            if can_access(self.current_user, vm)
        ]

        logger.info(
            f"User {self.current_user.id} successfully LISTED {len(vms)} virtual machines for version {version_id}"
        )
        return vms

    def attach_software_version_to_network_device(
        self, version_id: int, network_device_id: int
    ):
        """Attach a software version to a network device (mark as installed)."""
        logger.info(
            f"User {self.current_user.id} attempts to ATTACH version {version_id} to network device {network_device_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "network_device"):
            logger.warning(
                f"User {self.current_user.id} denied ATTACH access for version {version_id} to network device {network_device_id}"
            )
            raise PermissionError("Not allowed to update network devices.")

        nd: NetworkDevice = self.get_network_device(network_device_id)
        if not can_access(self.current_user, nd):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for network device {network_device_id}"
            )
            raise PermissionError("Not allowed to update this network device.")

        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        if version not in nd.software_versions:
            nd.software_versions.append(version)
            self.db.add(nd)
            self.db.commit()
            self.db.refresh(nd)

        logger.info(
            f"User {self.current_user.id} successfully ATTACHED version {version_id} to network device {network_device_id}"
        )
        return nd

    def detach_software_version_from_network_device(
        self, version_id: int, network_device_id: int
    ) -> None:
        """Detach a software version from a network device (mark as uninstalled)."""
        logger.info(
            f"User {self.current_user.id} attempts to DETACH version {version_id} from network device {network_device_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "network_device"):
            logger.warning(
                f"User {self.current_user.id} denied DETACH access for version {version_id} from network device {network_device_id}"
            )
            raise PermissionError("Not allowed to update network devices.")

        nd: NetworkDevice = self.get_network_device(network_device_id)
        if not can_access(self.current_user, nd):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for network device {network_device_id}"
            )
            raise PermissionError("Not allowed to update this network device.")

        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        if version in nd.software_versions:
            nd.software_versions.remove(version)
            self.db.add(nd)
            self.db.commit()
            self.db.refresh(nd)

        logger.info(
            f"User {self.current_user.id} successfully DETACHED version {version_id} from network device {network_device_id}"
        )
        return None

    def list_network_devices_for_software_version(
        self, version_id: int
    ) -> List[NetworkDevice]:
        """List network devices that have the given software version, filtered by access and update permission."""
        logger.info(
            f"User {self.current_user.id} attempts to LIST network devices for version {version_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "network_device"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to network devices for version {version_id}"
            )
            raise PermissionError("Not allowed to update network devices.")

        from app.db.crud import software as software_crud

        version = software_crud.get_software_version(self.db, version_id)
        if not version:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software version not found")

        devices: List[NetworkDevice] = [
            nd
            for nd in (version.network_devices or [])
            if can_access(self.current_user, nd)
        ]

        logger.info(
            f"User {self.current_user.id} successfully LISTED {len(devices)} network devices for version {version_id}"
        )
        return devices

    def attach_document_to_software(self, software_id: int, document_id: int):
        """Attach a document to a software."""
        logger.info(
            f"User {self.current_user.id} attempts to ATTACH document {document_id} to software {software_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "software"):
            logger.warning(
                f"User {self.current_user.id} denied ATTACH access for document {document_id} to software {software_id}"
            )
            raise PermissionError("Not allowed to attach documents to software.")

        software = self.get_software(software_id)
        if not software:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Software not found")

        if not can_access(self.current_user, software):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for software {software_id}"
            )
            raise PermissionError("Not allowed to update this software.")

        from app.db.crud import document_store as document_crud

        document = document_crud.get_document(self.db, document_id)
        if not document:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Document not found")

        if document not in software.documents:
            software.documents.append(document)
            self.db.add(software)
            self.db.commit()
            self.db.refresh(software)

        logger.info(
            f"User {self.current_user.id} successfully ATTACHED document {document_id} to software {software_id}"
        )
        return software

    def detach_document_from_software(self, software_id: int, document_id: int) -> None:
        """Detach a document from a software."""
        logger.info(
            f"User {self.current_user.id} attempts to DETACH document {document_id} from software {software_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "software"):
            logger.warning(
                f"User {self.current_user.id} denied DETACH access for document {document_id} from software {software_id}"
            )
            raise PermissionError("Not allowed to update software.")

        software = self.get_software(software_id)
        if not can_access(self.current_user, software):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for software {software_id}"
            )
            raise PermissionError("Not allowed to update this software.")

        from app.db.crud import document_store as document_crud

        document = document_crud.get_document(self.db, document_id)
        if not document:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Document not found")

        if document in software.documents:
            software.documents.remove(document)
            self.db.add(software)
            self.db.commit()
            self.db.refresh(software)

        logger.info(
            f"User {self.current_user.id} successfully DETACHED document {document_id} from software {software_id}"
        )
        return None
