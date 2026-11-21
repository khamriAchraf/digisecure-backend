# Database Seeding Instructions

This document explains how to use the database seeding script to initialize your database with roles, permissions, and optionally create a super-admin user.

## Overview

The seeding process creates:
1. **Preset Roles**: Super-Admin, Admin, Supervisor, Technician, Hotliner, Observer, Self-Service
2. **User Management Permissions**: read, create, update, delete, purge
3. **Role-Permission Mappings**: Assigns appropriate permissions to each role
4. **Compliance reference data**: Preset scopes, events, and controls
5. **Super-Admin User** (optional): Creates a user with Super-Admin role and full system access
6. **Test/demo fixtures** (optional): Locations, manufacturers, operating systems, sample assets, and (for development databases) test users

## Usage

### Recommended: Using the Python Script Directly

The direct script avoids creating a user unless credentials are explicitly
provided. Use `--skip-fixtures` for a baseline seed without test/demo data:

```bash
# Seed baseline and compliance data without test/demo fixtures
poetry run python -m app.utils.seed_db_schema --skip-fixtures

# Create super-admin user with all required arguments
poetry run python -m app.utils.seed_db_schema --username admin --email admin@example.com --password mypassword

# Create super-admin user with custom full name
poetry run python -m app.utils.seed_db_schema --username admin --email admin@example.com --password mypassword --full-name "System Administrator"

# Show help
poetry run python -m app.utils.seed_db_schema --help
```

### Legacy Shell Script

> **Warning:** `seed_db.sh` creates an `admin` account with the hard-coded
> password `admin`. Do not use it for production or shared databases.

## Arguments

- `--username`: Username for the super-admin user
- `--email`: Email for the super-admin user
- `--password`: Password for the super-admin user
- `--full-name`: Full name for the super-admin user (default: "Super Administrator")
- `--skip-fixtures`: Skip test/demo locations, manufacturers, operating systems, assets, and test users

## Important Notes

1. **All or Nothing**: If you provide any of username, email, or password, you must provide all three.

2. **Duplicate Prevention**: The script checks for existing users with the same username or email and will not create duplicates.

3. **Role Dependencies**: The super-admin user creation requires the Super-Admin role to exist. The script creates roles first, then users.

4. **Password Security**: Passwords are automatically hashed using bcrypt before storage.

5. **Logging**: All operations are logged to `seed_db.log` and the console.

## Role Hierarchy

The seeding script creates a hierarchy of roles with specific permissions. For a detailed breakdown of what each role can do, please refer to the [Role-Based Permissions](./PERMISSIONS.md) documentation.
This provides a comprehensive matrix of permissions for each resource type (`user`, `role`, `group`).

## Troubleshooting

### Common Issues

1. **"Super-Admin role not found"**
   - Run the script without user creation first to ensure roles are created
   - Check the database connection and schema

2. **"User already exists"**
   - The script detected an existing user with the same username or email
   - Use different credentials or remove the existing user

3. **"Integrity error"**
   - Check database constraints and existing data
   - Ensure the database schema is up to date

4. **"Permission denied"**
   - Make sure the script has execute permissions: `chmod +x seed_db.sh`
   - Check file ownership and permissions

### Logs

All operations are logged to `seed_db.log`. Check this file for detailed error information:

```bash
tail -f seed_db.log
```

## Security Considerations

1. **Password Strength**: Use strong passwords for super-admin accounts
2. **Environment Variables**: Consider using environment variables for sensitive data in production
3. **Access Control**: Limit access to the seeding script in production environments
4. **Database Security**: Ensure database connections use proper authentication and encryption

## Production Deployment

For production deployments:

1. Run the script without user creation first to set up roles and permissions
2. Create super-admin users through the application's user management interface
3. Use environment-specific database configurations
4. Implement proper backup procedures before running seeding scripts 