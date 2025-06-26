import argparse
import sys

from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.logger import logger
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models.role import Permission, Role
from app.db.models.user import User
from app.db.session import SessionLocal, engine


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

    # Hash the password
    hashed_password = get_password_hash(password)

    # Create the user
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        status="active",
    )

    # Assign the Super-Admin role
    user.roles.append(super_admin_role)

    session.add(user)
    session.commit()

    logger.info(f"Successfully created super-admin user with ID: {user.id}")
    return user


def main():
    args = parse_arguments()

    # Validate required arguments if any are provided
    if any([args.username, args.email, args.password]) and not all(
        [args.username, args.email, args.password]
    ):
        logger.error(
            "If creating a super-admin user, all three arguments (--username, --email, --password) are required"
        )
        sys.exit(1)

    logger.info(f"Seeding using schema: {settings.DB_SCHEMA}")

    # 1. Create all tables
    logger.info("Creating all tables (if not exist)...")
    Base.metadata.create_all(bind=engine)

    # 2. Preset roles
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

    # 4. Role-permission mapping
    role_permission_map = {
        "Super-Admin": ["read", "create", "update", "delete", "purge"],
        "Admin": ["read", "create", "update", "delete"],
        "Supervisor": ["read", "create", "update"],
        "Technician": ["read", "update"],
        "Hotliner": ["read"],
        "Observer": ["read"],
        "Self-Service": [],
    }

    session = SessionLocal()

    try:
        logger.info("Inserting preset roles...")
        for role_data in preset_roles:
            role = session.query(Role).filter_by(name=role_data["name"]).first()
            if not role:
                role = Role(**role_data)
                session.add(role)
        session.commit()
        logger.info("Preset roles inserted.")

        logger.info("Inserting user management permissions...")
        for perm_data in user_permissions:
            perm = (
                session.query(Permission)
                .filter_by(action=perm_data["action"], resource=perm_data["resource"])
                .first()
            )
            if not perm:
                perm = Permission(**perm_data)
                session.add(perm)
        session.commit()
        logger.info("User management permissions inserted.")

        logger.info("Assigning permissions to roles...")
        for role_name, actions in role_permission_map.items():
            role = session.query(Role).filter_by(name=role_name).first()
            if not role:
                continue
            for action in actions:
                perm = (
                    session.query(Permission)
                    .filter_by(action=action, resource="user")
                    .first()
                )
                if perm and perm not in role.permissions:
                    role.permissions.append(perm)
            session.add(role)
        session.commit()
        logger.info("Permissions assigned to roles.")

        # Create super-admin user if credentials provided
        if all([args.username, args.email, args.password]):
            create_super_admin_user(
                session, args.username, args.email, args.password, args.full_name
            )

    except IntegrityError as e:
        session.rollback()
        logger.error(f"Integrity error occurred during seeding: {e}")
        sys.exit(1)
    finally:
        session.close()

    logger.info("Seeding complete.")


if __name__ == "__main__":
    main()
