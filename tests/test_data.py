"""
Shared test data for all test files.
Contains user credentials, role information, and other test constants.
"""

TEST_USERS = {
    "admin": {
        "username": "admin1",
        "email": "admin1@example.com",
        "password": "testpass123!",
        "role_id": 2,
        "role_name": "Admin",
    },
    "supervisor": {
        "username": "supervisor1",
        "email": "supervisor1@example.com",
        "password": "testpass123!",
        "role_id": 3,
        "role_name": "Supervisor",
    },
    "technician": {
        "username": "technician1",
        "email": "technician1@example.com",
        "password": "testpass123!",
        "role_id": 4,
        "role_name": "Technician",
    },
    "hotliner": {
        "username": "hotliner1",
        "email": "hotliner1@example.com",
        "password": "testpass123!",
        "role_id": 5,
        "role_name": "Hotliner",
    },
    "observer": {
        "username": "observer1",
        "email": "observer1@example.com",
        "password": "testpass123!",
        "role_id": 6,
        "role_name": "Observer",
    },
    "self_service": {
        "username": "selfservice1",
        "email": "selfservice1@example.com",
        "password": "testpass123!",
        "role_id": 7,
        "role_name": "Self-Service",
    },
}

SUPER_ADMIN = {
    "username": "admin",
    "email": "admin@admin.com",
    "password": "admin",
    "role_id": 1,
    "role_name": "Super-Admin",
}

ROLES = {
    1: {"name": "Super-Admin"},
    2: {"name": "Admin"},
    3: {"name": "Supervisor"},
    4: {"name": "Technician"},
    5: {"name": "Hotliner"},
    6: {"name": "Observer"},
    7: {"name": "Self-Service"},
}

TEST_PASSWORD = "testpass123!"
BASE_URL = "http://test/api/v1"
