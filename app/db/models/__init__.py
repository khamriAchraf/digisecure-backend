# Import all models to ensure they are registered with SQLAlchemy
from app.db.models.asset import Asset
from app.db.models.compliance_scopes import (AssetComplianceScope,
                                             ComplianceScope)
from app.db.models.group import Group
from app.db.models.location import Location
from app.db.models.manufacturer import Manufacturer
from app.db.models.refresh_token import RefreshToken
from app.db.models.role import Permission, Role
from app.db.models.table_config import TableConfig
from app.db.models.user import User

__all__ = [
    "User",
    "Role",
    "Permission",
    "Group",
    "RefreshToken",
    "Location",
    "Manufacturer",
    "Asset",
    "TableConfig",
    "ComplianceScope",
    "AssetComplianceScope",
]
