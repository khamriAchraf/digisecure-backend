from datetime import datetime, timezone
from typing import List, Optional, Tuple, Union

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, with_polymorphic

from app.db.models.asset import (Asset, Computer, NetworkDevice, Software,
                                 VirtualMachine)
from app.schemas.asset import (ComputerCreate, ComputerUpdate,
                               NetworkDeviceCreate, NetworkDeviceUpdate,
                               SoftwareCreate, SoftwareUpdate,
                               VirtualMachineCreate, VirtualMachineUpdate)

ASSET_TYPE_MAPPING = {
    "computer": (Computer, ComputerCreate),
    "network_device": (NetworkDevice, NetworkDeviceCreate),
    "virtual_machine": (VirtualMachine, VirtualMachineCreate),
    "software": (Software, SoftwareCreate),
}

ALL_ASSET_TYPES = [
    Asset,
    Computer,
    NetworkDevice,
    VirtualMachine,
    Software,
]


def get_asset(db: Session, asset_id: int) -> Optional[Asset]:
    return db.query(Asset).filter(Asset.id == asset_id).first()


def get_asset_by_type(db: Session, asset_id: int, asset_type: str) -> Optional[Asset]:
    if asset_type not in ASSET_TYPE_MAPPING:
        raise ValueError(f"Invalid asset type: {asset_type}")

    asset_class = ASSET_TYPE_MAPPING[asset_type][0]
    return (
        db.query(asset_class)
        .options(
            joinedload(asset_class.manufacturer),
            joinedload(asset_class.location),
            joinedload(asset_class.groups),
            joinedload(asset_class.assigned_user),
        )
        .filter(asset_class.id == asset_id)
        .first()
    )


