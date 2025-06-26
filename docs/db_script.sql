-- USER STATUS ENUM
DO $$ BEGIN
    CREATE TYPE dev.userstatus AS ENUM ('active', 'inactive', 'deleted');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- USERS TABLE
CREATE TABLE IF NOT EXISTS dev.users (
    id SERIAL PRIMARY KEY,
    administrative_number VARCHAR UNIQUE,
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR NOT NULL,
    hashed_password VARCHAR NOT NULL,
    phone VARCHAR,
    secondary_phone VARCHAR,
    timezone VARCHAR,
    location VARCHAR,
    language VARCHAR DEFAULT 'en',
    theme VARCHAR DEFAULT 'light',
    status dev.userstatus NOT NULL DEFAULT 'active',
    valid_until TIMESTAMP,
    valid_from TIMESTAMP
);

-- ROLES TABLE
CREATE TABLE IF NOT EXISTS dev.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL,
    description TEXT,
    is_builtin BOOLEAN DEFAULT FALSE
);

-- PERMISSIONS TABLE
CREATE TABLE IF NOT EXISTS dev.permissions (
    id SERIAL PRIMARY KEY,
    action VARCHAR(16) NOT NULL,      -- e.g., read, create, update, delete, purge
    resource VARCHAR(32) NOT NULL,    -- e.g., user
    description TEXT
);

-- ROLE_PERMISSIONS ASSOCIATION TABLE
CREATE TABLE IF NOT EXISTS dev.role_permissions (
    role_id INTEGER NOT NULL REFERENCES dev.roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES dev.permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- USER_ROLES ASSOCIATION TABLE
CREATE TABLE IF NOT EXISTS dev.user_roles (
    user_id INTEGER NOT NULL REFERENCES dev.users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES dev.roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);


INSERT INTO dev.roles (name, description, is_builtin) VALUES
  ('Super-Admin', 'Full access to all system features and settings', TRUE),
  ('Admin', 'Manage users and settings within their organization', TRUE),
  ('Supervisor', 'Oversee teams and approve actions', TRUE),
  ('Technician', 'Handle technical tasks and tickets', TRUE),
  ('Hotliner', 'First-line support and ticket triage', TRUE),
  ('Observer', 'Read-only access to data', TRUE),
  ('Self-Service', 'Limited access for end users', TRUE)
ON CONFLICT (name) DO NOTHING;