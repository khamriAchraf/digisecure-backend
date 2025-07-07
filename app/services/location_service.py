from datetime import datetime

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import location as location_crud
from app.db.models.location import Location
from app.db.models.user import User
from app.schemas.location import LocationCreate, LocationUpdate


class PermissionError(Exception):
    pass


class LocationService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def get_location(self, location_id: int) -> Location:
        logger.info(
            f"User {self.current_user.id} attempts to READ location {location_id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "location"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to location {location_id}"
            )
            raise PermissionError("Not allowed to read locations.")
        location = location_crud.get_location(self.db, location_id)
        logger.info(
            f"User {self.current_user.id} successfully READ location {location_id}"
        )
        return location

    def list_locations(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST locations at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "read", "location"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to locations"
            )
            raise PermissionError("Not allowed to list locations.")
        locations = location_crud.list_locations(self.db, skip=skip, limit=limit)
        logger.info(f"User {self.current_user.id} successfully LISTED locations")
        return locations

    def create_location(self, location_in: LocationCreate) -> Location:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE location {location_in.name} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "create", "location"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for location {location_in.name}"
            )
            raise PermissionError("Not allowed to create locations.")
        try:
            location = location_crud.create_location(self.db, location_in)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))
        logger.info(
            f"User {self.current_user.id} successfully CREATED location {location.id}"
        )
        return location

    def update_location(
        self, location: Location, location_in: LocationUpdate
    ) -> Location:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE location {location.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "update", "location"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for location {location.id}"
            )
            raise PermissionError("Not allowed to update locations.")
        updated_location = location_crud.update_location(self.db, location, location_in)
        logger.info(
            f"User {self.current_user.id} successfully UPDATED location {location.id}"
        )
        return updated_location

    def delete_location(self, location: Location) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE location {location.id} at {datetime.utcnow().isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "location"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for location {location.id}"
            )
            raise PermissionError("Not allowed to delete locations.")
        location_crud.delete_location(self.db, location)
        logger.info(
            f"User {self.current_user.id} successfully DELETED location {location.id}"
        )
