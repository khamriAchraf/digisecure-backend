import argparse
import sys
from datetime import date, datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.logger import logger
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import (ComplianceControl, ComplianceScope, Location,
                           Manufacturer, Permission, Role, TableConfig, User)
from app.db.models.asset import Computer, NetworkDevice, Software
from app.db.session import SessionLocal, engine

sys.path.append(".")
from tests.test_data import TEST_LOCATIONS, TEST_MANUFACTURERS, TEST_USERS


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Seed the database with initial data and optionally create a super-admin user"
    )
    parser.add_argument(
        "--username", type=str, help="Username for the super-admin user"
    )
    parser.add_argument("--email", type=str, help="Email for the super-admin user")
    parser.add_argument(
        "--password", type=str, help="Password for the super-admin user"
    )
    parser.add_argument(
        "--full-name",
        type=str,
        default="Super Administrator",
        help="Full name for the super-admin user (default: Super Administrator)",
    )

    return parser.parse_args()


def create_super_admin_user(session, username, email, password, full_name):
    """Create a super-admin user with the provided credentials"""
    logger.info(f"Creating super-admin user: {username} ({email})")

    # Check if user already exists
    existing_user = (
        session.query(User)
        .filter((User.username == username) | (User.email == email))
        .first()
    )

    if existing_user:
        logger.warning(
            f"User with username '{username}' or email '{email}' already exists"
        )
        return existing_user

    # Get the Super-Admin role
    super_admin_role = session.query(Role).filter_by(name="Super-Admin").first()
    if not super_admin_role:
        logger.error(
            "Super-Admin role not found. Please run the seed script without user creation first."
        )
        return None

    hashed_password = get_password_hash(password)

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        status="active",
    )

    user.role = super_admin_role

    session.add(user)
    session.commit()

    logger.info(f"Successfully created super-admin user with ID: {user.id}")
    return user


def create_user_audit_table_and_trigger(session):
    # Create the audit table
    session.execute(
        text(
            """
    CREATE TABLE IF NOT EXISTS users_audit (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        request_id VARCHAR(64),
        action VARCHAR(10),
        changed_by INTEGER,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        old_data JSONB,
        new_data JSONB
    );
    """
        )
    )

    # Create the trigger function
    session.execute(
        text(
            """
    CREATE OR REPLACE FUNCTION audit_user_changes()
    RETURNS TRIGGER AS $$
    DECLARE
        current_user_id INTEGER;
        current_request_id VARCHAR(64);
    BEGIN
        BEGIN
            current_user_id := current_setting('app.current_user_id', true)::INTEGER;
        EXCEPTION WHEN OTHERS THEN
            current_user_id := NULL;
        END;
        BEGIN
            current_request_id := current_setting('app.request_id', true);
        EXCEPTION WHEN OTHERS THEN
            current_request_id := NULL;
        END;

        IF TG_OP = 'INSERT' THEN
            INSERT INTO users_audit (user_id, request_id, action, changed_by, new_data)
            VALUES (NEW.id, current_request_id, 'INSERT', current_user_id, row_to_json(NEW));
            RETURN NEW;
        ELSIF TG_OP = 'UPDATE' THEN
            INSERT INTO users_audit (user_id, request_id, action, changed_by, old_data, new_data)
            VALUES (NEW.id, current_request_id, 'UPDATE', current_user_id, row_to_json(OLD), row_to_json(NEW));
            RETURN NEW;
        ELSIF TG_OP = 'DELETE' THEN
            INSERT INTO users_audit (user_id, request_id, action, changed_by, old_data)
            VALUES (OLD.id, current_request_id, 'DELETE', current_user_id, row_to_json(OLD));
            RETURN OLD;
        END IF;
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
    """
        )
    )

    # Attach the trigger to the users table (not user)
    session.execute(
        text(
            """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger WHERE tgname = 'user_audit_trigger'
        ) THEN
            CREATE TRIGGER user_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON "users"
            FOR EACH ROW EXECUTE FUNCTION audit_user_changes();
        END IF;
    END;
    $$;
    """
        )
    )
    session.commit()


