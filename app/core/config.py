import os

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.logger import logger


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_SCHEMA: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRATION_MINUTES: int
    JWT_REFRESH_EXPIRATION_DAYS: int
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
    )


class TestSettings(BaseSettings):
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_SCHEMA: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRATION_MINUTES: int
    JWT_REFRESH_EXPIRATION_DAYS: int
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env.test"),
        env_file_encoding="utf-8",
    )


def get_settings() -> Settings:
    """Get settings based on environment."""
    if os.getenv("ENV_FILE") == ".env.test" or os.getenv("TESTING") == "true":
        logger.info("Using test settings")
        return TestSettings()  # type: ignore
    logger.info("Using dev settings")
    return Settings()  # type: ignore


settings = get_settings()


def get_test_settings() -> TestSettings:
    """Get settings configured for testing environment."""
    return TestSettings()  # type: ignore
