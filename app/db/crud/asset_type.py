from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.asset_type import AssetType
from app.schemas.asset_type import AssetTypeCreate, AssetTypeUpdate


def get_asset_type(db: Session, asset_type_id: int) -> Optional[AssetType]:
    return db.query(AssetType).filter(AssetType.id == asset_type_id).first()


def get_asset_type_by_name(db: Session, name: str) -> Optional[AssetType]:
    return db.query(AssetType).filter(AssetType.name == name).first()


def list_asset_types(db: Session, skip: int = 0, limit: int = 100) -> List[AssetType]:
    return db.query(AssetType).offset(skip).limit(limit).all()


def create_asset_type(db: Session, asset_type_in: AssetTypeCreate) -> AssetType:
    asset_type = AssetType(
        name=asset_type_in.name,
        description=asset_type_in.description,
        is_builtin=asset_type_in.is_builtin or False,
    )
    db.add(asset_type)
    try:
        db.commit()
        db.refresh(asset_type)
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        if "unique constraint" in msg and "asset_types_name" in msg:
            raise ValueError(
                f"AssetType with name '{asset_type_in.name}' already exists."
            )
        raise
    return asset_type


def update_asset_type(
    db: Session, asset_type: AssetType, asset_type_in: AssetTypeUpdate
) -> AssetType:
    for field, value in asset_type_in.dict(exclude_unset=True).items():
        setattr(asset_type, field, value)
    db.commit()
    db.refresh(asset_type)
    return asset_type


def delete_asset_type(db: Session, asset_type: AssetType) -> None:
    db.delete(asset_type)
    db.commit()
