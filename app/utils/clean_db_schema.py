from sqlalchemy import create_engine, text

from app.core.config import settings
from app.core.logger import logger

if __name__ == "__main__":
    if settings.DB_NAME != "test":
        raise RuntimeError(
            f"Refusing to clean schema outside of test database! Current database: {settings.DB_NAME}"
        )

    logger.info(f"Cleaning public schema in test database: {settings.DB_NAME}")

    # Connect directly to the test database
    engine = create_engine(
        f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )

    with engine.connect() as conn:
        # Drop and recreate the public schema
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        conn.commit()

    logger.info("Public schema cleaned and recreated.")
