from functools import lru_cache

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = Field(
        default="sqlite:///./quadral_cluster.db",
        description="SQLAlchemy database URL",
    )
    debug: bool = Field(default=False, description="Toggle FastAPI debug mode")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "QUADRAL_",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached instance of application settings."""

    return Settings()
