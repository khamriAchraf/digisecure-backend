from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import location as location_crud
from app.db.crud import manufacturer as manufacturer_crud
from app.db.crud import operating_system as operating_system_crud
from app.db.models.location import Location
from app.db.models.manufacturer import Manufacturer
from app.db.models.operating_system import OperatingSystem
from app.db.models.user import User
from app.schemas.location import LocationCreate, LocationUpdate
from app.schemas.manufacturer import ManufacturerCreate, ManufacturerUpdate
from app.schemas.operating_system import (OperatingSystemCreate,
                                          OperatingSystemUpdate)


class PermissionError(Exception):
    pass


class ReferenceDataService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    # Location methods
    def get_location(self, location_id: int) -> Location:
        logger.info(
            f"User {self.current_user.id} attempts to READ reference_data(location) {location_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "location"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to reference_data(location) {location_id}"
            )
            raise PermissionError("Not allowed to read reference_data(location).")
        location = location_crud.get_location(self.db, location_id)
        logger.info(
            f"User {self.current_user.id} successfully READ reference_data(location) {location_id}"
        )
        return location

    def list_locations(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST reference_data(location) at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "location"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to reference_data(location)"
            )
            raise PermissionError("Not allowed to list reference_data(location).")
        locations = location_crud.list_locations(self.db, skip=skip, limit=limit)
        logger.info(
            f"User {self.current_user.id} successfully LISTED reference_data(location)"
        )
        return locations

    def get_paginated_locations(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[Location], int]:
        logger.info(
            f"User {self.current_user.id} attempts to LIST reference_data(location) at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "location"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to reference_data(location)"
            )
            raise PermissionError("Not allowed to list reference_data(location).")
        items, total = location_crud.get_paginated_locations(
            self.db, page, per_page, sort_by, sort_order, search, filters
        )
        logger.info(
            f"User {self.current_user.id} successfully LISTED reference_data(location)"
        )
        return items, total

    def create_location(self, location_in: LocationCreate) -> Location:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE reference_data(location) {location_in.name} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "location"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for reference_data(location) {location_in.name}"
            )
            raise PermissionError("Not allowed to create reference_data(location).")
        try:
            location = location_crud.create_location(self.db, location_in)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(
            f"User {self.current_user.id} successfully CREATED reference_data(location) {location.id}"
        )
        return location

    def update_location(
        self, location: Location, location_in: LocationUpdate
    ) -> Location:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE reference_data(location) {location.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "location"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for reference_data(location) {location.id}"
            )
            raise PermissionError("Not allowed to update reference_data(location).")
        updated_location = location_crud.update_location(self.db, location, location_in)
        logger.info(
            f"User {self.current_user.id} successfully UPDATED reference_data(location) {location.id}"
        )
        return updated_location

    def delete_location(self, location: Location) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE location {location.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "location"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for reference_data(location) {location.id}"
            )
            raise PermissionError("Not allowed to delete reference_data(location).")
        location_crud.delete_location(self.db, location)
        logger.info(
            f"User {self.current_user.id} successfully DELETED reference_data(location) {location.id}"
        )

    # Manufacturer methods
    def get_manufacturer(self, manufacturer_id: int) -> Manufacturer:
        logger.info(
            f"User {self.current_user.id} attempts to READ reference_data(manufacturer) {manufacturer_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "manufacturer"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to reference_data(manufacturer) {manufacturer_id}"
            )
            raise PermissionError("Not allowed to read reference_data(manufacturer).")
        manufacturer = manufacturer_crud.get_manufacturer(self.db, manufacturer_id)
        logger.info(
            f"User {self.current_user.id} successfully READ reference_data(manufacturer) {manufacturer_id}"
        )
        return manufacturer

    def list_manufacturers(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST reference_data(manufacturer) at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "manufacturer"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to reference_data(manufacturer)"
            )
            raise PermissionError("Not allowed to list reference_data(manufacturer).")
        manufacturers = manufacturer_crud.list_manufacturers(
            self.db, skip=skip, limit=limit
        )
        logger.info(
            f"User {self.current_user.id} successfully LISTED reference_data(manufacturer)"
        )
        return manufacturers

    def get_paginated_manufacturers(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[Manufacturer], int]:
        logger.info(
            f"User {self.current_user.id} attempts to LIST reference_data(manufacturer) at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "manufacturer"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to reference_data(manufacturer)"
            )
            raise PermissionError("Not allowed to list reference_data(manufacturer).")
        items, total = manufacturer_crud.get_paginated_manufacturers(
            self.db, page, per_page, sort_by, sort_order, search, filters
        )
        logger.info(
            f"User {self.current_user.id} successfully LISTED reference_data(manufacturer)"
        )
        return items, total

    def create_manufacturer(self, manufacturer_in: ManufacturerCreate) -> Manufacturer:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE reference_data(manufacturer) {manufacturer_in.name} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "manufacturer"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for reference_data(manufacturer) {manufacturer_in.name}"
            )
            raise PermissionError("Not allowed to create reference_data(manufacturer).")
        try:
            manufacturer = manufacturer_crud.create_manufacturer(
                self.db, manufacturer_in
            )
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(
            f"User {self.current_user.id} successfully CREATED reference_data(manufacturer) {manufacturer.id}"
        )
        return manufacturer

    def update_manufacturer(
        self, manufacturer: Manufacturer, manufacturer_in: ManufacturerUpdate
    ) -> Manufacturer:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE reference_data(manufacturer) {manufacturer.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "manufacturer"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for reference_data(manufacturer) {manufacturer.id}"
            )
            raise PermissionError("Not allowed to update reference_data(manufacturer).")
        updated_manufacturer = manufacturer_crud.update_manufacturer(
            self.db, manufacturer, manufacturer_in
        )
        logger.info(
            f"User {self.current_user.id} successfully UPDATED reference_data(manufacturer) {manufacturer.id}"
        )
        return updated_manufacturer

    def delete_manufacturer(self, manufacturer: Manufacturer) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE manufacturer {manufacturer.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "manufacturer"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for reference_data(manufacturer) {manufacturer.id}"
            )
            raise PermissionError("Not allowed to delete reference_data(manufacturer).")
        manufacturer_crud.delete_manufacturer(self.db, manufacturer)
        logger.info(
            f"User {self.current_user.id} successfully DELETED reference_data(manufacturer) {manufacturer.id}"
        )

    # Operating System methods
    def get_operating_system(self, operating_system_id: int) -> OperatingSystem:
        logger.info(
            f"User {self.current_user.id} attempts to READ reference_data(operating_system) {operating_system_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "operating_system"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to reference_data(operating_system) {operating_system_id}"
            )
            raise PermissionError(
                "Not allowed to read reference_data(operating_system)."
            )
        operating_system = operating_system_crud.get_operating_system(
            self.db, operating_system_id
        )
        logger.info(
            f"User {self.current_user.id} successfully READ reference_data(operating_system) {operating_system_id}"
        )
        return operating_system

    def list_operating_systems(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST reference_data(operating_system) at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "operating_system"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to reference_data(operating_system)"
            )
            raise PermissionError(
                "Not allowed to list reference_data(operating_system)."
            )
        operating_systems = operating_system_crud.list_operating_systems(
            self.db, skip=skip, limit=limit
        )
        logger.info(
            f"User {self.current_user.id} successfully LISTED reference_data(operating_system)"
        )
        return operating_systems

    def get_paginated_operating_systems(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[OperatingSystem], int]:
        logger.info(
            f"User {self.current_user.id} attempts to LIST reference_data(operating_system) at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "operating_system"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to reference_data(operating_system)"
            )
            raise PermissionError(
                "Not allowed to list reference_data(operating_system)."
            )
        items, total = operating_system_crud.get_paginated_operating_systems(
            self.db, page, per_page, sort_by, sort_order, search, filters
        )
        logger.info(
            f"User {self.current_user.id} successfully LISTED reference_data(operating_system)"
        )
        return items, total

    def create_operating_system(
        self, operating_system_in: OperatingSystemCreate
    ) -> OperatingSystem:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE reference_data(operating_system) {operating_system_in.name} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "operating_system"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for reference_data(operating_system) {operating_system_in.name}"
            )
            raise PermissionError(
                "Not allowed to create reference_data(operating_system)."
            )
        try:
            operating_system = operating_system_crud.create_operating_system(
                self.db, operating_system_in
            )
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(
            f"User {self.current_user.id} successfully CREATED reference_data(operating_system) {operating_system.id}"
        )
        return operating_system

    def update_operating_system(
        self,
        operating_system: OperatingSystem,
        operating_system_in: OperatingSystemUpdate,
    ) -> OperatingSystem:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE reference_data(operating_system) {operating_system.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "operating_system"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for reference_data(operating_system) {operating_system.id}"
            )
            raise PermissionError(
                "Not allowed to update reference_data(operating_system)."
            )
        updated_operating_system = operating_system_crud.update_operating_system(
            self.db, operating_system, operating_system_in
        )
        logger.info(
            f"User {self.current_user.id} successfully UPDATED reference_data(operating_system) {operating_system.id}"
        )
        return updated_operating_system

    def delete_operating_system(self, operating_system: OperatingSystem) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE operating_system {operating_system.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "operating_system"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for reference_data(operating_system) {operating_system.id}"
            )
            raise PermissionError(
                "Not allowed to delete reference_data(operating_system)."
            )
        operating_system_crud.delete_operating_system(self.db, operating_system)
        logger.info(
            f"User {self.current_user.id} successfully DELETED reference_data(operating_system) {operating_system.id}"
        )
