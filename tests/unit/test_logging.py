"""Tests for logging configuration."""
import logging

import pytest

from logging_config.setup import configure_logging


def test_configure_logging_accepts_valid_level():
    configure_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING


def test_configure_logging_rejects_unknown_level():
    with pytest.raises(ValueError, match="Unsupported logging level"):
        configure_logging("NOT_A_LEVEL")
