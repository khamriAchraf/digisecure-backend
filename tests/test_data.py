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

TEST_LOCATIONS = {
    "location1": {
        "name": "Test Location 1",
        "postal_code": "12345",
        "building_number": "42",
        "latitude": 40.7128,
        "altitude": 100.0,
        "comment": "Test location for development",
        "address": "123 Test Street",
        "town": "Test City",
        "country": "Test Country",
        "state": "Test State",
        "room_number": "101",
        "longitude": -74.0060,
        "floor_number": "1",
    },
}

TEST_MANUFACTURERS = {
    "manufacturer1": {
        "name": "Test Manufacturer 1",
        "comment": "Test manufacturer for development",
    },
}

TEST_OPERATING_SYSTEMS = {
    "operating_system1": {
        "name": "Windows",
        "version": "10 Pro 22H2",
        "vendor": "Microsoft",
        "architecture": "x86_64",
    },
    "operating_system2": {
        "name": "Windows",
        "version": "11 Pro 23H2",
        "vendor": "Microsoft",
        "architecture": "x86_64",
    },
    "operating_system3": {
        "name": "Windows Server",
        "version": "2019",
        "vendor": "Microsoft",
        "architecture": "x86_64",
    },
    "operating_system4": {
        "name": "Windows Server",
        "version": "2022",
        "vendor": "Microsoft",
        "architecture": "x86_64",
    },
    "operating_system5": {
        "name": "Ubuntu",
        "version": "20.04 LTS",
        "vendor": "Canonical",
        "architecture": "x86_64",
    },
    "operating_system6": {
        "name": "Ubuntu",
        "version": "22.04 LTS",
        "vendor": "Canonical",
        "architecture": "x86_64",
    },
    "operating_system7": {
        "name": "Debian",
        "version": "12 (Bookworm)",
        "vendor": "Debian",
        "architecture": "x86_64",
    },
    "operating_system8": {
        "name": "CentOS",
        "version": "7",
        "vendor": "CentOS",
        "architecture": "x86_64",
    },
    "operating_system9": {
        "name": "RHEL",
        "version": "9",
        "vendor": "Red Hat",
        "architecture": "x86_64",
    },
    "operating_system10": {
        "name": "Cisco IOS",
        "version": "15.9(3)M11",
        "vendor": "Cisco",
        "architecture": "MIPS",
    },
}


TEST_PASSWORD = "testpass123!"
BASE_URL = "http://test/api/v1"
