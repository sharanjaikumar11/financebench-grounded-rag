"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Raised when required application configuration is invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    log_level: str
    answer_provider: str
    gemini_api_key: str | None
    gemini_model: str
    gemini_fallback_model: str
    gemini_thinking_level: str
    groq_api_key: str | None
    groq_model: str

    @classmethod
    def from_environment(cls) -> Settings:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigurationError("LOG_LEVEL must be a standard Python logging level")
        api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
        answer_provider = os.getenv("ANSWER_PROVIDER", "gemini").strip().casefold()
        if answer_provider not in {"gemini", "groq"}:
            raise ConfigurationError("ANSWER_PROVIDER must be either 'gemini' or 'groq'")
        return cls(
            log_level,
            answer_provider,
            api_key,
            os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite"),
            os.getenv("GEMINI_THINKING_LEVEL", "minimal"),
            os.getenv("GROQ_API_KEY", "").strip() or None,
            os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        )

    def require_gemini_key(self) -> str:
        if self.gemini_api_key is None:
            raise ConfigurationError("GEMINI_API_KEY is required for answer generation")
        return self.gemini_api_key

    def require_groq_key(self) -> str:
        if self.groq_api_key is None:
            raise ConfigurationError("GROQ_API_KEY is required when ANSWER_PROVIDER=groq")
        return self.groq_api_key
