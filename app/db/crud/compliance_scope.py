from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.db.models.compliance_scopes import (AssetComplianceScope,
                                             ComplianceScope)
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
    db.delete(scope)
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
