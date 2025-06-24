from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import get_password_hash


def create_org_schema_and_user(
    db: Session, schema_name, db_user, db_password, admin_email, admin_password
):
    # 1. Create schema
    db.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    # 2. Create user
    db.execute(
        text(f"CREATE USER {db_user} WITH PASSWORD :password"),
        {"password": db_password},
    )
    # 3. Grant privileges
    db.execute(text(f'GRANT USAGE ON SCHEMA "{schema_name}" TO {db_user}'))
    db.execute(text(f'ALTER USER {db_user} SET search_path = "{schema_name}"'))
    db.execute(text(f'GRANT ALL PRIVILEGES ON SCHEMA "{schema_name}" TO {db_user}'))
    # 4. Create tables
    db.execute(
        text(
            f"""
        CREATE TABLE "{schema_name}".users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL
        );
        CREATE TABLE "{schema_name}".assets (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            owner_id INTEGER REFERENCES "{schema_name}".users(id)
        );
        CREATE TABLE "{schema_name}".templates (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            content TEXT
        );
    """
        )
    )
    # 5. Create admin user
    hashed_pw = get_password_hash(admin_password)
    db.execute(
        text(
            f'INSERT INTO "{schema_name}".users (username, email, hashed_password) VALUES (:username, :email, :hashed_password)'
        ),
        {"username": "admin", "email": admin_email, "hashed_password": hashed_pw},
    )
    db.commit()