def get_paginated_assets(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Asset], int]:

    AssetPoly = with_polymorphic(Asset, ALL_ASSET_TYPES)
    query = db.query(AssetPoly).options(
        joinedload(AssetPoly.manufacturer),
        joinedload(AssetPoly.location),
        joinedload(AssetPoly.groups),
        joinedload(AssetPoly.assigned_user),
    )

    # Apply filters
    if filters:
        if "warranty_expired" in filters:
            from datetime import date

            today = date.today()
            if filters["warranty_expired"]:
                query = query.filter(
                    Asset.warranty_expiry.isnot(None), Asset.warranty_expiry < today
                )
            else:
                query = query.filter(
                    Asset.warranty_expiry.isnot(None), Asset.warranty_expiry >= today
                )
            del filters["warranty_expired"]

        for key, value in filters.items():
            if hasattr(Asset, key) and value is not None and value != "":
                query = query.filter(getattr(Asset, key) == value)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Asset.name.ilike(search_term),
                Asset.serial_number.ilike(search_term),
                Asset.inventory_number.ilike(search_term),
            )
        )

    total = query.count()

    # Apply sorting
    if sort_by and hasattr(Asset, sort_by):
        column = getattr(Asset, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    assets = query.all()
    return assets, total


def create_asset(
    db: Session,
    asset_in: Union[
        ComputerCreate,
        NetworkDeviceCreate,
        VirtualMachineCreate,
        SoftwareCreate,
    ],
) -> Asset:
    now = datetime.now(timezone.utc)

    # Determine asset type from the input schema
    asset_type = None
    for type_name, (asset_class, create_class) in ASSET_TYPE_MAPPING.items():
        if isinstance(asset_in, create_class):
            asset_type = type_name
            break

    if asset_type is None:
        # This should not happen with proper type checking, but handle gracefully
        raise ValueError("Invalid asset type - must be one of the supported subtypes")

    # Get the appropriate asset class
    asset_class = ASSET_TYPE_MAPPING[asset_type][0]

    # Prepare base fields
    base_fields = {
        "name": asset_in.name,
        "serial_number": asset_in.serial_number,
        "inventory_number": asset_in.inventory_number,
        "manufacturer_id": asset_in.manufacturer_id,
        "status": asset_in.status,
        "purchase_date": asset_in.purchase_date,
        "warranty_expiry": asset_in.warranty_expiry,
        "location_id": asset_in.location_id,
        "assigned_to": asset_in.assigned_to,
        "type": asset_type,
        "created_at": now,
        "updated_at": now,
    }

    subtype_fields = {}
    for field_name in asset_in.__fields__:
        if field_name not in base_fields and hasattr(asset_in, field_name):
            value = getattr(asset_in, field_name)
            if value is not None:
                subtype_fields[field_name] = value

    asset = asset_class(**base_fields, **subtype_fields)

    db.add(asset)
    try:
        db.commit()
        db.refresh(asset)

        if hasattr(asset_in, "group_ids") and asset_in.group_ids:
            from app.db.models.group import Group

            groups = db.query(Group).filter(Group.id.in_(asset_in.group_ids)).all()
            asset.groups = groups
            db.commit()
            db.refresh(asset)

    except IntegrityError:
        db.rollback()
        raise
    return asset


def update_asset(
    db: Session,
    asset: Asset,
    asset_in: Union[
        ComputerUpdate,
        NetworkDeviceUpdate,
        VirtualMachineUpdate,
        SoftwareUpdate,
    ],
) -> Asset:
    base_fields = [
        "name",
        "serial_number",
        "inventory_number",
        "manufacturer_id",
        "status",
        "purchase_date",
        "warranty_expiry",
        "location_id",
        "assigned_to",
    ]

    for field in base_fields:
        if hasattr(asset_in, field) and getattr(asset_in, field) is not None:
            setattr(asset, field, getattr(asset_in, field))

    for field, value in asset_in.dict(exclude_unset=True).items():
        if field not in base_fields and hasattr(asset, field):
            setattr(asset, field, value)

    # Handle groups relationship if group_ids are provided
    if hasattr(asset_in, "group_ids") and asset_in.group_ids is not None:
        from app.db.models.group import Group

        groups = db.query(Group).filter(Group.id.in_(asset_in.group_ids)).all()
        asset.groups = groups

    setattr(asset, "updated_at", datetime.now(timezone.utc))
    db.commit()
    db.refresh(asset)
    return asset


def delete_asset(db: Session, asset: Asset) -> None:
    asset.soft_delete()
    db.commit()


def get_asset_count_by_type(db: Session) -> dict:
    from sqlalchemy import func

    result = db.query(Asset.type, func.count(Asset.id)).group_by(Asset.type).all()
    return {row[0]: row[1] for row in result}


def get_asset_count_by_status(db: Session) -> dict:
    from sqlalchemy import func

    result = db.query(Asset.status, func.count(Asset.id)).group_by(Asset.status).all()
    return {row[0]: row[1] for row in result}


def get_asset_count_by_location(db: Session) -> dict:
    from sqlalchemy import func

    result = (
        db.query(Asset.location_id, func.count(Asset.id))
        .group_by(Asset.location_id)
        .all()
    )
    return {row[0]: row[1] for row in result}


def bulk_create_assets(
    db: Session,
    assets_in: List[
        Union[
            ComputerCreate,
            NetworkDeviceCreate,
            VirtualMachineCreate,
            SoftwareCreate,
        ]
    ],
) -> List[Asset]:
    now = datetime.now(timezone.utc)
    assets = []

    for asset_in in assets_in:
        # Determine asset type from the input schema
        asset_type = None
        for type_name, (asset_class, create_class) in ASSET_TYPE_MAPPING.items():
            if isinstance(asset_in, create_class):
                asset_type = type_name
                break

        if asset_type is None:
            # This should not happen with proper type checking, but handle gracefully
            raise ValueError(
                "Invalid asset type - must be one of the supported subtypes"
            )

        # Get the appropriate asset class
        asset_class = ASSET_TYPE_MAPPING[asset_type][0]

        # Prepare base fields
        base_fields = {
            "name": asset_in.name,
            "serial_number": asset_in.serial_number,
            "inventory_number": asset_in.inventory_number,
            "manufacturer_id": asset_in.manufacturer_id,
            "status": asset_in.status,
            "purchase_date": asset_in.purchase_date,
            "warranty_expiry": asset_in.warranty_expiry,
            "location_id": asset_in.location_id,
            "assigned_to": asset_in.assigned_to,
            "type": asset_type,  # This ensures the correct polymorphic identity
            "created_at": now,
            "updated_at": now,
        }

        # Extract subtype-specific fields
        subtype_fields = {}
        for field_name in asset_in.__fields__:
            if field_name not in base_fields and hasattr(asset_in, field_name):
                value = getattr(asset_in, field_name)
                if value is not None:  # Only include non-None values
                    subtype_fields[field_name] = value

        # Create the asset instance
        asset = asset_class(**base_fields, **subtype_fields)
        assets.append(asset)

    db.add_all(assets)
    try:
        db.commit()

        # Handle groups relationships for all assets
        for i, asset_in in enumerate(assets_in):
            if hasattr(asset_in, "group_ids") and asset_in.group_ids:
                from app.db.models.group import Group

                groups = db.query(Group).filter(Group.id.in_(asset_in.group_ids)).all()
                assets[i].groups = groups

        db.commit()
        for asset in assets:
            db.refresh(asset)

    except IntegrityError:
        db.rollback()
        raise

    return assets
