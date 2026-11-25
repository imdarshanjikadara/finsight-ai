"""Tests for finsight.config."""

import pytest
from pydantic import ValidationError

from finsight.config import Settings


@pytest.fixture
def fake_env(monkeypatch):
    """Set fake settings for one test, so tests never touch the real .env."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setenv("SEC_USER_AGENT", "Test User test@example.com")


def test_settings_are_read_from_environment(fake_env):
    # Act
    settings = Settings(_env_file=None)

    # Assert
    assert settings.gemini_api_key.get_secret_value() == "test-key-123"
    assert settings.sec_user_agent == "Test User test@example.com"


def test_api_key_is_masked_when_printed(fake_env):
    settings = Settings(_env_file=None)

    assert "test-key-123" not in str(settings.gemini_api_key)
    assert "test-key-123" not in repr(settings)


def test_missing_api_key_fails_fast(monkeypatch):
    # Arrange: the API key is deliberately missing
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("SEC_USER_AGENT", "Test User test@example.com")

    # Act + Assert: creating Settings must raise an error
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
