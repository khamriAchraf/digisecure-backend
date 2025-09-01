from datetime import datetime, timezone
from typing import List

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import asset as asset_crud
from app.db.crud import compliance_scope as compliance_crud
from app.db.models.compliance_scopes import ComplianceControl
from app.db.models.compliance_scopes import \
    ComplianceScope as ComplianceScopeModel
from app.db.models.compliance_scopes import ControlDocumentLink
from app.db.models.document_store import Document
from app.db.models.user import User
from app.schemas.compliance_scope import (AssetComplianceScopeCreate,
                                          AssetComplianceScopeUpdate)
from app.schemas.compliance_scope import \
    ComplianceControl as ComplianceControlSchema
from app.schemas.compliance_scope import (ComplianceControlListItem,
                                          ComplianceScopeCreate,
                                          ComplianceScopeUpdate,
                                          ControlDocumentLinkCreate,
                                          ControlDocumentLinkDelete,
                                          ScopedAsset)
from app.schemas.pagination import create_paginated_response


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
        if not has_permission(self.current_user, "list", "compliance_scope"):
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

    def update_scope(
        self, scope: ComplianceScopeModel, scope_in: ComplianceScopeUpdate
    ):
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

    def update_asset_scope(
        self, asset_id: int, scope_id: int, mapping_in: AssetComplianceScopeUpdate
    ):
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
        valid_scopes = (
            self.db.query(ComplianceScopeModel.id)
            .filter(ComplianceScopeModel.id.in_(scope_ids))
            .all()
        )
        valid_ids = {sid for (sid,) in valid_scopes}
        if len(valid_ids) != len(set(scope_ids)):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400, detail="One or more scopes are invalid"
            )

        from app.db.models.compliance_scopes import \
            AssetComplianceScope as Mapping

        self.db.query(Mapping).filter(Mapping.asset_id == asset_id).delete()
        for sid in scope_ids:
            self.db.add(Mapping(asset_id=asset_id, scope_id=sid))
        self.db.commit()

    # ----------------------------------------
    # Paginated assets within a given scope
    # ----------------------------------------

    def get_paginated_scope_assets(
        self,
        scope_id: int,
        page: int = 1,
        per_page: int = 20,
        sort_by: str | None = None,
        sort_order: str = "asc",
        search: str | None = None,
        filters: dict | None = None,
    ):
        if not has_permission(self.current_user, "list", "compliance_scope"):
            raise PermissionError("Not allowed to list compliance scopes.")

        rows, total = compliance_crud.get_paginated_scope_assets(
            self.db,
            scope_id=scope_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )

        # Map joined rows (mapping, asset) into ScopedAsset items
        items: List[ScopedAsset] = []
        for mapping, asset in rows:
            items.append(
                ScopedAsset(
                    id=asset.id,
                    name=asset.name,
                    type=asset.type,
                    compliant=mapping.compliant,
                    justification=mapping.justification,
                    last_review_date=mapping.last_review_date,
                    next_review_date=mapping.next_review_date,
                    compliance_notes=mapping.compliance_notes,
                )
            )

        return create_paginated_response(
            data=items, total=total, page=page, per_page=per_page
        )

    def get_cursor_scope_assets(
        self,
        scope_id: int,
        cursor: int | None = None,
        per_page: int = 20,
        sort_by: str | None = None,
        sort_order: str = "asc",
        search: str | None = None,
        filters: dict | None = None,
    ):
        if not has_permission(self.current_user, "list", "compliance_scope"):
            raise PermissionError("Not allowed to list compliance scopes.")

        rows, total = compliance_crud.get_cursor_scope_assets(
            self.db,
            scope_id=scope_id,
            cursor=cursor,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )

        items: List[ScopedAsset] = []
        for mapping, asset in rows:
            items.append(
                ScopedAsset(
                    id=asset.id,
                    name=asset.name,
                    type=asset.type,
                    compliant=mapping.compliant,
                    justification=mapping.justification,
                    last_review_date=mapping.last_review_date,
                    next_review_date=mapping.next_review_date,
                    compliance_notes=mapping.compliance_notes,
                )
            )

        # For cursor mode, we still return PaginatedResponse for consistency
        # with users endpoint behaviour
        page_number = 1
        return create_paginated_response(
            data=items, total=total, page=page_number, per_page=per_page
        )

    # ----------------------------------------
    # Controls for a given scope
    # ----------------------------------------

    def list_scope_controls(self, scope_id: int) -> list[ComplianceControlListItem]:
        if not has_permission(self.current_user, "list", "compliance_scope"):
            raise PermissionError("Not allowed to list compliance scopes.")
        # aggregate query returns tuples (control, document_count)
        rows = compliance_crud.list_scope_controls_with_count(self.db, scope_id)
        items: list[ComplianceControlListItem] = []
        for control, document_count in rows:
            items.append(
                ComplianceControlListItem(
                    id=control.id,
                    scope_id=control.scope_id,
                    code=control.code,
                    title=control.title,
                    description=control.description,
                    required_document_name=control.required_document_name,
                    required_document_description=control.required_document_description,
                    required_document_type=control.required_document_type,
                    last_audit_date=control.last_audit_date,
                    last_audit_result=control.last_audit_result,
                    last_review_date=control.last_review_date,
                    next_review_date=control.next_review_date,
                    expiration_date=control.expiration_date,
                    status=control.status,
                    compliance_notes=control.compliance_notes,
                    document_count=int(document_count or 0),
                )
            )
        return items

    def get_scope_control(
        self, scope_id: int, control_id: int
    ) -> ComplianceControlSchema | None:
        if not has_permission(self.current_user, "list", "compliance_scope"):
            raise PermissionError("Not allowed to list compliance scopes.")
        control = compliance_crud.get_control_for_scope(self.db, scope_id, control_id)
        return control

    # ----------------------------------------
    # Link/unlink documents to a control
    # ----------------------------------------

    def link_documents_to_control(
        self, scope_id: int, control_id: int, payload: ControlDocumentLinkCreate
    ):
        if not has_permission(self.current_user, "update", "compliance_scope"):
            raise PermissionError("Not allowed to update compliance scopes.")
        control = compliance_crud.get_control(self.db, control_id)
        if control is None or control.scope_id != scope_id:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Control not found in scope")

        # Validate documents
        existing_docs = compliance_crud.get_documents_by_ids(
            self.db, payload.document_ids
        )
        existing_ids = {d.id for d in existing_docs}
        missing = [
            doc_id for doc_id in payload.document_ids if doc_id not in existing_ids
        ]
        if missing:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail=f"Documents not found: {missing}"
            )

        links = compliance_crud.create_control_document_links(
            self.db,
            control_id=control_id,
            document_ids=payload.document_ids,
        )

        # Update each document's review frequency to the most stringent (minimum) across all linked controls
        for doc in existing_docs:
            min_freq = (
                self.db.query(
                    func.min(
                        func.coalesce(ComplianceControl.review_frequency_months, 12)
                    )
                )
                .join(
                    ControlDocumentLink,
                    ControlDocumentLink.control_id == ComplianceControl.id,
                )
                .filter(ControlDocumentLink.document_id == doc.id)
                .scalar()
            )
            if min_freq is None:
                min_freq = 12
            doc.review_frequency_months = int(min_freq)
        self.db.commit()

        return links

    def unlink_documents_from_control(
        self, scope_id: int, control_id: int, payload: ControlDocumentLinkDelete
    ) -> int:
        if not has_permission(self.current_user, "update", "compliance_scope"):
            raise PermissionError("Not allowed to update compliance scopes.")
        control = compliance_crud.get_control(self.db, control_id)
        if control is None or control.scope_id != scope_id:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Control not found in scope")

        # Validate documents
        existing_docs = compliance_crud.get_documents_by_ids(
            self.db, payload.document_ids
        )
        existing_ids = {d.id for d in existing_docs}
        missing = [
            doc_id for doc_id in payload.document_ids if doc_id not in existing_ids
        ]
        if missing:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail=f"Documents not found: {missing}"
            )

        deleted = compliance_crud.delete_control_document_links(
            self.db, control_id=control_id, document_ids=payload.document_ids
        )

        # Recompute each affected document's most stringent (minimum) review frequency among remaining links
        for doc_id in payload.document_ids:
            # Compute min frequency across remaining controls for this document (default to 12)
            min_freq = (
                self.db.query(
                    func.min(
                        func.coalesce(ComplianceControl.review_frequency_months, 12)
                    )
                )
                .join(
                    ControlDocumentLink,
                    ControlDocumentLink.control_id == ComplianceControl.id,
                )
                .filter(ControlDocumentLink.document_id == doc_id)
                .scalar()
            )
            if min_freq is None:
                min_freq = 12

            # Update the document's review frequency
            doc = self.db.query(Document).filter(Document.id == doc_id).one_or_none()
            if doc is not None:
                doc.review_frequency_months = int(min_freq)

        self.db.commit()

        return deleted
