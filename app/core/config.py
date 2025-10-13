import os

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.logger import logger


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
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
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_SERVICE_URL: str = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8080")
    PASSWORD_RESET_URL: str = os.getenv(
        "PASSWORD_RESET_URL", "http://localhost:3000/reset-password"
    )
    DEBUG: bool = False
    GEOLITE2_DB_PATH: str = os.getenv("GEOLITE2_DB_PATH", "./data/GeoLite2-City.mmdb")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
    )


class TestSettings(BaseSettings):
    DB_HOST: str = os.getenv("DB_HOST", "")
    DB_PORT: str = os.getenv("DB_PORT", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "")
    DB_SCHEMA: str = os.getenv("DB_SCHEMA", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "")
    JWT_EXPIRATION_MINUTES: int = os.getenv("JWT_EXPIRATION_MINUTES", 60)
    JWT_REFRESH_EXPIRATION_DAYS: int = os.getenv("JWT_REFRESH_EXPIRATION_DAYS", 7)
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_SERVICE_URL: str = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8080")
    PASSWORD_RESET_URL: str = os.getenv(
        "PASSWORD_RESET_URL", "http://localhost:3000/reset-password"
    )
    DEBUG: bool = False
    GEOLITE2_DB_PATH: str = os.getenv("GEOLITE2_DB_PATH", "./data/GeoLite2-City.mmdb")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env.test"),
        env_file_encoding="utf-8",
    )


def get_settings() -> Settings:
    """Get settings based on environment."""
    if os.getenv("ENV_FILE") == ".env.test" or os.getenv("TESTING") == "true":
        logger.debug("TEST environment detected")
        return TestSettings()  # type: ignore
    return Settings()  # type: ignore


settings = get_settings()


def get_test_settings() -> TestSettings:
    """Get settings configured for testing environment."""
    return TestSettings()  # type: ignore