def create_sample_assets(session):
    """Create sample assets for each type"""
    logger.info("Creating sample assets...")

    # Get some locations and manufacturers for reference
    locations = session.query(Location).all()
    manufacturers = session.query(Manufacturer).all()
    users = session.query(User).all()

    if not locations:
        logger.warning(
            "No locations found, creating assets without location assignment"
        )
    if not manufacturers:
        logger.warning(
            "No manufacturers found, creating assets without manufacturer assignment"
        )
    if not users:
        logger.warning("No users found, creating assets without user assignment")

    now = datetime.now(timezone.utc)

    # Sample Computers
    computers_data = [
        {
            "name": "Workstation-001",
            "serial_number": "WS001-2024-001",
            "inventory_number": "INV-COMP-001",
            "manufacturer_id": manufacturers[0].id if manufacturers else None,
            "status": "active",
            "purchase_date": date(2024, 1, 15),
            "warranty_expiry": date(2027, 1, 15),
            "location_id": locations[0].id if locations else None,
            "assigned_to": users[0].id if users else None,
            "type": "computer",
            "cpu": "Intel Core i7-12700K",
            "ram": "32GB DDR4",
            "storage": "1TB NVMe SSD",
            "os": "Windows 11 Pro",
            "mac_address": "00:1B:44:11:3A:B7",
            "ip_address": "192.168.1.100",
            "model": "Dell OptiPlex 7090",
            "hostname": "WS001",
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "Laptop-001",
            "serial_number": "LP001-2024-002",
            "inventory_number": "INV-COMP-002",
            "manufacturer_id": (
                manufacturers[1].id
                if len(manufacturers) > 1
                else manufacturers[0].id if manufacturers else None
            ),
            "status": "active",
            "purchase_date": date(2024, 2, 20),
            "warranty_expiry": date(2027, 2, 20),
            "location_id": (
                locations[1].id
                if len(locations) > 1
                else locations[0].id if locations else None
            ),
            "assigned_to": (
                users[1].id if len(users) > 1 else users[0].id if users else None
            ),
            "type": "computer",
            "created_at": now,
            "updated_at": now,
            "cpu": "AMD Ryzen 7 5800H",
            "ram": "16GB DDR4",
            "storage": "512GB NVMe SSD",
            "os": "Ubuntu 22.04 LTS",
            "mac_address": "00:1B:44:11:3A:B8",
            "ip_address": "192.168.1.101",
            "model": "Lenovo ThinkPad T14",
            "hostname": "LP001",
        },
    ]

    # Sample Network Devices
    network_devices_data = [
        {
            "name": "Core-Switch-01",
            "serial_number": "SW001-2023-001",
            "inventory_number": "INV-NET-001",
            "manufacturer_id": (
                manufacturers[2].id
                if len(manufacturers) > 2
                else manufacturers[0].id if manufacturers else None
            ),
            "status": "active",
            "purchase_date": date(2023, 3, 15),
            "warranty_expiry": date(2028, 3, 15),
            "location_id": locations[0].id if locations else None,
            "type": "network_device",
            "device_type": "Switch",
            "model": "Cisco Catalyst 2960-X",
            "ip_address": "192.168.1.1",
            "mac_address": "00:1B:44:11:3A:D1",
            "port_count": 48,
            "connection_type": "Ethernet",
            "management_ip": "192.168.1.1",
            "firmware_version": "15.2(4)E7",
            "created_at": now,
            "updated_at": now,
        }
    ]

    # Sample Software
    software_data = [
        {
            "name": "Microsoft Office 365",
            "serial_number": "SW001-2023-001",
            "inventory_number": "INV-SOFT-001",
            "manufacturer_id": None,
            "status": "active",
            "purchase_date": None,
            "warranty_expiry": None,
            "location_id": None,
            "assigned_to": None,
            "type": "software",
            "created_at": now,
            "updated_at": now,
            "vendor": "Microsoft",
            "description": "Office productivity suite",
            "software_type": "Application",
        }
    ]

    # Create assets
    assets_created = 0

    # Create computers
    for comp_data in computers_data:
        existing = (
            session.query(Computer)
            .filter_by(serial_number=comp_data["serial_number"])
            .first()
        )
        if not existing:
            computer = Computer(**comp_data)
            session.add(computer)
            assets_created += 1

    # Create network devices
    for net_data in network_devices_data:
        existing = (
            session.query(NetworkDevice)
            .filter_by(serial_number=net_data["serial_number"])
            .first()
        )
        if not existing:
            network_device = NetworkDevice(**net_data)
            session.add(network_device)
            assets_created += 1

    # Create software
    for soft_data in software_data:
        existing = (
            session.query(Software)
            .filter_by(serial_number=soft_data["serial_number"])
            .first()
        )
        if not existing:
            software = Software(**soft_data)
            session.add(software)
            assets_created += 1

    session.commit()
    logger.info(f"Created {assets_created} sample assets")


def ensure_database_exists():
    """Ensure the target database exists; create it if missing."""
    admin_url = (
        f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/postgres"
    )
    logger.info("Ensuring database '%s' exists...", settings.DB_NAME)
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": settings.DB_NAME},
            ).scalar()
            if not exists:
                logger.info("Database '%s' not found. Creating...", settings.DB_NAME)
                conn.execute(
                    text(
                        f'CREATE DATABASE "{settings.DB_NAME}" OWNER "{settings.DB_USER}" ENCODING "UTF8" TEMPLATE template1'
                    )
                )
                logger.info("Database '%s' created.", settings.DB_NAME)
            else:
                logger.info("Database '%s' already exists.", settings.DB_NAME)
    finally:
        admin_engine.dispose()


def ensure_schema_exists():
    """Ensure the target schema exists in the selected database."""
    db_url = (
        f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
    logger.info(
        "Ensuring schema '%s' exists in database '%s'...",
        settings.DB_SCHEMA,
        settings.DB_NAME,
    )
    schema_engine = create_engine(db_url)
    try:
        with schema_engine.connect() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.DB_SCHEMA}"'))
            logger.info("Schema '%s' ensured.", settings.DB_SCHEMA)
    finally:
        schema_engine.dispose()


