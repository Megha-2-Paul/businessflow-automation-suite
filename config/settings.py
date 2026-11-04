"""Validated application settings loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime configuration for BusinessFlow."""

    app_name: str
    environment: str
    database_url: str
    log_level: str
    max_upload_mb: int
    storage_dir: Path

    @classmethod
    def from_environment(cls) -> "Settings":
        """Build settings from environment variables and the project .env file."""
        load_dotenv(PROJECT_ROOT / ".env")
        max_upload_mb = int(os.getenv("BUSINESSFLOW_MAX_UPLOAD_MB", "25"))
        if not 1 <= max_upload_mb <= 500:
            raise ValueError("BUSINESSFLOW_MAX_UPLOAD_MB must be between 1 and 500.")

        environment = os.getenv("BUSINESSFLOW_ENVIRONMENT", "development").lower()
        if environment not in {"development", "testing", "production"}:
            raise ValueError(
                "BUSINESSFLOW_ENVIRONMENT must be development, testing, or production."
            )

        storage_dir = Path(
            os.getenv("BUSINESSFLOW_STORAGE_DIR", str(PROJECT_ROOT / "storage"))
        ).expanduser()
        if not storage_dir.is_absolute():
            storage_dir = PROJECT_ROOT / storage_dir

        return cls(
            app_name=os.getenv("BUSINESSFLOW_APP_NAME", "BusinessFlow Automation Suite"),
            environment=environment,
            database_url=os.getenv(
                "BUSINESSFLOW_DATABASE_URL",
                f"sqlite:///{(PROJECT_ROOT / 'data' / 'businessflow.db').as_posix()}",
            ),
            log_level=os.getenv("BUSINESSFLOW_LOG_LEVEL", "INFO").upper(),
            max_upload_mb=max_upload_mb,
            storage_dir=storage_dir.resolve(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings.from_environment()
