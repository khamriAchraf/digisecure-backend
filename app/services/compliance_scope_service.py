from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import asset as asset_crud
from app.db.crud import compliance_scope as compliance_crud
from app.db.models.compliance_scopes import ComplianceScope as ComplianceScopeModel
from app.db.models.user import User
from app.schemas.compliance_scope import (
    AssetComplianceScopeCreate,
    AssetComplianceScopeUpdate,
    ComplianceScopeCreate,
    ComplianceScopeUpdate,
)


class PermissionError(Exception):
    pass


class ComplianceScopeService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    # Scopes
    def get_scope(self, scope_id: int) -> ComplianceScopeModel:
        logger.info(
            f"User {self.current_user.id} attempts to READ compliance scope {scope_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "compliance_scope"):
            logger.warning(
                f"User {self.current_user.id} denied READ access to compliance scope {scope_id}"
            )
            raise PermissionError("Not allowed to read compliance scopes.")
        scope = compliance_crud.get_scope(self.db, scope_id)
        return scope

    def list_scopes(self, skip: int = 0, limit: int = 100):
        logger.info(
            f"User {self.current_user.id} attempts to LIST compliance scopes at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "compliance_scope"):
            logger.warning(
                f"User {self.current_user.id} denied LIST access to compliance scopes"
            )
            raise PermissionError("Not allowed to list compliance scopes.")
        return compliance_crud.list_scopes(self.db, skip=skip, limit=limit)

    def create_scope(self, scope_in: ComplianceScopeCreate):
        logger.info(
            f"User {self.current_user.id} attempts to CREATE compliance scope {scope_in.name} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "compliance_scope"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access for compliance scope {scope_in.name}"
            )
            raise PermissionError("Not allowed to create compliance scopes.")
        return compliance_crud.create_scope(self.db, scope_in)

    def update_scope(self, scope: ComplianceScopeModel, scope_in: ComplianceScopeUpdate):
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE compliance scope {scope.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "compliance_scope"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE access for compliance scope {scope.id}"
            )
            raise PermissionError("Not allowed to update compliance scopes.")
        return compliance_crud.update_scope(self.db, scope, scope_in)

    def delete_scope(self, scope: ComplianceScopeModel) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE compliance scope {scope.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "compliance_scope"):
            logger.warning(
                f"User {self.current_user.id} denied DELETE access for compliance scope {scope.id}"
            )
            raise PermissionError("Not allowed to delete compliance scopes.")
        try:
            compliance_crud.delete_scope(self.db, scope)
        except IntegrityError:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=409,
                detail="Compliance scope is in use and cannot be deleted",
            )

    # Asset tagging
    def tag_asset_with_scope(self, mapping_in: AssetComplianceScopeCreate):
        logger.info(
            f"User {self.current_user.id} attempts to TAG asset {mapping_in.asset_id} with scope {mapping_in.scope_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "compliance_manage", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied TAG access for asset {mapping_in.asset_id}"
            )
            raise PermissionError("Not allowed to tag assets.")
        asset = asset_crud.get_asset(self.db, mapping_in.asset_id)
        if asset is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Asset not found")
        scope = compliance_crud.get_scope(self.db, mapping_in.scope_id)
        if scope is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Compliance scope not found")
        existing = compliance_crud.get_asset_scope(
            self.db, mapping_in.asset_id, mapping_in.scope_id
        )
        if existing:
            return existing
        return compliance_crud.create_asset_scope(self.db, mapping_in)

    def update_asset_scope(self, asset_id: int, scope_id: int, mapping_in: AssetComplianceScopeUpdate):
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE asset {asset_id} scope {scope_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "compliance_manage", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied UPDATE asset scope for asset {asset_id}"
            )
            raise PermissionError("Not allowed to update asset scopes.")
        mapping = compliance_crud.get_asset_scope(self.db, asset_id, scope_id)
        if mapping is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Mapping not found")
        return compliance_crud.update_asset_scope(self.db, mapping, mapping_in)

    def untag_asset_scope(self, asset_id: int, scope_id: int):
        logger.info(
            f"User {self.current_user.id} attempts to UNTAG asset {asset_id} scope {scope_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "compliance_manage", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied UNTAG access for asset {asset_id}"
            )
            raise PermissionError("Not allowed to untag assets.")
        mapping = compliance_crud.get_asset_scope(self.db, asset_id, scope_id)
        if mapping is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Mapping not found")
        compliance_crud.delete_asset_scope(self.db, mapping)

    def replace_asset_scopes(self, asset_id: int, scope_ids: List[int]):
        logger.info(
            f"User {self.current_user.id} attempts to REPLACE scopes for asset {asset_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "compliance_manage", "asset"):
            logger.warning(
                f"User {self.current_user.id} denied REPLACE scopes for asset {asset_id}"
            )
            raise PermissionError("Not allowed to update asset scopes.")
        asset = asset_crud.get_asset(self.db, asset_id)
        if asset is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Asset not found")

        # Validate scopes
        valid_scopes = self.db.query(ComplianceScopeModel.id).filter(
            ComplianceScopeModel.id.in_(scope_ids)
        ).all()
        valid_ids = {sid for (sid,) in valid_scopes}
        if len(valid_ids) != len(set(scope_ids)):
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail="One or more scopes are invalid")

        from app.db.models.compliance_scopes import AssetComplianceScope as Mapping

        self.db.query(Mapping).filter(Mapping.asset_id == asset_id).delete()
        for sid in scope_ids:
            self.db.add(Mapping(asset_id=asset_id, scope_id=sid))
        self.db.commit()


