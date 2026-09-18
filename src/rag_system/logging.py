"""Consistent application logging configuration."""

from __future__ import annotations

import logging


def configure_logging(level: str) -> None:
    """Configure concise, timestamped logs once for the application process."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )
