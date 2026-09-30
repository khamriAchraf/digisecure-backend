# Import all models to ensure they are registered with SQLAlchemy
from app.db.models.asset import Asset
from app.db.models.compliance_event import (ComplianceEvent,
                                            compliance_event_notify_groups,
                                            compliance_event_notify_users)
from app.db.models.compliance_scopes import (AssetComplianceScope,
                                             ComplianceControl,
                                             ComplianceScope,
                                             ControlDocumentLink)
from app.db.models.document_store import (Document, DocumentFolder,
                                          DocumentVersion)
from app.db.models.group import Group
from app.db.models.location import Location
from app.db.models.manufacturer import Manufacturer
from app.db.models.operating_system import OperatingSystem
from app.db.models.password_reset_token import PasswordResetToken
from app.db.models.refresh_token import RefreshToken
from app.db.models.role import Permission, Role
from app.db.models.table_config import TableConfig
from app.db.models.user import User
from app.db.models.api_key import ApiKey

__all__ = [
    "User",
    "Role",
    "Permission",
    "Group",
    "RefreshToken",
    "PasswordResetToken",
    "Location",
    "Manufacturer",
    "OperatingSystem",
    "Asset",
    "TableConfig",
    "ComplianceScope",
    "ComplianceEvent",
    "compliance_event_notify_users",
    "compliance_event_notify_groups",
    "ComplianceControl",
    "ControlDocumentLink",
    "AssetComplianceScope",
    "Document",
    "DocumentVersion",
    "DocumentFolder",
    "ApiKey"
]
