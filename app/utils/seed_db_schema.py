import argparse
import sys

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.logger import logger
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models.role import Permission, Role
from app.db.models.user import User
from app.db.session import SessionLocal, engine

sys.path.append(".")
from tests.test_data import TEST_USERS


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

    user.roles.append(super_admin_role)

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

    ALL_PERMISSIONS = {
        "user": user_permissions,
        "role": role_permissions,
        "group": group_permissions,
    }

    # Role-permission mapping
    ROLE_PERMISSION_MAP = {
        "Super-Admin": {
            "user": ["read", "create", "update", "delete", "purge"],
            "role": ["read", "create", "update", "delete", "purge"],
            "group": ["read", "create", "update", "delete", "purge"],
        },
        "Admin": {
            "user": ["read", "create", "update", "delete"],
            "role": [],
            "group": [],
        },
        "Supervisor": {
            "user": ["read", "create", "update"],
            "role": [],
            "group": [],
        },
        "Technician": {"user": ["read", "update"], "role": [], "group": []},
        "Hotliner": {"user": ["read"], "role": [], "group": []},
        "Observer": {"user": ["read"], "role": [], "group": ["read"]},
        "Self-Service": {"user": [], "role": [], "group": []},
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
                user.roles.append(role)
                session.add(user)
                logger.info(
                    f"Created user for role '{role_name}': {username} / {email} (password: {password})"
                )
            session.commit()

    except IntegrityError as e:
        session.rollback()
        logger.error(f"Integrity error occurred during seeding: {e}")
        sys.exit(1)
    finally:
        session.close()

    logger.info("Seeding complete.")


if __name__ == "__main__":
    main()
