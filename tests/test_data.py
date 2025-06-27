"""
Shared test data for all test files.
Contains user credentials, role information, and other test constants.
"""

# Test user credentials created by test_create_and_list_users()
TEST_USERS = {
    "admin": {
        "username": "admin1",
        "email": "admin1@example.com",
        "password": "testpass123!",
        "role_id": 2,
        "role_name": "Admin",
        "permissions": ["read", "create", "update", "delete"],
    },
    "supervisor": {
        "username": "supervisor1",
        "email": "supervisor1@example.com",
        "password": "testpass123!",
        "role_id": 3,
        "role_name": "Supervisor",
        "permissions": ["read", "create", "update"],
    },
    "technician": {
        "username": "technician1",
        "email": "technician1@example.com",
        "password": "testpass123!",
        "role_id": 4,
        "role_name": "Technician",
        "permissions": ["read", "update"],
    },
    "hotliner": {
        "username": "hotliner1",
        "email": "hotliner1@example.com",
        "password": "testpass123!",
        "role_id": 5,
        "role_name": "Hotliner",
        "permissions": ["read"],
    },
    "observer": {
        "username": "observer1",
        "email": "observer1@example.com",
        "password": "testpass123!",
        "role_id": 6,
        "role_name": "Observer",
        "permissions": ["read"],
    },
    "self_service": {
        "username": "selfservice1",
        "email": "selfservice1@example.com",
        "password": "testpass123!",
        "role_id": 7,
        "role_name": "Self-Service",
        "permissions": [],
    },
}

# Super admin credentials (created by seeding script)
SUPER_ADMIN = {
    "username": "admin",
    "email": "admin@admin.com",
    "password": "admin",
    "role_id": 1,
    "role_name": "Super-Admin",
    "permissions": ["read", "create", "update", "delete", "purge"],
}

# Role information for reference
ROLES = {
    1: {
        "name": "Super-Admin",
        "permissions": ["read", "create", "update", "delete", "purge"],
    },
    2: {"name": "Admin", "permissions": ["read", "create", "update", "delete"]},
    3: {"name": "Supervisor", "permissions": ["read", "create", "update"]},
    4: {"name": "Technician", "permissions": ["read", "update"]},
    5: {"name": "Hotliner", "permissions": ["read"]},
    6: {"name": "Observer", "permissions": ["read"]},
    7: {"name": "Self-Service", "permissions": []},
}

# Test constants
TEST_PASSWORD = "testpass123!"
BASE_URL = "http://test/api/v1"
