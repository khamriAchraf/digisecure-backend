from datetime import datetime
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate


def get_asset(db: Session, asset_id: int) -> Optional[Asset]:
    return db.query(Asset).filter(Asset.id == asset_id).first()


def list_assets(db: Session, skip: int = 0, limit: int = 100) -> List[Asset]:
    return db.query(Asset).offset(skip).limit(limit).all()


def create_asset(db: Session, asset_in: AssetCreate) -> Asset:
    now = datetime.utcnow()
    asset = Asset(
        name=asset_in.name,
        asset_type=asset_in.asset_type,
        serial_number=asset_in.serial_number,
        inventory_number=asset_in.inventory_number,
        manufacturer_id=asset_in.manufacturer_id,
        status=asset_in.status,
        purchase_date=asset_in.purchase_date,
        warranty_expiry=asset_in.warranty_expiry,
        location_id=asset_in.location_id,
        group_id=asset_in.group_id,
        assigned_to=asset_in.assigned_to,
        created_at=now,
        updated_at=now,
    )
    db.add(asset)
    try:
        db.commit()
        db.refresh(asset)
    except IntegrityError:
        db.rollback()
        raise
    return asset


def update_asset(db: Session, asset: Asset, asset_in: AssetUpdate) -> Asset:
    for field, value in asset_in.dict(exclude_unset=True).items():
        setattr(asset, field, value)
    asset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(asset)
    return asset


def delete_asset(db: Session, asset: Asset) -> None:
    db.delete(asset)
    db.commit()
