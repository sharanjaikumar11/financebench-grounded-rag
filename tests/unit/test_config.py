import pytest

from rag_system.config import ConfigurationError, Settings


def test_settings_reads_safe_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    settings = Settings.from_environment()

    assert settings.log_level == "INFO"
    assert settings.gemini_api_key is None
    assert settings.gemini_thinking_level == "low"
    with pytest.raises(ConfigurationError):
        settings.require_gemini_key()


def test_settings_validates_log_level_and_reads_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    assert Settings.from_environment().require_gemini_key() == "test-key"

    monkeypatch.setenv("LOG_LEVEL", "invalid")
    with pytest.raises(ConfigurationError):
        Settings.from_environment()
