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


def test_settings_reject_invalid_upload_limit(monkeypatch):
    monkeypatch.setenv("BUSINESSFLOW_MAX_UPLOAD_MB", "0")
    with pytest.raises(ValueError, match="between 1 and 500"):
        Settings.from_environment()


def test_settings_reject_invalid_environment(monkeypatch):
    monkeypatch.setenv("BUSINESSFLOW_ENVIRONMENT", "staging")
    with pytest.raises(ValueError, match="BUSINESSFLOW_ENVIRONMENT"):
        Settings.from_environment()
