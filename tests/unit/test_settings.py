"""Tests for application settings."""
import pytest

from config.settings import Settings


def test_settings_defaults(monkeypatch, tmp_path):
    monkeypatch.setattr("config.settings.PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("BUSINESSFLOW_MAX_UPLOAD_MB", raising=False)
    monkeypatch.delenv("BUSINESSFLOW_ENVIRONMENT", raising=False)
    settings = Settings.from_environment()
    assert settings.environment == "development"
    assert settings.max_upload_mb == 25
    assert settings.database_url.startswith("sqlite:///")


@pytest.mark.parametrize("value", ["0", "501", "not-a-number", "1.5"])
def test_settings_reject_invalid_upload_limit(monkeypatch, value):
    monkeypatch.setenv("BUSINESSFLOW_MAX_UPLOAD_MB", value)
    with pytest.raises(ValueError, match="BUSINESSFLOW_MAX_UPLOAD_MB"):
        Settings.from_environment()


@pytest.mark.parametrize("value", ["", "not-a-url", "mysql://user:pass@host/db"])
def test_settings_reject_invalid_database_url(monkeypatch, value):
    monkeypatch.setenv("BUSINESSFLOW_DATABASE_URL", value)
    with pytest.raises(ValueError, match="BUSINESSFLOW_DATABASE_URL"):
        Settings.from_environment()


def test_settings_accepts_postgresql_driver_url(monkeypatch):
    monkeypatch.setenv("BUSINESSFLOW_DATABASE_URL", "postgresql+psycopg://user:secret@localhost:5432/businessflow")
    assert Settings.from_environment().database_url.startswith("postgresql+psycopg://")


def test_settings_reject_invalid_log_level(monkeypatch):
    monkeypatch.setenv("BUSINESSFLOW_LOG_LEVEL", "TRACE")
    with pytest.raises(ValueError, match="BUSINESSFLOW_LOG_LEVEL"):
        Settings.from_environment()


def test_settings_reject_invalid_environment(monkeypatch):
    monkeypatch.setenv("BUSINESSFLOW_ENVIRONMENT", "staging")
    with pytest.raises(ValueError, match="BUSINESSFLOW_ENVIRONMENT"):
        Settings.from_environment()
