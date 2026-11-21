import argparse
import sys
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.logger import logger
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import (
    ComplianceControl,
    ComplianceEvent,
    ComplianceScope,
    Location,
    Manufacturer,
    OperatingSystem,
    Permission,
    Role,
    TableConfig,
    User,
)
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
    parser.add_argument(
        "--skip-fixtures",
        action="store_true",
        help=(
            "Skip test/demo locations, manufacturers, operating systems, assets, "
            "and development test users"
        ),
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
    operating_systems = session.query(OperatingSystem).all()
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
            "operating_system_id": (
                operating_systems[0].id if operating_systems else None
            ),
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
            "operating_system_id": (
                operating_systems[1].id if operating_systems else None
            ),
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
            "operating_system_id": (
                operating_systems[9].id if operating_systems else None
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


def create_operating_systems(session):
    """Seed common operating systems (Windows and Linux variants)."""
    logger.info("Creating operating systems if not exist...")
    from tests.test_data import TEST_OPERATING_SYSTEMS

    created = 0
    for os_key, os_data in TEST_OPERATING_SYSTEMS.items():
        existing = (
            session.query(OperatingSystem)
            .filter_by(name=os_data["name"], version=os_data["version"])
            .first()  # unique on (name, version)
        )
        if not existing:
            session.add(OperatingSystem(**os_data))
            logger.info(f"Created operating system: {os_key}")
            created += 1

    if created:
        session.commit()
        logger.info(f"Created {created} operating systems")
    else:
        logger.info("Operating systems already present; no changes made.")


def upsert_document_controls_for_scope(session, scope, controls, scope_name):
    """Create or update document controls for a given compliance scope.

    - Creates controls that are missing
    - Backfills/corrects review_frequency_months for existing ones
    """
    created = 0
    updated = 0
    for ctrl in controls:
        existing_ctrl = (
            session.query(ComplianceControl)
            .filter_by(scope_id=scope.id, code=ctrl["code"])
            .first()
        )
        if not existing_ctrl:
            session.add(ComplianceControl(scope_id=scope.id, **ctrl))
            created += 1
        else:
            desired_freq = ctrl.get("review_frequency_months")
            if (
                desired_freq is not None
                and existing_ctrl.review_frequency_months != desired_freq
            ):
                existing_ctrl.review_frequency_months = desired_freq
                updated += 1

    if created or updated:
        session.commit()
        logger.info(
            f"Created {created} and updated {updated} {scope_name} document controls."
        )
    else:
        logger.info(f"{scope_name} document controls already present; no changes made.")


def create_compliance_events_for_scope(session, scope, events, scope_name):
    """Create compliance events for a given compliance scope.

    - Creates events that are missing (based on name uniqueness within scope)
    - Skips events that already exist
    """
    created = 0
    for event_data in events:
        existing_event = (
            session.query(ComplianceEvent)
            .filter_by(scope_id=scope.id, name=event_data["name"])
            .first()
        )
        if not existing_event:
            # Calculate next_due_date if frequency is provided
            if event_data.get("frequency") and not event_data.get("next_due_date"):
                today = date.today()
                freq = event_data["frequency"]
                if freq == "yearly":
                    event_data["next_due_date"] = today + timedelta(days=365)
                elif freq == "semi-annually":
                    event_data["next_due_date"] = today + timedelta(days=180)
                elif freq == "quarterly":
                    event_data["next_due_date"] = today + timedelta(days=90)
                elif freq == "monthly":
                    event_data["next_due_date"] = today + timedelta(days=30)

            session.add(ComplianceEvent(scope_id=scope.id, **event_data))
            created += 1

    if created:
        session.commit()
        logger.info(f"Created {created} {scope_name} compliance events.")
    else:
        logger.info(f"{scope_name} compliance events already present; no changes made.")


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
        {
            "name": "system_cronjob",
            "description": "Role for system cronjob operations",
            "is_builtin": True,
            "rank": 99,
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

    # 6a. manufacturer management permissions
    manufacturer_permissions = [
        {
            "action": "read",
            "resource": "manufacturer",
            "description": "View manufacturer information",
        },
        {
            "action": "list",
            "resource": "manufacturer",
            "description": "List manufacturers",
        },
        {
            "action": "create",
            "resource": "manufacturer",
            "description": "Create new manufacturers",
        },
        {
            "action": "update",
            "resource": "manufacturer",
            "description": "Update manufacturer information",
        },
        {
            "action": "delete",
            "resource": "manufacturer",
            "description": "Delete manufacturers",
        },
        {
            "action": "purge",
            "resource": "manufacturer",
            "description": "Permanently delete manufacturers",
        },
    ]

    # 6b. location management permissions
    location_permissions = [
        {
            "action": "read",
            "resource": "location",
            "description": "View location information",
        },
        {
            "action": "list",
            "resource": "location",
            "description": "List locations",
        },
        {
            "action": "create",
            "resource": "location",
            "description": "Create new locations",
        },
        {
            "action": "update",
            "resource": "location",
            "description": "Update location information",
        },
        {
            "action": "delete",
            "resource": "location",
            "description": "Delete locations",
        },
        {
            "action": "purge",
            "resource": "location",
            "description": "Permanently delete locations",
        },
    ]

    # 6c. operating system management permissions
    operating_system_permissions = [
        {
            "action": "read",
            "resource": "operating_system",
            "description": "View operating system information",
        },
        {
            "action": "list",
            "resource": "operating_system",
            "description": "List operating systems",
        },
        {
            "action": "create",
            "resource": "operating_system",
            "description": "Create new operating systems",
        },
        {
            "action": "update",
            "resource": "operating_system",
            "description": "Update operating system information",
        },
        {
            "action": "delete",
            "resource": "operating_system",
            "description": "Delete operating systems",
        },
        {
            "action": "purge",
            "resource": "operating_system",
            "description": "Permanently delete operating systems",
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

    analytics_permissions = [
        {
            "action": "list",
            "resource": "analytics",
            "description": "List analytics",
        },
    ]

    data_register_permissions = [
        {
            "action": "read",
            "resource": "data_register",
            "description": "View data register",
        },
        {
            "action": "list",
            "resource": "data_register",
            "description": "List data register",
        },
        {
            "action": "create",
            "resource": "data_register",
            "description": "Create data register",
        },
        {
            "action": "update",
            "resource": "data_register",
            "description": "Update data register",
        },
        {
            "action": "delete",
            "resource": "data_register",
            "description": "Delete data register",
        },
    ]

    api_keys_permissions = [
        {
            "action": "list",
            "resource": " api_key",
            "description": "List API keys",
        },
        {
            "action": "create",
            "resource": " api_key",
            "description": "Create API keys",
        },
        {
            "action": "delete",
            "resource": " api_key",
            "description": "Delete API keys",
        },
    ]

    compliance_event_permissions = [
        {
            "action": "read",
            "resource": "compliance_event",
            "description": "View compliance events",
        },
        {
            "action": "list",
            "resource": "compliance_event",
            "description": "List compliance events",
        },
        {
            "action": "create",
            "resource": "compliance_event",
            "description": "Create compliance events",
        },
        {
            "action": "update",
            "resource": "compliance_event",
            "description": "Update compliance events",
        },
        {
            "action": "delete",
            "resource": "compliance_event",
            "description": "Delete compliance events",
        },
    ]

    ALL_PERMISSIONS = {
        "user": user_permissions,
        "role": role_permissions,
        "group": group_permissions,
        "manufacturer": manufacturer_permissions,
        "location": location_permissions,
        "operating_system": operating_system_permissions,
        "computer": computer_permissions,
        "virtual_machine": virtual_machine_permissions,
        "network_device": network_device_permissions,
        "software": software_permissions,
        "document": document_permissions,
        "compliance_scope": compliance_scope_permissions,
        "compliance_event": compliance_event_permissions,
        "asset": asset_compliance_permissions,
        "recycle_bin_user": recycle_bin_user_permissions,
        "recycle_bin_computer": recycle_bin_computer_permissions,
        "recycle_bin_virtual_machine": recycle_bin_virtual_machine_permissions,
        "recycle_bin_network_device": recycle_bin_network_device_permissions,
        "recycle_bin_software": recycle_bin_software_permissions,
        "recycle_bin_certificate_key": recycle_bin_certificate_key_permissions,
        "recycle_bin_group": recycle_bin_group_permissions,
        "certificate_key": certificate_key_permissions,
        "analytics": analytics_permissions,
        "data_register": data_register_permissions,
        "api_key": api_keys_permissions,
    }

    # Role-permission mapping
    ROLE_PERMISSION_MAP = {
        "system_cronjob": {
            "analytics": ["list"],
        },
        "Super-Admin": {
            "user": ["read", "list", "create", "update", "delete"],
            "role": ["read", "list", "create", "update", "delete"],
            "group": ["read", "list", "create", "update", "delete", "purge"],
            "manufacturer": ["read", "list", "create", "update", "delete"],
            "location": ["read", "list", "create", "update", "delete"],
            "operating_system": ["read", "list", "create", "update", "delete"],
            "computer": ["read", "list", "create", "update", "delete"],
            "virtual_machine": ["read", "list", "create", "update", "delete"],
            "network_device": ["read", "list", "create", "update", "delete"],
            "software": ["read", "list", "create", "update", "delete"],
            "document": ["read", "list", "create", "update", "delete"],
            "compliance_scope": ["read", "list", "create", "update", "delete"],
            "compliance_event": ["read", "list", "create", "update", "delete"],
            "asset": ["compliance_manage", "compliance_check"],
            "recycle_bin_user": ["read", "list", "restore", "purge"],
            "recycle_bin_computer": ["read", "list", "restore", "purge"],
            "recycle_bin_virtual_machine": ["read", "list", "restore", "purge"],
            "recycle_bin_network_device": ["read", "list", "restore", "purge"],
            "recycle_bin_software": ["read", "list", "restore", "purge"],
            "recycle_bin_certificate_key": ["read", "list", "restore", "purge"],
            "recycle_bin_group": ["read", "list", "restore", "purge"],
            "certificate_key": ["read", "list", "create", "update", "delete"],
            "analytics": ["list"],
            "data_register": ["read", "list", "create", "update", "delete"],
            "api_key": ["list", "create", "delete"],
        },
        "Admin": {
            "user": ["read", "list", "create", "update", "delete"],
            "role": ["read", "list"],
            "group": [],
            "manufacturer": ["read", "list", "create", "update", "delete"],
            "location": ["read", "list", "create", "update", "delete"],
            "operating_system": ["read", "list", "create", "update", "delete"],
            "computer": ["read", "list", "create", "update", "delete"],
            "virtual_machine": ["read", "list", "create", "update", "delete"],
            "network_device": ["read", "list", "create", "update", "delete"],
            "software": ["read", "list", "create", "update", "delete"],
            "document": ["read", "list", "create", "update", "delete"],
            "compliance_scope": ["read", "list", "create", "update", "delete"],
            "compliance_event": ["read", "list", "create", "update", "delete"],
            "asset": ["compliance_manage", "compliance_check"],
            "recycle_bin_user": ["read", "list", "restore", "purge"],
            "recycle_bin_computer": ["read", "list", "restore", "purge"],
            "recycle_bin_virtual_machine": ["read", "list", "restore", "purge"],
            "recycle_bin_network_device": ["read", "list", "restore", "purge"],
            "recycle_bin_software": ["read", "list", "restore", "purge"],
            "recycle_bin_certificate_key": ["read", "list", "restore", "purge"],
            "recycle_bin_group": ["read", "list", "restore", "purge"],
            "certificate_key": ["read", "list", "create", "update", "delete"],
            "analytics": ["list"],
            
        },
        "Supervisor": {
            "user": ["read", "list", "create", "update"],
            "role": [],
            "group": [],
            "manufacturer": ["read", "list"],
            "location": ["read", "list"],
            "operating_system": ["read", "list"],
            "computer": ["read", "list", "create", "update"],
            "virtual_machine": ["read", "list", "create", "update"],
            "network_device": ["read", "list", "create", "update"],
            "software": ["read", "list", "create", "update"],
            "document": ["read", "list", "create", "update"],
            "compliance_scope": [],
            "compliance_event": [],
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
            "manufacturer": ["read", "list"],
            "location": ["read", "list"],
            "operating_system": ["read", "list"],
            "computer": ["read", "list", "create", "update"],
            "virtual_machine": ["read", "list", "create", "update"],
            "network_device": ["read", "list", "create", "update"],
            "software": ["read", "list", "create", "update"],
            "document": ["read", "list", "create", "update"],
            "compliance_scope": [],
            "compliance_event": [],
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
            "manufacturer": ["read", "list"],
            "location": ["read", "list"],
            "operating_system": ["read", "list"],
            "computer": ["read", "list"],
            "virtual_machine": ["read", "list"],
            "network_device": ["read", "list"],
            "software": ["read", "list"],
            "document": ["read", "list"],
            "compliance_scope": ["read", "list"],
            "compliance_event": ["read", "list"],
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
            "manufacturer": ["read", "list"],
            "location": ["read", "list"],
            "operating_system": ["read", "list"],
            "computer": ["read", "list"],
            "virtual_machine": ["read", "list"],
            "network_device": ["read", "list"],
            "software": ["read", "list"],
            "document": ["read", "list"],
            "compliance_scope": ["read", "list"],
            "compliance_event": ["read", "list"],
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
            "manufacturer": ["read", "list"],
            "location": ["read", "list"],
            "operating_system": ["read", "list"],
            "computer": ["read", "list"],
            "virtual_machine": ["read", "list"],
            "network_device": ["read", "list"],
            "software": ["read", "list"],
            "document": [],
            "compliance_scope": [],
            "compliance_event": [],
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

        if not args.skip_fixtures:
            # Create test locations
            logger.info("Creating test locations if not exist...")
            for location_data in TEST_LOCATIONS.values():
                existing_location = (
                    session.query(Location)
                    .filter_by(name=location_data["name"])
                    .first()
                )
                if not existing_location:
                    location = Location(**location_data)
                    session.add(location)
            session.commit()
            logger.info("Test locations created.")

            # Create test manufacturers
            logger.info("Creating test manufacturers if not exist...")
            for manufacturer_data in TEST_MANUFACTURERS.values():
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

            create_operating_systems(session)
        else:
            logger.info("Skipping test/demo fixture creation.")

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
                "name": "NDSSI",
                "description": "Directive nationale de la sécurité des systèmes d’information",
                "reference_url": "https://www.dgssi.gov.ma/fr/publications/directive-nationale-de-la-securite-des-systemes-dinformation-dnssi",
            },
            {
                "name": "ISO 22301",
                "description": "International standard for business continuity management systems.",
                "reference_url": "https://www.iso.org/standard/57460.html",
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

        if not args.skip_fixtures:
            create_sample_assets(session)

        # Create PCI-DSS v4.0 compliance events
        logger.info("Creating PCI-DSS v4.0 compliance events if not exist...")
        pci_scope = session.query(ComplianceScope).filter_by(name="PCI-DSS").first()
        if pci_scope:
            pci_compliance_events = [
                {
                    "name": "Date de début du projet de certification",
                    "description": "Date officielle de démarrage du projet de mise en conformité PCI-DSS",
                    "frequency": None,  # One-time event
                    "notify": False,
                    "remind_before_days": 30,
                    "notes": "Événement unique marquant le début du projet de certification PCI-DSS",
                },
                {
                    "name": "Audit de certification PCI-DSS",
                    "description": "Audit annuel de certification PCI-DSS par un QSA (Qualified Security Assessor) ou auto-évaluation SAQ",
                    "frequency": "yearly",
                    "notify": True,
                    "remind_before_days": 60,
                    "notes": "Audit obligatoire pour maintenir la certification PCI-DSS. Prévoir 2 mois de préparation.",
                },
                {
                    "name": "Revue de périmètre PCI-DSS",
                    "description": "Revue annuelle du périmètre CDE (Cardholder Data Environment) et validation de la segmentation réseau",
                    "frequency": "yearly",
                    "notify": True,
                    "remind_before_days": 30,
                    "notes": "Exigence 12.5.2 - Documenter et valider le périmètre PCI-DSS et la segmentation annuellement",
                },
                {
                    "name": "Test d'intrusion interne",
                    "description": "Pentest interne du périmètre CDE pour identifier les vulnérabilités internes (Exigence 11.4.1)",
                    "frequency": "yearly",
                    "notify": True,
                    "remind_before_days": 45,
                    "notes": "Exigence 11.4 - Test d'intrusion annuel obligatoire de l'infrastructure interne. Inclure tests de segmentation.",
                },
                {
                    "name": "Test d'intrusion externe",
                    "description": "Pentest externe des systèmes exposés à Internet dans le périmètre PCI (Exigence 11.4.2)",
                    "frequency": "yearly",
                    "notify": True,
                    "remind_before_days": 45,
                    "notes": "Exigence 11.4 - Test d'intrusion externe annuel obligatoire par un testeur qualifié",
                },
                {
                    "name": "Revue des règles de pare-feu",
                    "description": "Revue semestrielle des règles de pare-feu et routeurs pour valider leur pertinence (Exigence 1.2.7)",
                    "frequency": "semi-annually",
                    "notify": True,
                    "remind_before_days": 21,
                    "notes": "Exigence 1.2.7 - Revue obligatoire tous les 6 mois de toutes les règles de filtrage avec justification",
                },
                {
                    "name": "Scan de vulnérabilités interne",
                    "description": "Scan trimestriel de vulnérabilités des systèmes internes du périmètre CDE (Exigence 11.3.1)",
                    "frequency": "quarterly",
                    "notify": True,
                    "remind_before_days": 14,
                    "notes": "Exigence 11.3.1 - Scans trimestriels obligatoires avec remédiation des vulnérabilités critiques/élevées",
                },
                {
                    "name": "Scan ASV (Approved Scanning Vendor)",
                    "description": "Scan trimestriel externe par un ASV approuvé PCI SSC des systèmes exposés à Internet (Exigence 11.3.2)",
                    "frequency": "quarterly",
                    "notify": True,
                    "remind_before_days": 14,
                    "notes": "Exigence 11.3.2 - Scans ASV trimestriels obligatoires pour tous les systèmes publics. Résultat 'Passing' requis.",
                },
                {
                    "name": "Revue des accès utilisateurs",
                    "description": "Revue trimestrielle des comptes et habilitations d'accès au CDE (Exigence 8.2.4)",
                    "frequency": "quarterly",
                    "notify": True,
                    "remind_before_days": 14,
                    "notes": "Exigence 8.2.4 - Validation trimestrielle que les accès sont appropriés et conformes au principe du moindre privilège",
                },
                {
                    "name": "Revue des journaux d'événements",
                    "description": "Revue quotidienne des journaux de sécurité et d'audit des systèmes critiques (Exigence 10.6)",
                    "frequency": "monthly",
                    "notify": True,
                    "remind_before_days": 7,
                    "notes": "Exigence 10.6 - Revue quotidienne ou hebdomadaire des logs selon criticité. Documenter les résultats.",
                },
                {
                    "name": "Test de restauration des sauvegardes",
                    "description": "Test annuel de restauration des sauvegardes critiques incluant les données du CDE (Exigence 10.5.1)",
                    "frequency": "yearly",
                    "notify": True,
                    "remind_before_days": 30,
                    "notes": "Exigence 10.5.1 - Vérifier au moins annuellement que les sauvegardes sont fonctionnelles et restaurables",
                },
                {
                    "name": "Formation de sensibilisation à la sécurité",
                    "description": "Formation annuelle obligatoire de sensibilisation PCI-DSS pour tout le personnel (Exigence 12.6)",
                    "frequency": "yearly",
                    "notify": True,
                    "remind_before_days": 45,
                    "notes": "Exigence 12.6 - Formation annuelle sur les politiques de sécurité et les procédures pour tous les employés",
                },
                {
                    "name": "Revue des politiques et procédures",
                    "description": "Revue annuelle de toutes les politiques et procédures de sécurité (Exigence 12.1.1)",
                    "frequency": "yearly",
                    "notify": True,
                    "remind_before_days": 30,
                    "notes": "Exigence 12.1.1 - Revue et approbation annuelle de la politique de sécurité par la direction",
                },
                {
                    "name": "Inventaire des actifs du CDE",
                    "description": "Mise à jour de l'inventaire complet des composants système dans le périmètre PCI (Exigence 2.4)",
                    "frequency": "quarterly",
                    "notify": True,
                    "remind_before_days": 14,
                    "notes": "Exigence 2.4 - Maintenir un inventaire à jour de tous les composants système dans le périmètre",
                },
                {
                    "name": "Revue des comptes privilégiés",
                    "description": "Revue trimestrielle de tous les comptes administrateurs et à privilèges (Exigence 7.2.4)",
                    "frequency": "quarterly",
                    "notify": True,
                    "remind_before_days": 14,
                    "notes": "Exigence 7.2.4 - Valider que les privilèges d'administration sont justifiés et nécessaires",
                },
                {
                    "name": "Test du plan de réponse aux incidents",
                    "description": "Test annuel du plan de réponse aux incidents de sécurité (Exigence 12.10.4)",
                    "frequency": "yearly",
                    "notify": True,
                    "remind_before_days": 30,
                    "notes": "Exigence 12.10.4 - Exercice annuel de simulation d'incident pour tester les procédures de réponse",
                },
                {
                    "name": "Évaluation des risques formelle",
                    "description": "Évaluation annuelle des risques selon la méthodologie documentée (Exigence 12.3.1)",
                    "frequency": "yearly",
                    "notify": True,
                    "remind_before_days": 45,
                    "notes": "Exigence 12.3.1 - Analyse de risque annuelle incluant menaces, vulnérabilités et impact",
                },
                {
                    "name": "Revue de la détection d'intrusion (IDS/IPS)",
                    "description": "Mise à jour et test des systèmes de détection/prévention d'intrusion (Exigence 11.5)",
                    "frequency": "quarterly",
                    "notify": True,
                    "remind_before_days": 14,
                    "notes": "Exigence 11.5 - Maintenir à jour les signatures et tester régulièrement l'efficacité des IDS/IPS",
                },
                {
                    "name": "Validation de la segmentation réseau",
                    "description": "Test semestriel de la segmentation réseau pour valider l'isolation du CDE (Exigence 11.4.3)",
                    "frequency": "semi-annually",
                    "notify": True,
                    "remind_before_days": 21,
                    "notes": "Exigence 11.4.3 - Tests de segmentation pour confirmer que le CDE est isolé des autres réseaux",
                },
            ]

            create_compliance_events_for_scope(
                session, pci_scope, pci_compliance_events, "PCI-DSS"
            )
        else:
            logger.warning("PCI-DSS scope not found; skipping PCI events creation.")

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
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-002",
                    "title": "Politique de sécurité réseau",
                    "description": "Politique encadrant la sécurité des réseaux, incluant segmentation CDE, filtrage et supervision.",
                    "required_document_name": "Politique de sécurité réseau",
                    "required_document_type": "policy",
                    "review_frequency_months": 6,
                },
                {
                    "code": "DOC-003",
                    "title": "Politique antivirale",
                    "description": "Politique couvrant l'utilisation, la mise à jour et la surveillance des solutions anti‑malware.",
                    "required_document_name": "Politique antivirale",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-004",
                    "title": "Document du périmètre PCI",
                    "description": "Description et justification du périmètre PCI DSS (CDE), incluant systèmes et flux concernés.",
                    "required_document_name": "Document du périmètre PCI",
                    "required_document_type": "document",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-005",
                    "title": "Document des rôles et responsabilités",
                    "description": "Définition des rôles et responsabilités en matière de sécurité et de conformité PCI DSS.",
                    "required_document_name": "Document des rôles et responsabilités",
                    "required_document_type": "document",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-006",
                    "title": "Méthodologie d'appréciation des risques",
                    "description": "Méthodologie de gestion des risques couvrant l'identification, l'évaluation et le traitement des risques PCI.",
                    "required_document_name": "Méthodologie d'appréciation des risques",
                    "required_document_type": "methodology",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-007",
                    "title": "Cartographie des risques",
                    "description": "Cartographie/registre des risques identifiés et mesures associées pour le périmètre PCI.",
                    "required_document_name": "Cartographie des risques",
                    "required_document_type": "document",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-008",
                    "title": "Politique/charte de développement sécurisé",
                    "description": "Politique et pratiques de développement sécurisé (SDLC) incluant revues de code et correctifs.",
                    "required_document_name": "Charte de développement sécurisé",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-009",
                    "title": "Charte des administrateurs",
                    "description": "Charte d'utilisation et de sécurité pour les comptes et activités d'administration.",
                    "required_document_name": "Charte des administrateurs",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-010",
                    "title": "Charte des utilisateurs du système",
                    "description": "Charte d'utilisation acceptable et règles de sécurité pour tous les utilisateurs.",
                    "required_document_name": "Charte des utilisateurs du système",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-011",
                    "title": "Charte de conformité PCI DSS",
                    "description": "Engagements et responsabilités de l'organisation vis‑à‑vis de la conformité PCI DSS.",
                    "required_document_name": "Charte de conformité PCI DSS",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-012",
                    "title": "Diagramme réseau",
                    "description": "Schéma réseau à jour incluant la segmentation et les flux vers/depuis le CDE.",
                    "required_document_name": "Diagramme réseau",
                    "required_document_type": "diagram",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-013",
                    "title": "Diagramme de flux monétique",
                    "description": "Schéma détaillant les flux de données de carte (données PAN/CHD) au sein de l'environnement.",
                    "required_document_name": "Diagramme de flux monétique",
                    "required_document_type": "diagram",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-014",
                    "title": "Standard de configuration des pare‑feu",
                    "description": "Standard de configuration sécurisée des pare‑feu incluant règles, justification et revue.",
                    "required_document_name": "Standard de configuration des pare‑feu",
                    "required_document_type": "standard",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-015",
                    "title": "Standard de configuration des routeurs et commutateurs",
                    "description": "Standard de configuration sécurisée pour routeurs et switches.",
                    "required_document_name": "Standard de configuration des routeurs et commutateurs",
                    "required_document_type": "standard",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-016",
                    "title": "Standard de configuration des systèmes (OS)",
                    "description": "Standards de durcissement des systèmes d'exploitation (serveurs et postes).",
                    "required_document_name": "Standard de configuration des systèmes (OS)",
                    "required_document_type": "standard",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-017",
                    "title": "Standard de configuration des bases de données",
                    "description": "Standards de durcissement et règles d'accès pour SGBD.",
                    "required_document_name": "Standard de configuration des bases de données",
                    "required_document_type": "standard",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-018",
                    "title": "Standard de configuration des serveurs applicatifs",
                    "description": "Standards de configuration sécurisée pour serveurs applicatifs/web.",
                    "required_document_name": "Standard de configuration des serveurs applicatifs",
                    "required_document_type": "standard",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-019",
                    "title": "Standard de configuration des postes de travail",
                    "description": "Standard de configuration et de sécurité pour les postes utilisateurs.",
                    "required_document_name": "Standard de configuration des postes de travail",
                    "required_document_type": "standard",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-020",
                    "title": "Procédure de gestion des logs",
                    "description": "Procédure de collecte, conservation, intégrité et revue des journaux de sécurité.",
                    "required_document_name": "Procédure de gestion des logs",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-021",
                    "title": "Inventaire des composants CDE",
                    "description": "Inventaire à jour des composants de l'environnement de données de cartes.",
                    "required_document_name": "Inventaire des composants CDE",
                    "required_document_type": "inventory",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-022",
                    "title": "Inventaire des certificats et clés cryptographiques",
                    "description": "Inventaire et suivi des certificats, clés et matériels cryptographiques.",
                    "required_document_name": "Inventaire des certificats et clés cryptographiques",
                    "required_document_type": "inventory",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-023",
                    "title": "Inventaire des applications",
                    "description": "Catalogue des applications (internes/externes) avec propriétaires et criticité.",
                    "required_document_name": "Inventaire des applications",
                    "required_document_type": "inventory",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-024",
                    "title": "Procédure de gestion des identifiants",
                    "description": "Procédure couvrant création, attribution, révocation et rotation des identifiants.",
                    "required_document_name": "Procédure de gestion des identifiants",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-025",
                    "title": "Méthodologie des tests d'intrusion",
                    "description": "Méthodologie, périmètre et critères des tests d'intrusion périodiques.",
                    "required_document_name": "Méthodologie des tests d'intrusion",
                    "required_document_type": "methodology",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-026",
                    "title": "Procédure de gestion des habilitations",
                    "description": "Procédure d'attribution, revue périodique et retrait des droits d'accès.",
                    "required_document_name": "Procédure de gestion des habilitations",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-027",
                    "title": "Processus de gestion des changements",
                    "description": "Processus ITSM de gestion des changements incluant évaluation des risques et approbations.",
                    "required_document_name": "Processus de gestion des changements",
                    "required_document_type": "process",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-028",
                    "title": "Procédure de gestion des comptes",
                    "description": "Procédure de gestion du cycle de vie des comptes utilisateurs et techniques.",
                    "required_document_name": "Procédure de gestion des comptes",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-029",
                    "title": "Procédure de gestion des actifs",
                    "description": "Procédure d'inventaire, classification et suivi des actifs.",
                    "required_document_name": "Procédure de gestion des actifs",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-030",
                    "title": "Procédure d'authentification forte",
                    "description": "Procédure d'authentification multi‑facteurs et exigences associées.",
                    "required_document_name": "Procédure d'authentification forte",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-031",
                    "title": "Procédure de gestion des accès logiques",
                    "description": "Procédure d'octroi, de modification et de retrait des accès logiques.",
                    "required_document_name": "Procédure de gestion des accès logiques",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-032",
                    "title": "Procédure de gestion des accès distants",
                    "description": "Procédure encadrant les accès à distance sécurisés aux systèmes PCI.",
                    "required_document_name": "Procédure de gestion des accès distants",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-033",
                    "title": "Procédure de gestion des sauvegardes",
                    "description": "Procédure de sauvegarde/restauration, chiffrement et tests de restauration.",
                    "required_document_name": "Procédure de gestion des sauvegardes",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-034",
                    "title": "Procédure de réponse aux incidents de sécurité",
                    "description": "Procédure de détection, d'escalade, de traitement et de post‑mortem des incidents.",
                    "required_document_name": "Procédure de réponse aux incidents de sécurité",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-035",
                    "title": "Procédure de gestion des vulnérabilités",
                    "description": "Procédure de détection, priorisation et remédiation des vulnérabilités.",
                    "required_document_name": "Procédure de gestion des vulnérabilités",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-036",
                    "title": "Procédure de gestion des clés cryptographiques",
                    "description": "Procédure de génération, distribution, stockage, rotation et révocation des clés.",
                    "required_document_name": "Procédure de gestion des clés cryptographiques",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-037",
                    "title": "Procédure de gestion des prestataires",
                    "description": "Procédure d'évaluation et de suivi des fournisseurs/tiers avec accès PCI.",
                    "required_document_name": "Procédure de gestion des prestataires",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-038",
                    "title": "Procédure de gestion des accès physiques",
                    "description": "Procédure de contrôle et de surveillance des accès physiques aux locaux CDE.",
                    "required_document_name": "Procédure de gestion des accès physiques",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-039",
                    "title": "Procédure de mise en rebut des supports",
                    "description": "Procédure d'effacement sécurisé et de destruction des supports contenant des données de carte.",
                    "required_document_name": "Procédure de mise en rebut des supports",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-040",
                    "title": "Plan de continuité d'activité (PCA)",
                    "description": "Plan de continuité d'activité couvrant la résilience des services incluant PCI.",
                    "required_document_name": "Plan de continuité d'activité (PCA)",
                    "required_document_type": "plan",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-041",
                    "title": "Procédure de reprise d'activité (PRA)",
                    "description": "Procédure/plan de reprise d'activité, objectifs RTO/RPO et scénarios.",
                    "required_document_name": "Procédure de reprise d'activité (PRA)",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "DOC-042",
                    "title": "Revue des règles des pare‑feu",
                    "description": "Compte‑rendu des revues périodiques des règles de filtrage et justifications.",
                    "required_document_name": "Revue des règles des pare‑feu",
                    "required_document_type": "record",
                    "review_frequency_months": 6,
                },
                {
                    "code": "DOC-043",
                    "title": "PV de revue annuel des documents",
                    "description": "Procès‑verbal des revues annuelles des politiques, standards et procédures PCI.",
                    "required_document_name": "PV de revue annuel des documents",
                    "required_document_type": "record",
                    "review_frequency_months": 12,
                },
            ]

            created_doc_controls = 0
            updated_doc_controls = 0
            for ctrl in pci_document_controls:
                existing_ctrl = (
                    session.query(ComplianceControl)
                    .filter_by(scope_id=pci_scope.id, code=ctrl["code"])
                    .first()
                )
                if not existing_ctrl:
                    session.add(ComplianceControl(scope_id=pci_scope.id, **ctrl))
                    created_doc_controls += 1
                else:
                    # Backfill or correct review_frequency_months for existing controls
                    desired_freq = ctrl.get("review_frequency_months")
                    if (
                        desired_freq is not None
                        and existing_ctrl.review_frequency_months != desired_freq
                    ):
                        existing_ctrl.review_frequency_months = desired_freq
                        updated_doc_controls += 1
            if created_doc_controls or updated_doc_controls:
                session.commit()
                logger.info(
                    f"Created {created_doc_controls} and updated {updated_doc_controls} PCI-DSS document controls."
                )
            else:
                logger.info(
                    "PCI-DSS document controls already present; no changes made."
                )
        else:
            logger.warning("PCI-DSS scope not found; skipping PCI controls creation.")

        # Create ISO/IEC 27001 core document controls
        logger.info("Creating ISO 27001 controls if not exist...")
        iso_scope = session.query(ComplianceScope).filter_by(name="ISO 27001").first()
        if iso_scope:
            iso_27001_document_controls = [
                {
                    "code": "ISMS-001",
                    "title": "Politique de sécurité de l'information",
                    "description": "Politique ISMS couvrant le périmètre et les objectifs de sécurité.",
                    "required_document_name": "Politique de sécurité de l'information",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
                {
                    "code": "ISMS-002",
                    "title": "Méthodologie d'appréciation des risques",
                    "description": "Approche d'identification, d'évaluation et de traitement des risques ISMS.",
                    "required_document_name": "Méthodologie d'appréciation des risques",
                    "required_document_type": "methodology",
                    "review_frequency_months": 12,
                },
                {
                    "code": "ISMS-003",
                    "title": "Déclaration d'Applicabilité (SoA)",
                    "description": "Déclaration d'applicabilité des contrôles de référence et leurs justifications.",
                    "required_document_name": "Déclaration d'Applicabilité (SoA)",
                    "required_document_type": "document",
                    "review_frequency_months": 12,
                },
                {
                    "code": "ISMS-004",
                    "title": "Plan de traitement des risques",
                    "description": "Plan d'actions pour réduire les risques à des niveaux acceptables.",
                    "required_document_name": "Plan de traitement des risques",
                    "required_document_type": "plan",
                    "review_frequency_months": 12,
                },
                {
                    "code": "ISMS-005",
                    "title": "Procédure de gestion des incidents",
                    "description": "Procédure de détection, d'escalade et de résolution des incidents de sécurité.",
                    "required_document_name": "Procédure de gestion des incidents",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "ISMS-006",
                    "title": "Politique de contrôle d'accès",
                    "description": "Règles d'octroi, de modification et de retrait des accès.",
                    "required_document_name": "Politique de contrôle d'accès",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
                {
                    "code": "ISMS-007",
                    "title": "Politique de continuité d'activité (ISMS)",
                    "description": "Exigences de continuité et intégration BC avec l'ISMS.",
                    "required_document_name": "Politique de continuité d'activité",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
            ]
            upsert_document_controls_for_scope(
                session, iso_scope, iso_27001_document_controls, "ISO 27001"
            )
        else:
            logger.warning("ISO 27001 scope not found; skipping ISO controls creation.")

        # Create ISO 22301 BCMS document controls
        logger.info("Creating ISO 22301 controls if not exist...")
        iso22301_scope = (
            session.query(ComplianceScope).filter_by(name="ISO 22301").first()
        )
        if iso22301_scope:
            iso_22301_document_controls = [
                {
                    "code": "BCMS-001",
                    "title": "Politique de continuité d'activité",
                    "description": "Politique BCMS décrivant objectifs et périmètre.",
                    "required_document_name": "Politique de continuité d'activité",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
                {
                    "code": "BCMS-002",
                    "title": "Analyse d'impact sur l'activité (BIA)",
                    "description": "Méthodologie et rapport BIA identifiant processus critiques et MTPD.",
                    "required_document_name": "Analyse d'impact sur l'activité",
                    "required_document_type": "analysis",
                    "review_frequency_months": 12,
                },
                {
                    "code": "BCMS-003",
                    "title": "Évaluation des risques BC",
                    "description": "Méthodologie et résultats d'évaluation des risques de continuité.",
                    "required_document_name": "Évaluation des risques BC",
                    "required_document_type": "assessment",
                    "review_frequency_months": 12,
                },
                {
                    "code": "BCMS-004",
                    "title": "Plans de continuité (PCAs)",
                    "description": "Plans détaillés, rôles et procédures de continuité.",
                    "required_document_name": "Plans de continuité",
                    "required_document_type": "plan",
                    "review_frequency_months": 12,
                },
                {
                    "code": "BCMS-005",
                    "title": "Rapports de tests et exercices",
                    "description": "Résultats des tests/exercices BC, leçons apprises et actions.",
                    "required_document_name": "Rapports de tests BC",
                    "required_document_type": "record",
                    "review_frequency_months": 12,
                },
                {
                    "code": "BCMS-006",
                    "title": "Procédures de reprise d'activité",
                    "description": "Procédures de reprise et priorités de restauration.",
                    "required_document_name": "Procédures de reprise d'activité",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
            ]
            upsert_document_controls_for_scope(
                session, iso22301_scope, iso_22301_document_controls, "ISO 22301"
            )
        else:
            logger.warning(
                "ISO 22301 scope not found; skipping ISO 22301 controls creation."
            )

        # Create NDSSI document controls
        logger.info("Creating NDSSI controls if not exist...")
        ndssi_scope = session.query(ComplianceScope).filter_by(name="NDSSI").first()
        if ndssi_scope:
            ndssi_document_controls = [
                {
                    "code": "ND-001",
                    "title": "Politique SSI",
                    "description": "Politique de sécurité des systèmes d'information conforme à la DNSSI.",
                    "required_document_name": "Politique SSI",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
                {
                    "code": "ND-002",
                    "title": "Méthodologie d'analyse de risque",
                    "description": "Méthodologie et registre des risques selon la directive nationale.",
                    "required_document_name": "Méthodologie d'analyse de risque",
                    "required_document_type": "methodology",
                    "review_frequency_months": 12,
                },
                {
                    "code": "ND-003",
                    "title": "Procédure de gestion des incidents",
                    "description": "Processus de traitement des incidents de sécurité (détection à clôture).",
                    "required_document_name": "Procédure de gestion des incidents",
                    "required_document_type": "procedure",
                    "review_frequency_months": 12,
                },
                {
                    "code": "ND-004",
                    "title": "Charte et politique d'accès",
                    "description": "Règles d'habilitation, révision périodique et retrait d'accès.",
                    "required_document_name": "Politique d'accès",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
                {
                    "code": "ND-005",
                    "title": "Plan de continuité et PRA",
                    "description": "PCA et PRA alignés à la directive nationale.",
                    "required_document_name": "PCA/PRA",
                    "required_document_type": "plan",
                    "review_frequency_months": 12,
                },
                {
                    "code": "ND-006",
                    "title": "Charte des administrateurs",
                    "description": "Règles d'utilisation et de sécurité pour comptes à privilèges.",
                    "required_document_name": "Charte des administrateurs",
                    "required_document_type": "policy",
                    "review_frequency_months": 12,
                },
            ]
            upsert_document_controls_for_scope(
                session, ndssi_scope, ndssi_document_controls, "NDSSI"
            )
        else:
            logger.warning("NDSSI scope not found; skipping NDSSI controls creation.")

        # Create a user for each role if the database name contains 'dev'
        if not args.skip_fixtures and "dev" in settings.DB_NAME.lower():
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
