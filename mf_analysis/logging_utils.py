from __future__ import annotations

import logging
from typing import Mapping


def configure_logging(settings: Mapping[str, str] | None) -> None:
    """Configure global logging based on config settings."""
    settings = settings or {}
    logging.basicConfig(
        level=getattr(logging, str(settings.get("level", "INFO")).upper()),
        format=settings.get("format", "%(levelname)s:%(name)s:%(message)s"),
        datefmt=settings.get("datefmt"),
    )
