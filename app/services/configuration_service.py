from datetime import datetime

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import asset_type as asset_type_crud
from app.db.crud import location as location_crud
from app.db.crud import manufacturer as manufacturer_crud
from app.db.models.asset_type import AssetType
from app.db.models.location import Location
from app.db.models.manufacturer import Manufacturer
from app.db.models.user import User
from app.schemas.asset_type import AssetTypeCreate, AssetTypeUpdate
from app.schemas.location import LocationCreate, LocationUpdate
from app.schemas.manufacturer import ManufacturerCreate, ManufacturerUpdate


class PermissionError(Exception):
    pass


class ConfigurationService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    # Location methods
    def get_location(self, location_id: int) -> Location:
        logger.info(
            f"User {self.current_user.id} attempts to READ configuration(location) {location_id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to configuration(location) {location_id}"
            )
            raise PermissionError("Not allowed to read configuration(location).")
        location = location_crud.get_location(self.db, location_id)
        logger.info(
            f"User {self.current_user.id} successfully READ configuration(location) {location_id}"
        )
        return location

    def list_locations(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST configuration(location) at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to configuration(location)"
            )
            raise PermissionError("Not allowed to list configuration(location).")
        locations = location_crud.list_locations(self.db, skip=skip, limit=limit)
        logger.info(
            f"User {self.current_user.id} successfully LISTED configuration(location)"
        )
        return locations

    def create_location(self, location_in: LocationCreate) -> Location:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE configuration(location) {location_in.name} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "create", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for configuration(location) {location_in.name}"
            )
            raise PermissionError("Not allowed to create configuration(location).")
        try:
            location = location_crud.create_location(self.db, location_in)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(
            f"User {self.current_user.id} successfully CREATED configuration(location) {location.id}"
        )
        return location

    def update_location(
        self, location: Location, location_in: LocationUpdate
    ) -> Location:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE configuration(location) {location.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "update", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for configuration(location) {location.id}"
            )
            raise PermissionError("Not allowed to update configuration(location).")
        updated_location = location_crud.update_location(self.db, location, location_in)
        logger.info(
            f"User {self.current_user.id} successfully UPDATED configuration(location) {location.id}"
        )
        return updated_location

    def delete_location(self, location: Location) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE location {location.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for configuration(location) {location.id}"
            )
            raise PermissionError("Not allowed to delete configuration(location).")
        location_crud.delete_location(self.db, location)
        logger.info(
            f"User {self.current_user.id} successfully DELETED configuration(location) {location.id}"
        )

    # Manufacturer methods
    def get_manufacturer(self, manufacturer_id: int) -> Manufacturer:
        logger.info(
            f"User {self.current_user.id} attempts to READ configuration(manufacturer) {manufacturer_id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to configuration(manufacturer) {manufacturer_id}"
            )
            raise PermissionError("Not allowed to read configuration(manufacturer).")
        manufacturer = manufacturer_crud.get_manufacturer(self.db, manufacturer_id)
        logger.info(
            f"User {self.current_user.id} successfully READ configuration(manufacturer) {manufacturer_id}"
        )
        return manufacturer

    def list_manufacturers(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST configuration(manufacturer) at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to configuration(manufacturer)"
            )
            raise PermissionError("Not allowed to list configuration(manufacturer).")
        manufacturers = manufacturer_crud.list_manufacturers(
            self.db, skip=skip, limit=limit
        )
        logger.info(
            f"User {self.current_user.id} successfully LISTED configuration(manufacturer)"
        )
        return manufacturers

    def create_manufacturer(self, manufacturer_in: ManufacturerCreate) -> Manufacturer:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE configuration(manufacturer) {manufacturer_in.name} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "create", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for configuration(manufacturer) {manufacturer_in.name}"
            )
            raise PermissionError("Not allowed to create configuration(manufacturer).")
        try:
            manufacturer = manufacturer_crud.create_manufacturer(
                self.db, manufacturer_in
            )
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(
            f"User {self.current_user.id} successfully CREATED configuration(manufacturer) {manufacturer.id}"
        )
        return manufacturer

    def update_manufacturer(
        self, manufacturer: Manufacturer, manufacturer_in: ManufacturerUpdate
    ) -> Manufacturer:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE configuration(manufacturer) {manufacturer.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "update", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for configuration(manufacturer) {manufacturer.id}"
            )
            raise PermissionError("Not allowed to update configuration(manufacturer).")
        updated_manufacturer = manufacturer_crud.update_manufacturer(
            self.db, manufacturer, manufacturer_in
        )
        logger.info(
            f"User {self.current_user.id} successfully UPDATED configuration(manufacturer) {manufacturer.id}"
        )
        return updated_manufacturer

    def delete_manufacturer(self, manufacturer: Manufacturer) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE manufacturer {manufacturer.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for configuration(manufacturer) {manufacturer.id}"
            )
            raise PermissionError("Not allowed to delete configuration(manufacturer).")
        manufacturer_crud.delete_manufacturer(self.db, manufacturer)
        logger.info(
            f"User {self.current_user.id} successfully DELETED configuration(manufacturer) {manufacturer.id}"
        )

    # Asset type methods
    def get_asset_type(self, asset_type_id: int) -> AssetType:
        logger.info(
            f"User {self.current_user.id} attempts to READ configuration(asset_type) {asset_type_id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to configuration(asset_type) {asset_type_id}"
            )
            raise PermissionError("Not allowed to read configuration(asset_type).")
        asset_type = asset_type_crud.get_asset_type(self.db, asset_type_id)
        logger.info(
            f"User {self.current_user.id} successfully READ configuration(asset_type) {asset_type_id}"
        )
        return asset_type

    def list_asset_types(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST configuration(asset_type) at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to configuration(asset_type)"
            )
            raise PermissionError("Not allowed to list configuration(asset_type).")
        asset_types = asset_type_crud.list_asset_types(self.db, skip=skip, limit=limit)
        logger.info(
            f"User {self.current_user.id} successfully LISTED configuration(asset_type)"
        )
        return asset_types

    def create_asset_type(self, asset_type_in: AssetTypeCreate) -> AssetType:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE configuration(asset_type) {asset_type_in.name} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "create", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for configuration(asset_type) {asset_type_in.name}"
            )
            raise PermissionError("Not allowed to create configuration(asset_type).")
        try:
            asset_type = asset_type_crud.create_asset_type(self.db, asset_type_in)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(
            f"User {self.current_user.id} successfully CREATED configuration(asset_type) {asset_type.id}"
        )
        return asset_type

    def update_asset_type(
        self, asset_type: AssetType, asset_type_in: AssetTypeUpdate
    ) -> AssetType:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE configuration(asset_type) {asset_type.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "update", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for configuration(asset_type) {asset_type.id}"
            )
            raise PermissionError("Not allowed to update configuration(asset_type).")
        updated_asset_type = asset_type_crud.update_asset_type(
            self.db, asset_type, asset_type_in
        )
        logger.info(
            f"User {self.current_user.id} successfully UPDATED configuration(asset_type) {asset_type.id}"
        )
        return updated_asset_type

    def delete_asset_type(self, asset_type: AssetType) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE asset_type {asset_type.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "configuration"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for configuration(asset_type) {asset_type.id}"
            )
            raise PermissionError("Not allowed to delete configuration(asset_type).")
        asset_type_crud.delete_asset_type(self.db, asset_type)
        logger.info(
            f"User {self.current_user.id} successfully DELETED configuration(asset_type) {asset_type.id}"
        )
