from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.models.asset import Asset
from app.db.models.compliance_scopes import (AssetComplianceScope,
                                             ComplianceControl,
                                             ComplianceScope,
                                             ControlDocumentLink)
from app.db.models.document_store import Document
from app.schemas.compliance_scope import (AssetComplianceScopeCreate,
                                          AssetComplianceScopeUpdate,
                                          ComplianceScopeCreate,
                                          ComplianceScopeUpdate)


# ComplianceScope CRUD
def get_scope(db: Session, scope_id: int) -> Optional[ComplianceScope]:
    return (
        db.query(ComplianceScope)
        .options(
            joinedload(ComplianceScope.asset_mappings).joinedload(
                AssetComplianceScope.asset
            )
        )
        .filter(ComplianceScope.id == scope_id)
        .first()
    )


def get_scope_by_name(db: Session, name: str) -> Optional[ComplianceScope]:
    return db.query(ComplianceScope).filter(ComplianceScope.name == name).first()


def list_scopes(db: Session, skip: int = 0, limit: int = 100) -> List[ComplianceScope]:
    return (
        db.query(ComplianceScope)
        .options(
            joinedload(ComplianceScope.asset_mappings).joinedload(
                AssetComplianceScope.asset
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_scope(db: Session, scope_in: ComplianceScopeCreate) -> ComplianceScope:
    scope = ComplianceScope(**scope_in.dict())
    db.add(scope)
    db.commit()
    db.refresh(scope)
    return scope


def update_scope(
    db: Session, scope: ComplianceScope, scope_in: ComplianceScopeUpdate
) -> ComplianceScope:
    for field, value in scope_in.dict(exclude_unset=True).items():
        setattr(scope, field, value)
    db.commit()
    db.refresh(scope)
    return scope


def delete_scope(db: Session, scope: ComplianceScope) -> None:
    scope.soft_delete(db)
    db.commit()


# AssetComplianceScope CRUD
def get_asset_scope(
    db: Session, asset_id: int, scope_id: int
) -> Optional[AssetComplianceScope]:
    return (
        db.query(AssetComplianceScope)
        .filter(
            AssetComplianceScope.asset_id == asset_id,
            AssetComplianceScope.scope_id == scope_id,
        )
        .first()
    )


def list_asset_scopes(db: Session, asset_id: int) -> List[AssetComplianceScope]:
    return (
        db.query(AssetComplianceScope)
        .filter(AssetComplianceScope.asset_id == asset_id)
        .all()
    )


def create_asset_scope(
    db: Session, mapping_in: AssetComplianceScopeCreate
) -> AssetComplianceScope:
    mapping = AssetComplianceScope(**mapping_in.dict())
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


def update_asset_scope(
    db: Session, mapping: AssetComplianceScope, mapping_in: AssetComplianceScopeUpdate
) -> AssetComplianceScope:
    for field, value in mapping_in.dict(exclude_unset=True).items():
        setattr(mapping, field, value)
    db.commit()
    db.refresh(mapping)
    return mapping


def delete_asset_scope(db: Session, mapping: AssetComplianceScope) -> None:
    db.delete(mapping)
    db.commit()


# ----------------------------------------
# Paginated assets for a given compliance scope
# Mirrors user pagination and search/filter style
# ----------------------------------------


def get_paginated_scope_assets(
    db: Session,
    scope_id: int,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Tuple[AssetComplianceScope, Asset]], int]:
    """Return paginated (mapping, asset) rows for assets within a scope.

    - Supports search on asset name and serial/inventory numbers
    - Supports filter on asset `type` via filters["type"] if provided
    - Sorting defaults to asset.id when sort_by is unspecified
    """

    # Base join query between mapping and asset
    query = (
        db.query(AssetComplianceScope, Asset)
        .join(Asset, AssetComplianceScope.asset_id == Asset.id)
        .filter(AssetComplianceScope.scope_id == scope_id)
    )

    # Apply filters
    if filters:
        # explicit support for type filtering
        asset_type = filters.get("type")
        if asset_type:
            query = query.filter(Asset.type == asset_type)

        # Allow exact match filters on Asset columns if passed
        for key, value in filters.items():
            if key == "type":
                continue
            if hasattr(Asset, key) and value is not None and value != "":
                query = query.filter(getattr(Asset, key) == value)

    # Apply search across common asset identifiers
    if search:
        from sqlalchemy import or_

        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Asset.name.ilike(search_term),
                Asset.serial_number.ilike(search_term),
                Asset.inventory_number.ilike(search_term),
            )
        )

    total = query.count()

    # Sorting
    if sort_by and hasattr(Asset, sort_by):
        column = getattr(Asset, sort_by)
    else:
        column = Asset.id

    if sort_order.lower() == "desc":
        query = query.order_by(column.desc())
    else:
        query = query.order_by(column.asc())

    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    rows = query.all()
    return rows, total


