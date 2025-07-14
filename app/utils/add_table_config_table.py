#!/usr/bin/env python3
"""
Script to add the user_table_configs table to the database.
This should be run once to add the new table to existing databases.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from app.core.config import settings
from app.core.logger import logger
from app.db.session import engine


def add_table_config_table():
    """Add the user_table_configs table to the database."""

    # Read the SQL script
    sql_file = Path(__file__).parent / "add_table_config_table.sql"
    with open(sql_file, "r") as f:
        sql_script = f.read()

    logger.info(f"Adding user_table_configs table to database: {settings.DB_NAME}")

    try:
        with engine.connect() as conn:
            # Split the script into individual statements
            statements = [
                stmt.strip() for stmt in sql_script.split(";") if stmt.strip()
            ]

            for statement in statements:
                if statement:
                    logger.debug(f"Executing: {statement[:50]}...")
                    conn.execute(text(statement))

            conn.commit()
            logger.info("Successfully added user_table_configs table")

    except Exception as e:
        logger.error(f"Error adding table: {e}")
        raise


if __name__ == "__main__":
    add_table_config_table()