def main():
    args = parse_arguments()

    if any([args.username, args.email, args.password]) and not all(
        [args.username, args.email, args.password]
    ):
        logger.error(
            "If creating a super-admin user, all three arguments (--username, --email, --password) are required"
        )
        sys.exit(1)

    logger.info(f"Seeding database: {settings.DB_NAME}")

    # Ensure database and schema exist before proceeding
    ensure_database_exists()
    ensure_schema_exists()

    logger.info("Creating all tables (if not exist)...")
    Base.metadata.create_all(bind=engine)

    # Ensure DDL is flushed by closing and reopening the session
    session = SessionLocal()
    session.close()
    session = SessionLocal()

    # Create audit table and trigger
    create_user_audit_table_and_trigger(session)

    preset_roles = [
        {
            "name": "Super-Admin",
            "description": "Full access to all system features and settings",
            "is_builtin": True,
            "rank": 1,
        },
        {
            "name": "Admin",
            "description": "Manage users and settings within their organization",
            "is_builtin": True,
            "rank": 2,
        },
        {
            "name": "Supervisor",
            "description": "Oversee teams and approve actions",
            "is_builtin": True,
            "rank": 3,
        },
        {
            "name": "Technician",
            "description": "Handle technical tasks and tickets",
            "is_builtin": True,
            "rank": 4,
        },
        {
            "name": "Hotliner",
            "description": "First-line support and ticket triage",
            "is_builtin": True,
            "rank": 5,
        },
        {
            "name": "Observer",
            "description": "Read-only access to data",
            "is_builtin": True,
            "rank": 6,
        },
        {
            "name": "Self-Service",
            "description": "Limited access for end users",
            "is_builtin": True,
            "rank": 7,
        },
    ]

    # 3. User management permissions
    user_permissions = [
        {"action": "read", "resource": "user", "description": "View user information"},
        {"action": "list", "resource": "user", "description": "List users"},
        {"action": "create", "resource": "user", "description": "Create new users"},
        {
            "action": "update",
            "resource": "user",
            "description": "Update user information",
        },
        {"action": "delete", "resource": "user", "description": "Soft-delete users"},
        {
            "action": "purge",
            "resource": "user",
            "description": "Permanently delete users",
        },
    ]

    # 4. Role management permissions
    role_permissions = [
        {"action": "read", "resource": "role", "description": "View role information"},
        {"action": "list", "resource": "role", "description": "List roles"},
        {"action": "create", "resource": "role", "description": "Create new roles"},
        {
            "action": "update",
            "resource": "role",
            "description": "Update role information",
        },
        {"action": "delete", "resource": "role", "description": "Delete roles"},
        {
            "action": "purge",
            "resource": "role",
            "description": "Permanently delete roles",
        },
    ]

    # 5. Group management permissions
    group_permissions = [
        {
            "action": "read",
            "resource": "group",
            "description": "View group information",
        },
        {"action": "list", "resource": "group", "description": "List groups"},
        {"action": "create", "resource": "group", "description": "Create new groups"},
        {
            "action": "update",
            "resource": "group",
            "description": "Update group information",
        },
        {"action": "delete", "resource": "group", "description": "Delete groups"},
        {
            "action": "purge",
            "resource": "group",
            "description": "Permanently delete groups",
        },
    ]

    # 6. Reference data management permissions
    reference_data_permissions = [
        {
            "action": "read",
            "resource": "reference_data",
            "description": "View reference data information",
        },
        {
            "action": "list",
            "resource": "reference_data",
            "description": "List reference data",
        },
        {
            "action": "create",
            "resource": "reference_data",
            "description": "Create new reference data",
        },
        {
            "action": "update",
            "resource": "reference_data",
            "description": "Update reference data information",
        },
        {
            "action": "delete",
            "resource": "reference_data",
            "description": "Delete reference data",
        },
        {
            "action": "purge",
            "resource": "reference_data",
            "description": "Permanently delete reference data",
        },
    ]

    # 7. computer management permissions
    computer_permissions = [
        {
            "action": "read",
            "resource": "computer",
            "description": "View computer information",
        },
        {"action": "list", "resource": "computer", "description": "List computers"},
        {
            "action": "create",
            "resource": "computer",
            "description": "Create new computers",
        },
        {
            "action": "update",
            "resource": "computer",
            "description": "Update computer information",
        },
        {"action": "delete", "resource": "computer", "description": "Delete computers"},
        {
            "action": "purge",
            "resource": "computer",
            "description": "Permanently delete computers",
        },
    ]

    # 8. virtual machine management permissions
    virtual_machine_permissions = [
        {
            "action": "read",
            "resource": "virtual_machine",
            "description": "View virtual machine information",
        },
        {
            "action": "list",
            "resource": "virtual_machine",
            "description": "List virtual machines",
        },
        {
            "action": "create",
            "resource": "virtual_machine",
            "description": "Create new virtual machines",
        },
        {
            "action": "update",
            "resource": "virtual_machine",
            "description": "Update virtual machine information",
        },
        {
            "action": "delete",
            "resource": "virtual_machine",
            "description": "Delete virtual machines",
        },
        {
            "action": "purge",
            "resource": "virtual_machine",
            "description": "Permanently delete virtual machines",
        },
    ]

    # 9. network device management permissions
    network_device_permissions = [
        {
            "action": "read",
            "resource": "network_device",
            "description": "View network device information",
        },
        {
            "action": "list",
            "resource": "network_device",
            "description": "List network devices",
        },
        {
            "action": "create",
            "resource": "network_device",
            "description": "Create new network devices",
        },
        {
            "action": "update",
            "resource": "network_device",
            "description": "Update network device information",
        },
        {
            "action": "delete",
            "resource": "network_device",
            "description": "Delete network devices",
        },
        {
            "action": "purge",
            "resource": "network_device",
            "description": "Permanently delete network devices",
        },
    ]

    # 10. software management permissions
    software_permissions = [
        {
            "action": "read",
            "resource": "software",
            "description": "View software information",
        },
        {"action": "list", "resource": "software", "description": "List software"},
        {
            "action": "create",
            "resource": "software",
            "description": "Create new software",
        },
        {
            "action": "update",
            "resource": "software",
            "description": "Update software information",
        },
        {
            "action": "delete",
            "resource": "software",
            "description": "Delete software",
        },
        {
            "action": "purge",
            "resource": "software",
            "description": "Permanently delete software",
        },
    ]

    # 11a. certificate key management permissions
    certificate_key_permissions = [
        {
            "action": "read",
            "resource": "certificate_key",
            "description": "View certificate keys",
        },
        {
            "action": "list",
            "resource": "certificate_key",
            "description": "List certificate keys",
        },
        {
            "action": "create",
            "resource": "certificate_key",
            "description": "Create certificate keys",
        },
        {
            "action": "update",
            "resource": "certificate_key",
            "description": "Update certificate keys",
        },
        {
            "action": "delete",
            "resource": "certificate_key",
            "description": "Delete certificate keys",
        },
        {
            "action": "purge",
            "resource": "certificate_key",
            "description": "Permanently delete certificate keys",
        },
    ]

    # 11b. document management permissions
    document_permissions = [
        {"action": "read", "resource": "document", "description": "View documents"},
        {"action": "list", "resource": "document", "description": "List documents"},
        {
            "action": "create",
            "resource": "document",
            "description": "Create new documents",
        },
        {
            "action": "update",
            "resource": "document",
            "description": "Update documents (metadata and versions)",
        },
        {"action": "delete", "resource": "document", "description": "Delete documents"},
        {
            "action": "purge",
            "resource": "document",
            "description": "Permanently delete documents",
        },
    ]

    # 11. compliance scope management permissions
    compliance_scope_permissions = [
        {
            "action": "read",
            "resource": "compliance_scope",
            "description": "View compliance scopes",
        },
        {
            "action": "list",
            "resource": "compliance_scope",
            "description": "List compliance scopes",
        },
        {
            "action": "create",
            "resource": "compliance_scope",
            "description": "Create compliance scopes",
        },
        {
            "action": "update",
            "resource": "compliance_scope",
            "description": "Update compliance scopes",
        },
        {
            "action": "delete",
            "resource": "compliance_scope",
            "description": "Delete compliance scopes",
        },
        {
            "action": "purge",
            "resource": "compliance_scope",
            "description": "Permanently delete compliance scopes",
        },
    ]

    # 12. asset compliance management (tagging/un-tagging)
    asset_compliance_permissions = [
        {
            "action": "compliance_manage",
            "resource": "asset",
            "description": "Manage compliance scopes on assets (tag/untag/replace)",
        },
        {
            "action": "compliance_check",
            "resource": "asset",
            "description": "Check compliance of assets",
        },
    ]

    recycle_bin_user_permissions = [
        {
            "action": "read",
            "resource": "recycle_bin_user",
            "description": "View recycle bin(users)",
        },
        {
            "action": "list",
            "resource": "recycle_bin_user",
            "description": "List recycle bin users",
        },
        {
            "action": "restore",
            "resource": "recycle_bin_user",
            "description": "Restore deleted users",
        },
        {
            "action": "purge",
            "resource": "recycle_bin_user",
            "description": "Permanently remove deleted users",
        },
    ]

    recycle_bin_computer_permissions = [
        {
            "action": "read",
            "resource": "recycle_bin_computer",
            "description": "View recycle bin(computers)",
        },
        {
            "action": "list",
            "resource": "recycle_bin_computer",
            "description": "List recycle bin computers",
        },
        {
            "action": "restore",
            "resource": "recycle_bin_computer",
            "description": "Restore deleted computers",
        },
        {
            "action": "purge",
            "resource": "recycle_bin_computer",
            "description": "Permanently remove deleted computers",
        },
    ]
    recycle_bin_virtual_machine_permissions = [
        {
            "action": "read",
            "resource": "recycle_bin_virtual_machine",
            "description": "View recycle bin(virtual machines)",
        },
        {
            "action": "list",
            "resource": "recycle_bin_virtual_machine",
            "description": "List recycle bin virtual machines",
        },
        {
            "action": "restore",
            "resource": "recycle_bin_virtual_machine",
            "description": "Restore deleted virtual machines",
        },
        {
            "action": "purge",
            "resource": "recycle_bin_virtual_machine",
            "description": "Permanently remove deleted virtual machines",
        },
    ]
    recycle_bin_network_device_permissions = [
        {
            "action": "read",
            "resource": "recycle_bin_network_device",
            "description": "View recycle bin(network devices)",
        },
        {
            "action": "list",
            "resource": "recycle_bin_network_device",
            "description": "List recycle bin network devices",
        },
        {
            "action": "restore",
            "resource": "recycle_bin_network_device",
            "description": "Restore deleted network devices",
        },
        {
            "action": "purge",
            "resource": "recycle_bin_network_device",
            "description": "Permanently remove deleted network devices",
        },
    ]
    recycle_bin_software_permissions = [
        {
            "action": "read",
            "resource": "recycle_bin_software",
            "description": "View recycle bin(software)",
        },
        {
            "action": "list",
            "resource": "recycle_bin_software",
            "description": "List recycle bin software",
        },
        {
            "action": "restore",
            "resource": "recycle_bin_software",
            "description": "Restore deleted software",
        },
        {
            "action": "purge",
            "resource": "recycle_bin_software",
            "description": "Permanently remove deleted software",
        },
    ]
    recycle_bin_certificate_key_permissions = [
        {
            "action": "read",
            "resource": "recycle_bin_certificate_key",
            "description": "View recycle bin(certificate keys)",
        },
        {
            "action": "list",
            "resource": "recycle_bin_certificate_key",
            "description": "List recycle bin certificate keys",
        },
        {
            "action": "restore",
            "resource": "recycle_bin_certificate_key",
            "description": "Restore deleted certificate keys",
        },
        {
            "action": "purge",
            "resource": "recycle_bin_certificate_key",
            "description": "Permanently remove deleted certificate keys",
        },
    ]

    recycle_bin_group_permissions = [
        {
            "action": "read",
            "resource": "recycle_bin_group",
            "description": "View recycle bin(groups)",
        },
        {
            "action": "list",
            "resource": "recycle_bin_group",
            "description": "List recycle bin groups",
        },
        {
            "action": "restore",
            "resource": "recycle_bin_group",
            "description": "Restore deleted groups",
        },
        {
            "action": "purge",
            "resource": "recycle_bin_group",
            "description": "Permanently remove deleted groups",
        },
    ]

    ALL_PERMISSIONS = {
        "user": user_permissions,
        "role": role_permissions,
        "group": group_permissions,
        "reference_data": reference_data_permissions,
        "computer": computer_permissions,
        "virtual_machine": virtual_machine_permissions,
        "network_device": network_device_permissions,
        "software": software_permissions,
        "document": document_permissions,
        "compliance_scope": compliance_scope_permissions,
        "asset": asset_compliance_permissions,
        "recycle_bin_user": recycle_bin_user_permissions,
        "recycle_bin_computer": recycle_bin_computer_permissions,
        "recycle_bin_virtual_machine": recycle_bin_virtual_machine_permissions,
        "recycle_bin_network_device": recycle_bin_network_device_permissions,
        "recycle_bin_software": recycle_bin_software_permissions,
        "recycle_bin_certificate_key": recycle_bin_certificate_key_permissions,
        "recycle_bin_group": recycle_bin_group_permissions,
        "certificate_key": certificate_key_permissions,
    }

    # Role-permission mapping
    ROLE_PERMISSION_MAP = {
        "Super-Admin": {
            "user": ["read", "list", "create", "update", "delete"],
            "role": ["read", "list", "create", "update", "delete"],
            "group": ["read", "list", "create", "update", "delete", "purge"],
            "reference_data": ["read", "list", "create", "update", "delete"],
            "computer": ["read", "list", "create", "update", "delete"],
            "virtual_machine": ["read", "list", "create", "update", "delete"],
            "network_device": ["read", "list", "create", "update", "delete"],
            "software": ["read", "list", "create", "update", "delete"],
            "document": ["read", "list", "create", "update", "delete"],
            "compliance_scope": ["read", "list", "create", "update", "delete"],
            "asset": ["compliance_manage", "compliance_check"],
            "recycle_bin_user": ["read", "list", "restore", "purge"],
            "recycle_bin_computer": ["read", "list", "restore", "purge"],
            "recycle_bin_virtual_machine": ["read", "list", "restore", "purge"],
            "recycle_bin_network_device": ["read", "list", "restore", "purge"],
            "recycle_bin_software": ["read", "list", "restore", "purge"],
            "recycle_bin_certificate_key": ["read", "list", "restore", "purge"],
            "recycle_bin_group": ["read", "list", "restore", "purge"],
            "certificate_key": ["read", "list", "create", "update", "delete"],
        },
        "Admin": {
            "user": ["read", "list", "create", "update", "delete"],
            "role": ["read", "list"],
            "group": [],
            "reference_data": ["read", "list", "create", "update", "delete"],
            "computer": ["read", "list", "create", "update", "delete"],
            "virtual_machine": ["read", "list", "create", "update", "delete"],
            "network_device": ["read", "list", "create", "update", "delete"],
            "software": ["read", "list", "create", "update", "delete"],
            "document": ["read", "list", "create", "update", "delete"],
            "compliance_scope": ["read", "list", "create", "update", "delete"],
            "asset": ["compliance_manage", "compliance_check"],
            "recycle_bin_user": ["read", "list", "restore", "purge"],
            "recycle_bin_computer": ["read", "list", "restore", "purge"],
            "recycle_bin_virtual_machine": ["read", "list", "restore", "purge"],
            "recycle_bin_network_device": ["read", "list", "restore", "purge"],
            "recycle_bin_software": ["read", "list", "restore", "purge"],
            "recycle_bin_certificate_key": ["read", "list", "restore", "purge"],
            "recycle_bin_group": ["read", "list", "restore", "purge"],
            "certificate_key": ["read", "list", "create", "update", "delete"],
        },
        "Supervisor": {
            "user": ["read", "list", "create", "update"],
            "role": [],
            "group": [],
            "reference_data": [],
            "computer": ["read", "list", "create", "update"],
            "virtual_machine": ["read", "list", "create", "update"],
            "network_device": ["read", "list", "create", "update"],
            "software": ["read", "list", "create", "update"],
            "document": ["read", "list", "create", "update"],
            "compliance_scope": [],
            "recycle_bin_user": ["read", "list", "restore"],
            "recycle_bin_computer": ["read", "list", "restore"],
            "recycle_bin_virtual_machine": ["read", "list", "restore"],
            "recycle_bin_network_device": ["read", "list", "restore"],
            "recycle_bin_software": ["read", "list", "restore"],
            "recycle_bin_certificate_key": ["read", "list", "restore"],
            "recycle_bin_group": ["read", "list", "restore"],
            "certificate_key": ["read", "list", "create", "update"],
        },
        "Technician": {
            "user": ["read", "list", "update"],
            "role": [],
            "group": [],
            "reference_data": [],
            "computer": ["read", "list", "create", "update"],
            "virtual_machine": ["read", "list", "create", "update"],
            "network_device": ["read", "list", "create", "update"],
            "software": ["read", "list", "create", "update"],
            "document": ["read", "list", "create", "update"],
            "compliance_scope": [],
            "recycle_bin_user": [],
            "recycle_bin_computer": [],
            "recycle_bin_virtual_machine": [],
            "recycle_bin_network_device": [],
            "recycle_bin_software": [],
            "recycle_bin_certificate_key": [],
            "recycle_bin_group": [],
            "certificate_key": ["read", "list", "create", "update"],
        },
        "Hotliner": {
            "user": ["read", "list"],
            "role": [],
            "group": [],
            "reference_data": [],
            "computer": ["read", "list"],
            "virtual_machine": ["read", "list"],
            "network_device": ["read", "list"],
            "software": ["read", "list"],
            "document": ["read", "list"],
            "compliance_scope": ["read", "list"],
            "recycle_bin_user": [],
            "recycle_bin_computer": [],
            "recycle_bin_virtual_machine": [],
            "recycle_bin_network_device": [],
            "recycle_bin_software": [],
            "recycle_bin_certificate_key": [],
            "recycle_bin_group": [],
            "certificate_key": ["read", "list", "create", "update"],
        },
        "Observer": {
            "user": ["read", "list"],
            "role": [],
            "group": ["read", "list"],
            "reference_data": ["read", "list"],
            "computer": ["read", "list"],
            "virtual_machine": ["read", "list"],
            "network_device": ["read", "list"],
            "software": ["read", "list"],
            "document": ["read", "list"],
            "compliance_scope": ["read", "list"],
            "recycle_bin_user": [],
            "recycle_bin_computer": [],
            "recycle_bin_virtual_machine": [],
            "recycle_bin_network_device": [],
            "recycle_bin_software": [],
            "recycle_bin_certificate_key": [],
            "recycle_bin_group": [],
            "certificate_key": ["read", "list"],
        },
        "Self-Service": {
            "user": [],
            "role": [],
            "group": [],
            "reference_data": [],
            "computer": ["read", "list"],
            "virtual_machine": ["read", "list"],
            "network_device": ["read", "list"],
            "software": ["read", "list"],
            "document": [],
            "compliance_scope": [],
            "recycle_bin_user": [],
            "recycle_bin_computer": [],
            "recycle_bin_virtual_machine": [],
            "recycle_bin_network_device": [],
            "recycle_bin_software": [],
            "recycle_bin_certificate_key": [],
            "recycle_bin_group": [],
            "certificate_key": ["read", "list"],
        },
    }

    try:
        logger.info("Inserting preset roles...")
        for role_data in preset_roles:
            role = session.query(Role).filter_by(name=role_data["name"]).first()
            if not role:
                role = Role(**role_data)
                session.add(role)
        session.commit()
        logger.info("Preset roles inserted.")

        logger.info("Inserting all permissions...")
        for resource, permissions in ALL_PERMISSIONS.items():
            for perm_data in permissions:
                perm = (
                    session.query(Permission)
                    .filter_by(
                        action=perm_data["action"], resource=perm_data["resource"]
                    )
                    .first()
                )
                if not perm:
                    perm = Permission(**perm_data)
                    session.add(perm)
        session.commit()
        logger.info("All permissions inserted.")

        logger.info("Assigning permissions to roles...")
        for role_name, resource_map in ROLE_PERMISSION_MAP.items():
            role = session.query(Role).filter_by(name=role_name).first()
            if not role:
                logger.warning(
                    f"Role '{role_name}' not found, skipping permission assignment."
                )
                continue

            # Clear existing permissions to ensure a clean slate
            role.permissions.clear()

            for resource, actions in resource_map.items():
                for action in actions:
                    perm = (
                        session.query(Permission)
                        .filter_by(action=action, resource=resource)
                        .first()
                    )
                    if perm and perm not in role.permissions:
                        role.permissions.append(perm)
            session.add(role)
        session.commit()
        logger.info("Permissions assigned to roles.")

        logger.info("Assigning role management permissions to Super-Admin role...")
        super_admin_role = session.query(Role).filter_by(name="Super-Admin").first()
        if not super_admin_role:
            logger.error(
                "Super-Admin role not found. Skipping assignment of role management permissions."
            )
        else:
            for perm_data in role_permissions:
                perm = (
                    session.query(Permission)
                    .filter_by(
                        action=perm_data["action"], resource=perm_data["resource"]
                    )
                    .first()
                )
                if perm and perm not in super_admin_role.permissions:
                    super_admin_role.permissions.append(perm)
            session.add(super_admin_role)
            session.commit()
            logger.info("Role management permissions assigned to Super-Admin role.")

        logger.info("Assigning group management permissions to Super-Admin role...")
        super_admin_role = session.query(Role).filter_by(name="Super-Admin").first()
        if not super_admin_role:
            logger.error(
                "Super-Admin role not found. Skipping assignment of group management permissions."
            )
        else:
            for perm_data in group_permissions:
                perm = (
                    session.query(Permission)
                    .filter_by(
                        action=perm_data["action"], resource=perm_data["resource"]
                    )
                    .first()
                )
                if perm and perm not in super_admin_role.permissions:
                    super_admin_role.permissions.append(perm)
            session.add(super_admin_role)
            session.commit()
            logger.info("Group management permissions assigned to Super-Admin role.")

        # Create super-admin user if credentials provided
        if all([args.username, args.email, args.password]):
            create_super_admin_user(
                session, args.username, args.email, args.password, args.full_name
            )

        # Create test locations
        logger.info("Creating test locations if not exist...")
        for location_key, location_data in TEST_LOCATIONS.items():
            existing_location = (
                session.query(Location).filter_by(name=location_data["name"]).first()
            )
            if not existing_location:
                location = Location(**location_data)
                session.add(location)
        session.commit()
        logger.info("Test locations created.")

        # Create test manufacturers
        logger.info("Creating test manufacturers if not exist...")
        for manufacturer_key, manufacturer_data in TEST_MANUFACTURERS.items():
            existing_manufacturer = (
                session.query(Manufacturer)
                .filter_by(name=manufacturer_data["name"])
                .first()
            )
            if not existing_manufacturer:
                manufacturer = Manufacturer(**manufacturer_data)
                session.add(manufacturer)
        session.commit()
        logger.info("Test manufacturers created.")

        # Create compliance scopes
        logger.info("Creating compliance scopes if not exist...")
        preset_compliance_scopes = [
            {
                "name": "PCI-DSS",
                "description": "Payment Card Industry Data Security Standard for organizations that process cardholder data.",
                "reference_url": "https://www.pcisecuritystandards.org/",
            },
            {
                "name": "ISO 27001",
                "description": "International standard for establishing, implementing, maintaining, and continually improving an ISMS.",
                "reference_url": "https://www.iso.org/isoiec-27001-information-security.html",
            },
            {
                "name": "SOC 2",
                "description": "AICPA Trust Services Criteria-based attestation for security, availability, processing integrity, confidentiality, and privacy.",
                "reference_url": "https://www.aicpa.org/topic/audit-assurance/service-organization-reporting-soc",
            },
            {
                "name": "HIPAA",
                "description": "U.S. healthcare regulation for the protection of PHI (Protected Health Information).",
                "reference_url": "https://www.hhs.gov/hipaa/index.html",
            },
            {
                "name": "GDPR",
                "description": "EU General Data Protection Regulation governing personal data protection and privacy.",
                "reference_url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
            },
            {
                "name": "NIST CSF",
                "description": "NIST Cybersecurity Framework for improving critical infrastructure cybersecurity.",
                "reference_url": "https://www.nist.gov/cyberframework",
            },
            {
                "name": "NIST SP 800-53",
                "description": "NIST catalog of security and privacy controls for federal information systems and organizations.",
                "reference_url": "https://csrc.nist.gov/publications/sp800-53",
            },
            {
                "name": "FedRAMP",
                "description": "U.S. federal program for security assessment, authorization, and continuous monitoring of cloud services.",
                "reference_url": "https://www.fedramp.gov/",
            },
            {
                "name": "SOX",
                "description": "Sarbanes-Oxley Act requirements for financial reporting controls for U.S. public companies.",
                "reference_url": "https://www.sec.gov/about/laws/soa2002.pdf",
            },
        ]

        for scope_data in preset_compliance_scopes:
            existing_scope = (
                session.query(ComplianceScope)
                .filter_by(name=scope_data["name"])
                .first()
            )
            if not existing_scope:
                scope = ComplianceScope(**scope_data)
                session.add(scope)
        session.commit()
        logger.info("Compliance scopes created.")

        # Create sample assets
        create_sample_assets(session)

        # Create PCI-DSS v4.0 top-level requirements as controls
        logger.info("Creating PCI-DSS v4.0 controls if not exist...")
        pci_scope = session.query(ComplianceScope).filter_by(name="PCI-DSS").first()
        if pci_scope:
            # Add PCI-DSS document controls (French titles as per provided list)
            pci_document_controls = [
                {
                    "code": "DOC-001",
                    "title": "Politique Générale de Sécurité",
                    "description": "Politique de sécurité de l'information couvrant l'ensemble de l'organisation et le périmètre PCI.",
                    "required_document_name": "Politique Générale de Sécurité",
                    "required_document_type": "policy",
                },
                {
                    "code": "DOC-002",
                    "title": "Politique de sécurité réseau",
                    "description": "Politique encadrant la sécurité des réseaux, incluant segmentation CDE, filtrage et supervision.",
                    "required_document_name": "Politique de sécurité réseau",
                    "required_document_type": "policy",
                },
                {
                    "code": "DOC-003",
                    "title": "Politique antivirale",
                    "description": "Politique couvrant l'utilisation, la mise à jour et la surveillance des solutions anti‑malware.",
                    "required_document_name": "Politique antivirale",
                    "required_document_type": "policy",
                },
                {
                    "code": "DOC-004",
                    "title": "Document du périmètre PCI",
                    "description": "Description et justification du périmètre PCI DSS (CDE), incluant systèmes et flux concernés.",
                    "required_document_name": "Document du périmètre PCI",
                    "required_document_type": "document",
                },
                {
                    "code": "DOC-005",
                    "title": "Document des rôles et responsabilités",
                    "description": "Définition des rôles et responsabilités en matière de sécurité et de conformité PCI DSS.",
                    "required_document_name": "Document des rôles et responsabilités",
                    "required_document_type": "document",
                },
                {
                    "code": "DOC-006",
                    "title": "Méthodologie d'appréciation des risques",
                    "description": "Méthodologie de gestion des risques couvrant l'identification, l'évaluation et le traitement des risques PCI.",
                    "required_document_name": "Méthodologie d'appréciation des risques",
                    "required_document_type": "methodology",
                },
                {
                    "code": "DOC-007",
                    "title": "Cartographie des risques",
                    "description": "Cartographie/registre des risques identifiés et mesures associées pour le périmètre PCI.",
                    "required_document_name": "Cartographie des risques",
                    "required_document_type": "document",
                },
                {
                    "code": "DOC-008",
                    "title": "Politique/charte de développement sécurisé",
                    "description": "Politique et pratiques de développement sécurisé (SDLC) incluant revues de code et correctifs.",
                    "required_document_name": "Charte de développement sécurisé",
                    "required_document_type": "policy",
                },
                {
                    "code": "DOC-009",
                    "title": "Charte des administrateurs",
                    "description": "Charte d'utilisation et de sécurité pour les comptes et activités d'administration.",
                    "required_document_name": "Charte des administrateurs",
                    "required_document_type": "policy",
                },
                {
                    "code": "DOC-010",
                    "title": "Charte des utilisateurs du système",
                    "description": "Charte d'utilisation acceptable et règles de sécurité pour tous les utilisateurs.",
                    "required_document_name": "Charte des utilisateurs du système",
                    "required_document_type": "policy",
                },
                {
                    "code": "DOC-011",
                    "title": "Charte de conformité PCI DSS",
                    "description": "Engagements et responsabilités de l'organisation vis‑à‑vis de la conformité PCI DSS.",
                    "required_document_name": "Charte de conformité PCI DSS",
                    "required_document_type": "policy",
                },
                {
                    "code": "DOC-012",
                    "title": "Diagramme réseau",
                    "description": "Schéma réseau à jour incluant la segmentation et les flux vers/depuis le CDE.",
                    "required_document_name": "Diagramme réseau",
                    "required_document_type": "diagram",
                },
                {
                    "code": "DOC-013",
                    "title": "Diagramme de flux monétique",
                    "description": "Schéma détaillant les flux de données de carte (données PAN/CHD) au sein de l'environnement.",
                    "required_document_name": "Diagramme de flux monétique",
                    "required_document_type": "diagram",
                },
                {
                    "code": "DOC-014",
                    "title": "Standard de configuration des pare‑feu",
                    "description": "Standard de configuration sécurisée des pare‑feu incluant règles, justification et revue.",
                    "required_document_name": "Standard de configuration des pare‑feu",
                    "required_document_type": "standard",
                },
                {
                    "code": "DOC-015",
                    "title": "Standard de configuration des routeurs et commutateurs",
                    "description": "Standard de configuration sécurisée pour routeurs et switches.",
                    "required_document_name": "Standard de configuration des routeurs et commutateurs",
                    "required_document_type": "standard",
                },
                {
                    "code": "DOC-016",
                    "title": "Standard de configuration des systèmes (OS)",
                    "description": "Standards de durcissement des systèmes d'exploitation (serveurs et postes).",
                    "required_document_name": "Standard de configuration des systèmes (OS)",
                    "required_document_type": "standard",
                },
                {
                    "code": "DOC-017",
                    "title": "Standard de configuration des bases de données",
                    "description": "Standards de durcissement et règles d'accès pour SGBD.",
                    "required_document_name": "Standard de configuration des bases de données",
                    "required_document_type": "standard",
                },
                {
                    "code": "DOC-018",
                    "title": "Standard de configuration des serveurs applicatifs",
                    "description": "Standards de configuration sécurisée pour serveurs applicatifs/web.",
                    "required_document_name": "Standard de configuration des serveurs applicatifs",
                    "required_document_type": "standard",
                },
                {
                    "code": "DOC-019",
                    "title": "Standard de configuration des postes de travail",
                    "description": "Standard de configuration et de sécurité pour les postes utilisateurs.",
                    "required_document_name": "Standard de configuration des postes de travail",
                    "required_document_type": "standard",
                },
                {
                    "code": "DOC-020",
                    "title": "Procédure de gestion des logs",
                    "description": "Procédure de collecte, conservation, intégrité et revue des journaux de sécurité.",
                    "required_document_name": "Procédure de gestion des logs",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-021",
                    "title": "Inventaire des composants CDE",
                    "description": "Inventaire à jour des composants de l'environnement de données de cartes.",
                    "required_document_name": "Inventaire des composants CDE",
                    "required_document_type": "inventory",
                },
                {
                    "code": "DOC-022",
                    "title": "Inventaire des certificats et clés cryptographiques",
                    "description": "Inventaire et suivi des certificats, clés et matériels cryptographiques.",
                    "required_document_name": "Inventaire des certificats et clés cryptographiques",
                    "required_document_type": "inventory",
                },
                {
                    "code": "DOC-023",
                    "title": "Inventaire des applications",
                    "description": "Catalogue des applications (internes/externes) avec propriétaires et criticité.",
                    "required_document_name": "Inventaire des applications",
                    "required_document_type": "inventory",
                },
                {
                    "code": "DOC-024",
                    "title": "Procédure de gestion des identifiants",
                    "description": "Procédure couvrant création, attribution, révocation et rotation des identifiants.",
                    "required_document_name": "Procédure de gestion des identifiants",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-025",
                    "title": "Méthodologie des tests d'intrusion",
                    "description": "Méthodologie, périmètre et critères des tests d'intrusion périodiques.",
                    "required_document_name": "Méthodologie des tests d'intrusion",
                    "required_document_type": "methodology",
                },
                {
                    "code": "DOC-026",
                    "title": "Procédure de gestion des habilitations",
                    "description": "Procédure d'attribution, revue périodique et retrait des droits d'accès.",
                    "required_document_name": "Procédure de gestion des habilitations",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-027",
                    "title": "Processus de gestion des changements",
                    "description": "Processus ITSM de gestion des changements incluant évaluation des risques et approbations.",
                    "required_document_name": "Processus de gestion des changements",
                    "required_document_type": "process",
                },
                {
                    "code": "DOC-028",
                    "title": "Procédure de gestion des comptes",
                    "description": "Procédure de gestion du cycle de vie des comptes utilisateurs et techniques.",
                    "required_document_name": "Procédure de gestion des comptes",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-029",
                    "title": "Procédure de gestion des actifs",
                    "description": "Procédure d'inventaire, classification et suivi des actifs.",
                    "required_document_name": "Procédure de gestion des actifs",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-030",
                    "title": "Procédure d'authentification forte",
                    "description": "Procédure d'authentification multi‑facteurs et exigences associées.",
                    "required_document_name": "Procédure d'authentification forte",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-031",
                    "title": "Procédure de gestion des accès logiques",
                    "description": "Procédure d'octroi, de modification et de retrait des accès logiques.",
                    "required_document_name": "Procédure de gestion des accès logiques",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-032",
                    "title": "Procédure de gestion des accès distants",
                    "description": "Procédure encadrant les accès à distance sécurisés aux systèmes PCI.",
                    "required_document_name": "Procédure de gestion des accès distants",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-033",
                    "title": "Procédure de gestion des sauvegardes",
                    "description": "Procédure de sauvegarde/restauration, chiffrement et tests de restauration.",
                    "required_document_name": "Procédure de gestion des sauvegardes",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-034",
                    "title": "Procédure de réponse aux incidents de sécurité",
                    "description": "Procédure de détection, d'escalade, de traitement et de post‑mortem des incidents.",
                    "required_document_name": "Procédure de réponse aux incidents de sécurité",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-035",
                    "title": "Procédure de gestion des vulnérabilités",
                    "description": "Procédure de détection, priorisation et remédiation des vulnérabilités.",
                    "required_document_name": "Procédure de gestion des vulnérabilités",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-036",
                    "title": "Procédure de gestion des clés cryptographiques",
                    "description": "Procédure de génération, distribution, stockage, rotation et révocation des clés.",
                    "required_document_name": "Procédure de gestion des clés cryptographiques",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-037",
                    "title": "Procédure de gestion des prestataires",
                    "description": "Procédure d'évaluation et de suivi des fournisseurs/tiers avec accès PCI.",
                    "required_document_name": "Procédure de gestion des prestataires",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-038",
                    "title": "Procédure de gestion des accès physiques",
                    "description": "Procédure de contrôle et de surveillance des accès physiques aux locaux CDE.",
                    "required_document_name": "Procédure de gestion des accès physiques",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-039",
                    "title": "Procédure de mise en rebut des supports",
                    "description": "Procédure d'effacement sécurisé et de destruction des supports contenant des données de carte.",
                    "required_document_name": "Procédure de mise en rebut des supports",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-040",
                    "title": "Plan de continuité d'activité (PCA)",
                    "description": "Plan de continuité d'activité couvrant la résilience des services incluant PCI.",
                    "required_document_name": "Plan de continuité d'activité (PCA)",
                    "required_document_type": "plan",
                },
                {
                    "code": "DOC-041",
                    "title": "Procédure de reprise d'activité (PRA)",
                    "description": "Procédure/plan de reprise d'activité, objectifs RTO/RPO et scénarios.",
                    "required_document_name": "Procédure de reprise d'activité (PRA)",
                    "required_document_type": "procedure",
                },
                {
                    "code": "DOC-042",
                    "title": "Revue des règles des pare‑feu",
                    "description": "Compte‑rendu des revues périodiques des règles de filtrage et justifications.",
                    "required_document_name": "Revue des règles des pare‑feu",
                    "required_document_type": "record",
                },
                {
                    "code": "DOC-043",
                    "title": "PV de revue annuel des documents",
                    "description": "Procès‑verbal des revues annuelles des politiques, standards et procédures PCI.",
                    "required_document_name": "PV de revue annuel des documents",
                    "required_document_type": "record",
                },
            ]

            created_doc_controls = 0
            for ctrl in pci_document_controls:
                existing_ctrl = (
                    session.query(ComplianceControl)
                    .filter_by(scope_id=pci_scope.id, code=ctrl["code"])
                    .first()
                )
                if not existing_ctrl:
                    session.add(ComplianceControl(scope_id=pci_scope.id, **ctrl))
                    created_doc_controls += 1
            if created_doc_controls:
                session.commit()
                logger.info(
                    f"Created {created_doc_controls} PCI-DSS document controls."
                )
            else:
                logger.info(
                    "PCI-DSS document controls already present; no changes made."
                )
        else:
            logger.warning("PCI-DSS scope not found; skipping PCI controls creation.")

        # Create a user for each role if the database name contains 'dev'
        if "dev" in settings.DB_NAME.lower():
            logger.info(
                "Detected 'dev' in DB name, creating test users from test_data.py..."
            )
            for user_key, user_data in TEST_USERS.items():
                username = user_data["username"]
                email = user_data["email"]
                full_name = f"{user_data['role_name']} User"
                password = user_data["password"]
                role_name = user_data["role_name"]
                # Check if user already exists
                existing_user = (
                    session.query(User)
                    .filter((User.username == username) | (User.email == email))
                    .first()
                )
                if existing_user:
                    logger.info(
                        f"User for role '{role_name}' already exists: {username} / {email}"
                    )
                    continue
                role = session.query(Role).filter_by(name=role_name).first()
                if not role:
                    logger.warning(
                        f"Role '{role_name}' not found, skipping user creation for this role."
                    )
                    continue
                hashed_password = get_password_hash(password)
                user = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    hashed_password=hashed_password,
                    status="active",
                )
                user.role = role
                session.add(user)
                logger.info(
                    f"Created user for role '{role_name}': {username} / {email} (password: {password})"
                )
            session.commit()

        # Create example table configurations for user with ID=1
        logger.info("Creating example table configurations for user ID=1...")
        user_1 = session.query(User).filter_by(id=1).first()
        if user_1:
            # Create table config for users table
            existing_user_config = (
                session.query(TableConfig)
                .filter_by(user_id=1, table_key="users")
                .first()
            )
            if not existing_user_config:
                user_table_config = TableConfig(
                    user_id=1,
                    table_key="users",
                    columns=["id", "username", "email", "full_name"],
                )
                session.add(user_table_config)
                logger.info("Created table config for 'users' table")

            # Create table config for groups table
            existing_group_config = (
                session.query(TableConfig)
                .filter_by(user_id=1, table_key="groups")
                .first()
            )
            if not existing_group_config:
                group_table_config = TableConfig(
                    user_id=1,
                    table_key="groups",
                    columns=[
                        "id",
                        "name",
                        "description",
                        "type",
                        "contain_users",
                        "contain_items",
                    ],
                )
                session.add(group_table_config)
                logger.info("Created table config for 'groups' table")

            # Create table config for assets table
            existing_asset_config = (
                session.query(TableConfig)
                .filter_by(user_id=1, table_key="assets")
                .first()
            )
            if not existing_asset_config:
                asset_table_config = TableConfig(
                    user_id=1,
                    table_key="assets",
                    columns=[
                        "id",
                        "name",
                        "type",
                        "status",
                        "serial_number",
                        "inventory_number",
                        "location_id",
                        "assigned_to",
                    ],
                )
                session.add(asset_table_config)
                logger.info("Created table config for 'assets' table")

            session.commit()
            logger.info("Example table configurations created successfully.")
        else:
            logger.warning("User with ID=1 not found, skipping table config creation.")

    except IntegrityError as e:
        session.rollback()
        logger.error(f"Integrity error occurred during seeding: {e}")
        sys.exit(1)
    finally:
        session.close()

    logger.info("Seeding complete.")


if __name__ == "__main__":
    main()
