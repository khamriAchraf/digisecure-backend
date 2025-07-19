#!/usr/bin/env python3
"""
Demonstration script for the updated JWT token structure with role_id and permissions.

This script shows how tokens now include role information and permissions
in the format 'resource:action' for more efficient permission checking.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from unittest.mock import Mock

from app.core.security import has_permission_from_token
from app.db.models.role import Permission, Role
from app.db.models.user import User
from app.services.auth_service import (_get_user_permissions,
                                       create_access_token,
                                       decode_access_token_payload)


def create_mock_user_with_permissions():
    """Create a mock user with role and permissions for demonstration."""

    # Create mock permissions
    perm1 = Mock(spec=Permission)
    perm1.resource = "user"
    perm1.action = "read"

    perm2 = Mock(spec=Permission)
    perm2.resource = "user"
    perm2.action = "create"

    perm3 = Mock(spec=Permission)
    perm3.resource = "role"
    perm3.action = "read"

    perm4 = Mock(spec=Permission)
    perm4.resource = "asset"
    perm4.action = "update"

    # Create mock role with permissions
    role = Mock(spec=Role)
    role.id = 1
    role.name = "Admin"
    role.permissions = [perm1, perm2, perm3, perm4]

    # Create mock user with role
    user = Mock(spec=User)
    user.id = 123
    user.email = "admin@example.com"
    user.role = role

    return user


def demonstrate_token_creation():
    """Demonstrate token creation with role_id and permissions."""
    print("=== Token Creation with Role and Permissions ===\n")

    # Create mock user
    user = create_mock_user_with_permissions()

    # Get user permissions
    permissions = _get_user_permissions(user)
    print(f"User permissions: {permissions}")

    # Prepare token data
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": user.role.id if user.role else None,
        "permissions": permissions,
    }

    print(f"Token data: {token_data}")

    # Create access token
    access_token = create_access_token(token_data)
    print(f"\nAccess token created: {access_token[:50]}...")

    return access_token


def demonstrate_token_decoding(token):
    """Demonstrate decoding token and extracting permissions."""
    print("\n=== Token Decoding and Permission Extraction ===\n")

    # Decode token payload
    payload = decode_access_token_payload(token)
    if payload:
        print(f"Decoded payload:")
        print(f"  User ID: {payload.get('sub')}")
        print(f"  Email: {payload.get('email')}")
        print(f"  Role ID: {payload.get('role_id')}")
        print(f"  Permissions: {payload.get('permissions')}")
        print(f"  Token type: {payload.get('type')}")
        print(f"  Expires: {datetime.fromtimestamp(payload.get('exp'))}")

        return payload
    else:
        print("Failed to decode token")
        return None


def demonstrate_permission_checking(payload):
    """Demonstrate permission checking from token payload."""
    print("\n=== Permission Checking from Token ===\n")

    if not payload:
        print("No payload available for permission checking")
        return

    # Test various permission checks
    test_permissions = [
        ("read", "user"),
        ("create", "user"),
        ("delete", "user"),
        ("read", "role"),
        ("update", "asset"),
        ("delete", "asset"),
        ("read", "asset"),
    ]

    print("Permission check results:")
    for action, resource in test_permissions:
        has_perm = has_permission_from_token(payload, action, resource)
        status = "✅ GRANTED" if has_perm else "❌ DENIED"
        print(f"  {resource}:{action} -> {status}")


def demonstrate_performance_benefits():
    """Demonstrate the performance benefits of token-based permission checking."""
    print("\n=== Performance Benefits ===\n")

    print("Benefits of token-based permission checking:")
    print("1. No database queries required for permission checks")
    print("2. Reduced database load under high traffic")
    print("3. Faster permission validation")
    print("4. Permissions cached in token for token lifetime")
    print("5. Better scalability for microservices")

    print("\nUse cases:")
    print("- API rate limiting based on permissions")
    print("- Frontend permission-based UI rendering")
    print("- Microservice-to-microservice authorization")
    print("- Real-time permission validation")


def main():
    """Main demonstration function."""
    print("JWT Token Structure with Role and Permissions Demo")
    print("=" * 50)

    try:
        # Demonstrate token creation
        token = demonstrate_token_creation()

        # Demonstrate token decoding
        payload = demonstrate_token_decoding(token)

        # Demonstrate permission checking
        demonstrate_permission_checking(payload)

        # Demonstrate performance benefits
        demonstrate_performance_benefits()

        print("\n" + "=" * 50)
        print("Demo completed successfully!")

    except Exception as e:
        print(f"\nError during demonstration: {e}")
        print(
            "Make sure you have the required dependencies installed and the app is properly configured."
        )


if __name__ == "__main__":
    main()
