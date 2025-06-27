from sqlalchemy import text

from app.core.config import settings
from app.core.logger import logger
from app.db.session import engine

if __name__ == "__main__":
    if settings.DB_SCHEMA != "test":
        raise RuntimeError(
            f"Refusing to drop tables outside of test schema! Current schema: {settings.DB_SCHEMA}"
        )
    logger.info(f"Dropping all tables in schema: {settings.DB_SCHEMA}")
    with engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {settings.DB_SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {settings.DB_SCHEMA}"))
        conn.commit()
    logger.info("All tables dropped.")