def get_cursor_scope_assets(
    db: Session,
    scope_id: int,
    cursor: Optional[int] = None,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Tuple[AssetComplianceScope, Asset]], int]:
    """Return assets for infinite scrolling within a scope based on an integer cursor.

    Applies the cursor to Asset.id semantics similar to users cursor pagination.
    """

    query = (
        db.query(AssetComplianceScope, Asset)
        .join(Asset, AssetComplianceScope.asset_id == Asset.id)
        .filter(AssetComplianceScope.scope_id == scope_id)
    )

    # Filters
    if filters:
        asset_type = filters.get("type")
        if asset_type:
            query = query.filter(Asset.type == asset_type)
        for key, value in filters.items():
            if key == "type":
                continue
            if hasattr(Asset, key) and value is not None and value != "":
                query = query.filter(getattr(Asset, key) == value)

    # Search
    if search:
        from sqlalchemy import or_

        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Asset.name.ilike(search_term),
                Asset.serial_number.ilike(search_term),
                Asset.inventory_number.ilike(search_term),
            )
        )

    if cursor is not None:
        if sort_order.lower() == "desc":
            query = query.filter(Asset.id < cursor)
        else:
            query = query.filter(Asset.id > cursor)

    total = query.count()

    # Sorting (fallback to id)
    if sort_by and hasattr(Asset, sort_by):
        column = getattr(Asset, sort_by)
    else:
        column = Asset.id

    if sort_order.lower() == "desc":
        query = query.order_by(column.desc())
    else:
        query = query.order_by(column.asc())

    # Limit
    query = query.limit(per_page)
    rows = query.all()
    return rows, total


# Controls for a scope
def list_scope_controls(db: Session, scope_id: int):
    return (
        db.query(ComplianceControl)
        .options(selectinload(ComplianceControl.documents))
        .filter(ComplianceControl.scope_id == scope_id)
        .order_by(ComplianceControl.code.asc())
        .all()
    )


def get_control(db: Session, control_id: int) -> Optional[ComplianceControl]:
    return (
        db.query(ComplianceControl).filter(ComplianceControl.id == control_id).first()
    )


def get_control_for_scope(
    db: Session, scope_id: int, control_id: int
) -> Optional[ComplianceControl]:
    return (
        db.query(ComplianceControl)
        .options(selectinload(ComplianceControl.documents))
        .filter(
            ComplianceControl.id == control_id,
            ComplianceControl.scope_id == scope_id,
        )
        .first()
    )


def list_scope_controls_with_count(db: Session, scope_id: int):
    """Return controls for a scope with aggregated document count per control."""
    counts_subq = (
        db.query(
            ControlDocumentLink.control_id.label("control_id"),
            func.count(ControlDocumentLink.document_id).label("document_count"),
        )
        .group_by(ControlDocumentLink.control_id)
        .subquery()
    )

    return (
        db.query(
            ComplianceControl,
            func.coalesce(counts_subq.c.document_count, 0).label("document_count"),
        )
        .outerjoin(counts_subq, counts_subq.c.control_id == ComplianceControl.id)
        .filter(ComplianceControl.scope_id == scope_id)
        .order_by(ComplianceControl.code.asc())
        .all()
    )


def create_control_document_links(
    db: Session,
    control_id: int,
    document_ids: List[int],
) -> List[ControlDocumentLink]:
    links: List[ControlDocumentLink] = []
    # Avoid creating duplicates
    existing = {
        row.document_id
        for row in db.query(ControlDocumentLink.document_id)
        .filter(
            ControlDocumentLink.control_id == control_id,
            ControlDocumentLink.document_id.in_(document_ids),
        )
        .all()
    }
    for doc_id in document_ids:
        if doc_id in existing:
            continue
        link = ControlDocumentLink(control_id=control_id, document_id=doc_id)
        db.add(link)
        links.append(link)
    db.commit()
    return links


def delete_control_document_links(
    db: Session, control_id: int, document_ids: List[int]
) -> int:
    q = db.query(ControlDocumentLink).filter(
        ControlDocumentLink.control_id == control_id,
        ControlDocumentLink.document_id.in_(document_ids),
    )
    count = q.count()
    q.delete(synchronize_session=False)
    db.commit()
    return count


def get_documents_by_ids(db: Session, document_ids: List[int]) -> List[Document]:
    if not document_ids:
        return []
    return db.query(Document).filter(Document.id.in_(document_ids)).all()
