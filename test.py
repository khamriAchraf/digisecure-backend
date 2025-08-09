def create_software(self, software_in: SoftwareCreate):
        """Create a new software."""
        logger.info(
            f"User {self.current_user.id} attempts to CREATE software {software_in.name} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "software"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for software {software_in.name}"
            )
            raise PermissionError("Not allowed to create software.")

        from app.db.crud import software as software_crud

        try:
            software = software_crud.create_software(self.db, software_in)
        except ValueError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=409, detail=str(e))

        logger.info(
            f"User {self.current_user.id} successfully CREATED software {software.id}"
        )
        return software

