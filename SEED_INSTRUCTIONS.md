# Database Seeding Instructions

This document explains how to use the database seeding script to initialize your database with roles, permissions, and optionally create a super-admin user.

## Overview

The seeding process creates:
1. **Preset Roles**: Super-Admin, Admin, Supervisor, Technician, Hotliner, Observer, Self-Service
2. **User Management Permissions**: read, create, update, delete, purge
3. **Role-Permission Mappings**: Assigns appropriate permissions to each role
4. **Super-Admin User** (optional): Creates a user with Super-Admin role and full system access

## Usage

### Method 1: Using the Shell Script (Recommended)

The `seed_db.sh` script provides a convenient way to seed the database:

```bash
# Seed only roles and permissions (no user creation)
./seed_db.sh

# Create super-admin user with credentials
./seed_db.sh <username> <email> <password>

# Examples:
./seed_db.sh admin admin@example.com mypassword
./seed_db.sh "John Doe" john@company.com "secure123!"

# Show help
./seed_db.sh --help
```

### Method 2: Using the Python Script Directly

You can also run the Python script directly with more options:

```bash
# Seed only roles and permissions
poetry run python app/db/seed.py

# Create super-admin user with all required arguments
poetry run python app/db/seed.py --username admin --email admin@example.com --password mypassword

# Create super-admin user with custom full name
poetry run python app/db/seed.py --username admin --email admin@example.com --password mypassword --full-name "System Administrator"

# Show help
poetry run python app/db/seed.py --help
```

## Arguments

### Shell Script Arguments
- `username`: Username for the super-admin user (required if creating user)
- `email`: Email for the super-admin user (required if creating user)
- `password`: Password for the super-admin user (required if creating user)

### Python Script Arguments
- `--username`: Username for the super-admin user
- `--email`: Email for the super-admin user
- `--password`: Password for the super-admin user
- `--full-name`: Full name for the super-admin user (default: "Super Administrator")

## Important Notes

1. **All or Nothing**: If you provide any of username, email, or password, you must provide all three.

2. **Duplicate Prevention**: The script checks for existing users with the same username or email and will not create duplicates.

3. **Role Dependencies**: The super-admin user creation requires the Super-Admin role to exist. The script creates roles first, then users.

4. **Password Security**: Passwords are automatically hashed using bcrypt before storage.

5. **Logging**: All operations are logged to `seed_db.log` and the console.

## Role Hierarchy

The seeding script creates the following role hierarchy:

| Role | Permissions | Description |
|------|-------------|-------------|
| Super-Admin | read, create, update, delete, purge | Full system access |
| Admin | read, create, update, delete | Manage users and settings |
| Supervisor | read, create, update | Oversee teams and approve actions |
| Technician | read, update | Handle technical tasks |
| Hotliner | read | First-line support |
| Observer | read | Read-only access |
| Self-Service | none | Limited end-user access |

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