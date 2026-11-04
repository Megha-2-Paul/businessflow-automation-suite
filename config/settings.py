"""Validated application settings loaded from environment variables."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_DATABASE_DRIVERS = {"sqlite", "postgresql", "postgresql+psycopg"}
VALID_LOG_LEVELS = set(logging.getLevelNamesMapping())

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
    def from_environment(cls) -> Settings:
        """Build and validate settings from environment variables and .env."""
        load_dotenv(PROJECT_ROOT / ".env")
        raw_limit = os.getenv("BUSINESSFLOW_MAX_UPLOAD_MB", "25")
        try:
            max_upload_mb = int(raw_limit)
        except ValueError as exc:
            raise ValueError(
                "BUSINESSFLOW_MAX_UPLOAD_MB must be a whole number between 1 and 500."
            ) from exc
        if not 1 <= max_upload_mb <= 500:
            raise ValueError("BUSINESSFLOW_MAX_UPLOAD_MB must be between 1 and 500.")
        environment = os.getenv("BUSINESSFLOW_ENVIRONMENT", "development").strip().lower()
        if environment not in {"development", "testing", "production"}:
            raise ValueError(
                "BUSINESSFLOW_ENVIRONMENT must be development, testing, or production."
            )
        default_database_url = f"sqlite:///{(PROJECT_ROOT / 'data' / 'businessflow.db').as_posix()}"
        database_url = os.getenv(
            "BUSINESSFLOW_DATABASE_URL", default_database_url
        ).strip()
        if not database_url:
            raise ValueError("BUSINESSFLOW_DATABASE_URL must not be empty.")
        try:
            parsed_url = make_url(database_url)
        except (ValueError, TypeError) as exc:
            raise ValueError("BUSINESSFLOW_DATABASE_URL is not a valid SQLAlchemy URL.") from exc
        if parsed_url.drivername not in SUPPORTED_DATABASE_DRIVERS:
            raise ValueError(
                "BUSINESSFLOW_DATABASE_URL must use SQLite or PostgreSQL with psycopg."
            )
        if parsed_url.drivername == "sqlite" and parsed_url.database in {None, ""}:
            raise ValueError("BUSINESSFLOW_DATABASE_URL must identify a SQLite database.")
        log_level = os.getenv("BUSINESSFLOW_LOG_LEVEL", "INFO").strip().upper()
        if log_level not in VALID_LOG_LEVELS:
            raise ValueError("BUSINESSFLOW_LOG_LEVEL must be a standard Python logging level.")
        storage_dir = Path(
            os.getenv("BUSINESSFLOW_STORAGE_DIR", str(PROJECT_ROOT / "storage"))
        ).expanduser()
        if not storage_dir.is_absolute():
            storage_dir = PROJECT_ROOT / storage_dir
        return cls(
            app_name=os.getenv("BUSINESSFLOW_APP_NAME", "BusinessFlow Automation Suite").strip(),
            environment=environment, database_url=database_url, log_level=log_level,
            max_upload_mb=max_upload_mb, storage_dir=storage_dir.resolve(),
        )

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings.from_environment()
