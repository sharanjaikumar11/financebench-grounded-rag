"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Raised when required application configuration is invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    log_level: str
    gemini_api_key: str | None
    gemini_model: str

    @classmethod
    def from_environment(cls) -> "Settings":
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigurationError("LOG_LEVEL must be a standard Python logging level")
        api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
        return cls(log_level, api_key, os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"))

    def require_gemini_key(self) -> str:
        if self.gemini_api_key is None:
            raise ConfigurationError("GEMINI_API_KEY is required for answer generation")
        return self.gemini_api_key
