import argparse
import sys
from datetime import date, datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.logger import logger
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import (
    Location,
    Manufacturer,
    Permission,
    Role,
    TableConfig,
    User,
    ComplianceScope,
)
from app.db.models.asset import (Cable, Computer, Consumable, NetworkDevice,
                                 Peripheral, Phone, Printer, Rack, SimCardItem)
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
            "created_at": now,
            "updated_at": now,
            "cpu": "Intel Core i7-12700K",
            "ram": "32GB DDR4",
            "storage": "1TB NVMe SSD",
            "os": "Windows 11 Pro",
            "mac_address": "00:1B:44:11:3A:B7",
            "ip_address": "192.168.1.100",
            "model": "Dell OptiPlex 7090",
            "hostname": "WS001",
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

    # Sample Printers
    printers_data = [
        {
            "name": "Office-Printer-01",
            "serial_number": "PR001-2023-001",
            "inventory_number": "INV-PRT-001",
            "manufacturer_id": manufacturers[0].id if manufacturers else None,
            "status": "active",
            "purchase_date": date(2023, 6, 10),
            "warranty_expiry": date(2026, 6, 10),
            "location_id": locations[0].id if locations else None,
            "type": "printer",
            "created_at": now,
            "updated_at": now,
            "model": "HP LaserJet Pro M404n",
            "ip_address": "192.168.1.200",
            "mac_address": "00:1B:44:11:3A:C1",
            "connection_type": "Network",
            "print_technology": "Laser",
            "max_resolution": "600x600 dpi",
            "color_support": "Monochrome",
            "duplex_support": "Yes",
        }
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
            "created_at": now,
            "updated_at": now,
            "device_type": "Switch",
            "model": "Cisco Catalyst 2960-X",
            "ip_address": "192.168.1.1",
            "mac_address": "00:1B:44:11:3A:D1",
            "port_count": 48,
            "connection_type": "Ethernet",
            "management_ip": "192.168.1.1",
            "firmware_version": "15.2(4)E7",
        }
    ]

    # Sample Phones
    phones_data = [
        {
            "name": "Desk-Phone-01",
            "serial_number": "PH001-2024-001",
            "inventory_number": "INV-PHN-001",
            "manufacturer_id": (
                manufacturers[3].id
                if len(manufacturers) > 3
                else manufacturers[0].id if manufacturers else None
            ),
            "status": "active",
            "purchase_date": date(2024, 1, 10),
            "warranty_expiry": date(2027, 1, 10),
            "location_id": locations[0].id if locations else None,
            "assigned_to": users[0].id if users else None,
            "type": "phone",
            "created_at": now,
            "updated_at": now,
            "model": "Cisco IP Phone 8845",
            "phone_type": "Desk Phone",
            "extension": "1001",
            "ip_address": "192.168.1.150",
            "mac_address": "00:1B:44:11:3A:E1",
            "phone_system": "Cisco Unified Communications",
            "line_count": 2,
        }
    ]

    # Sample Peripherals
    peripherals_data = [
        {
            "name": "Wireless-Mouse-01",
            "serial_number": "PR001-2024-001",
            "inventory_number": "INV-PER-001",
            "manufacturer_id": (
                manufacturers[4].id
                if len(manufacturers) > 4
                else manufacturers[0].id if manufacturers else None
            ),
            "status": "active",
            "purchase_date": date(2024, 3, 5),
            "warranty_expiry": date(2027, 3, 5),
            "location_id": locations[0].id if locations else None,
            "assigned_to": users[0].id if users else None,
            "type": "peripheral",
            "created_at": now,
            "updated_at": now,
            "peripheral_type": "Mouse",
            "model": "Logitech MX Master 3",
            "connection_type": "Wireless",
            "compatibility": "Windows, Mac, Linux",
            "special_features": "Wireless, Ergonomic",
        }
    ]

    # Sample Consumables
    consumables_data = [
        {
            "name": "HP-Toner-Cartridge",
            "serial_number": "TC001-2024-001",
            "inventory_number": "INV-CON-001",
            "manufacturer_id": manufacturers[0].id if manufacturers else None,
            "status": "active",
            "purchase_date": date(2024, 4, 1),
            "warranty_expiry": date(2025, 4, 1),
            "location_id": locations[0].id if locations else None,
            "type": "consumable",
            "created_at": now,
            "updated_at": now,
            "consumable_type": "Toner",
            "model": "HP 26A Black Toner Cartridge",
            "quantity": 5,
            "unit": "cartridges",
            "expiry_date": date(2026, 4, 1),
            "compatible_with": "HP LaserJet Pro M404n",
        }
    ]

    # Sample Racks
    racks_data = [
        {
            "name": "Server-Rack-01",
            "serial_number": "RK001-2023-001",
            "inventory_number": "INV-RCK-001",
            "manufacturer_id": (
                manufacturers[5].id
                if len(manufacturers) > 5
                else manufacturers[0].id if manufacturers else None
            ),
            "status": "active",
            "purchase_date": date(2023, 8, 20),
            "warranty_expiry": date(2028, 8, 20),
            "location_id": locations[0].id if locations else None,
            "type": "rack",
            "created_at": now,
            "updated_at": now,
            "rack_type": "Server Rack",
            "model": "APC AR3100",
            "height_units": 42,
            "width": '19"',
            "depth": '36"',
            "max_weight_capacity": "2000 lbs",
            "location_details": "Data Center - Row A",
        }
    ]

    # Sample Cables
    cables_data = [
        {
            "name": "Ethernet-Cable-01",
            "serial_number": "CB001-2024-001",
            "inventory_number": "INV-CBL-001",
            "manufacturer_id": (
                manufacturers[6].id
                if len(manufacturers) > 6
                else manufacturers[0].id if manufacturers else None
            ),
            "status": "active",
            "purchase_date": date(2024, 2, 15),
            "warranty_expiry": date(2029, 2, 15),
            "location_id": locations[0].id if locations else None,
            "type": "cable",
            "created_at": now,
            "updated_at": now,
            "cable_type": "Ethernet",
            "model": "Cat6 UTP Cable",
            "length": "100m",
            "connector_type": "RJ45",
            "category": "Cat6",
            "color": "Blue",
            "max_bandwidth": "1 Gbps",
        }
    ]

    # Sample SIM Cards
    sim_cards_data = [
        {
            "name": "Data-SIM-01",
            "serial_number": "SC001-2024-001",
            "inventory_number": "INV-SIM-001",
            "manufacturer_id": (
                manufacturers[7].id
                if len(manufacturers) > 7
                else manufacturers[0].id if manufacturers else None
            ),
            "status": "active",
            "purchase_date": date(2024, 1, 20),
            "warranty_expiry": date(2027, 1, 20),
            "location_id": locations[0].id if locations else None,
            "assigned_to": users[0].id if users else None,
            "type": "sim_card_item",
            "created_at": now,
            "updated_at": now,
            "sim_type": "Nano",
            "iccid": "89014103211118510720",
            "imsi": "310260123456789",
            "carrier": "AT&T",
            "phone_number": "+1-555-0123",
            "data_plan": "Unlimited Data",
            "activation_date": date(2024, 1, 25),
            "expiry_date": date(2025, 1, 25),
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

    # Create printers
    for prt_data in printers_data:
        existing = (
            session.query(Printer)
            .filter_by(serial_number=prt_data["serial_number"])
            .first()
        )
        if not existing:
            printer = Printer(**prt_data)
            session.add(printer)
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

    # Create phones
    for phn_data in phones_data:
        existing = (
            session.query(Phone)
            .filter_by(serial_number=phn_data["serial_number"])
            .first()
        )
        if not existing:
            phone = Phone(**phn_data)
            session.add(phone)
            assets_created += 1

    # Create peripherals
    for per_data in peripherals_data:
        existing = (
            session.query(Peripheral)
            .filter_by(serial_number=per_data["serial_number"])
            .first()
        )
        if not existing:
            peripheral = Peripheral(**per_data)
            session.add(peripheral)
            assets_created += 1

    # Create consumables
    for con_data in consumables_data:
        existing = (
            session.query(Consumable)
            .filter_by(serial_number=con_data["serial_number"])
            .first()
        )
        if not existing:
            consumable = Consumable(**con_data)
            session.add(consumable)
            assets_created += 1

    # Create racks
    for rck_data in racks_data:
        existing = (
            session.query(Rack)
            .filter_by(serial_number=rck_data["serial_number"])
            .first()
        )
        if not existing:
            rack = Rack(**rck_data)
            session.add(rack)
            assets_created += 1

    # Create cables
    for cbl_data in cables_data:
        existing = (
            session.query(Cable)
            .filter_by(serial_number=cbl_data["serial_number"])
            .first()
        )
        if not existing:
            cable = Cable(**cbl_data)
            session.add(cable)
            assets_created += 1

    # Create SIM cards
    for sim_data in sim_cards_data:
        existing = (
            session.query(SimCardItem)
            .filter_by(serial_number=sim_data["serial_number"])
            .first()
        )
        if not existing:
            sim_card = SimCardItem(**sim_data)
            session.add(sim_card)
            assets_created += 1

    session.commit()
    logger.info(f"Created {assets_created} sample assets")


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
        },
        {
            "name": "Admin",
            "description": "Manage users and settings within their organization",
            "is_builtin": True,
        },
        {
            "name": "Supervisor",
            "description": "Oversee teams and approve actions",
            "is_builtin": True,
        },
        {
            "name": "Technician",
            "description": "Handle technical tasks and tickets",
            "is_builtin": True,
        },
        {
            "name": "Hotliner",
            "description": "First-line support and ticket triage",
            "is_builtin": True,
        },
        {
            "name": "Observer",
            "description": "Read-only access to data",
            "is_builtin": True,
        },
        {
            "name": "Self-Service",
            "description": "Limited access for end users",
            "is_builtin": True,
        },
    ]

    # 3. User management permissions
    user_permissions = [
        {"action": "read", "resource": "user", "description": "View user information"},
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

    # 11. compliance scope management permissions
    compliance_scope_permissions = [
        {
            "action": "read",
            "resource": "compliance_scope",
            "description": "View compliance scopes",
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
        }
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
        "compliance_scope": compliance_scope_permissions,
        "asset": asset_compliance_permissions,
    }

    # Role-permission mapping
    ROLE_PERMISSION_MAP = {
        "Super-Admin": {
            "user": ["read", "create", "update", "delete", "purge"],
            "role": ["read", "create", "update", "delete", "purge"],
            "group": ["read", "create", "update", "delete", "purge"],
            "reference_data": ["read", "create", "update", "delete", "purge"],
            "computer": ["read", "create", "update", "delete", "purge"],
            "virtual_machine": ["read", "create", "update", "delete", "purge"],
            "network_device": ["read", "create", "update", "delete", "purge"],
            "software": ["read", "create", "update", "delete", "purge"],
            "compliance_scope": ["read", "create", "update", "delete", "purge"],
            "asset": ["compliance_manage"],
        },
        "Admin": {
            "user": ["read", "create", "update", "delete"],
            "role": [],
            "group": [],
            "reference_data": ["read", "create", "update", "delete", "purge"],
            "computer": ["read", "create", "update", "delete"],
            "virtual_machine": ["read", "create", "update", "delete"],
            "network_device": ["read", "create", "update", "delete"],
            "software": ["read", "create", "update", "delete", "purge"],
            "compliance_scope": ["read", "create", "update", "delete", "purge"],
            "asset": ["compliance_manage"],
        },
        "Supervisor": {
            "user": ["read", "create", "update"],
            "role": [],
            "group": [],
            "reference_data": [],
            "computer": ["read", "create", "update"],
            "virtual_machine": ["read", "create", "update"],
            "network_device": ["read", "create", "update"],
            "software": ["read", "create", "update"],
            "compliance_scope": [],
        },
        "Technician": {
            "user": ["read", "update"],
            "role": [],
            "group": [],
            "reference_data": [],
            "computer": ["read", "create", "update"],
            "virtual_machine": ["read", "create", "update"],
            "network_device": ["read", "create", "update"],
            "software": ["read", "create", "update"],
            "compliance_scope": [],
        },
        "Hotliner": {
            "user": ["read"],
            "role": [],
            "group": [],
            "reference_data": [],
            "computer": ["read"],
            "virtual_machine": ["read"],
            "network_device": ["read"],
            "software": ["read"],
            "compliance_scope": ["read"],
        },
        "Observer": {
            "user": ["read"],
            "role": [],
            "group": ["read"],
            "reference_data": ["read"],
            "computer": ["read"],
            "virtual_machine": ["read"],
            "network_device": ["read"],
            "software": ["read"],
            "compliance_scope": ["read"],
        },
        "Self-Service": {
            "user": [],
            "role": [],
            "group": [],
            "reference_data": [],
            "computer": ["read"],
            "virtual_machine": ["read"],
            "network_device": ["read"],
            "software": ["read"],
            "compliance_scope": [],
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
