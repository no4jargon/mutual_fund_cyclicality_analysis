from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Mapping

DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(
    level: str = "INFO",
    filename: str | os.PathLike[str] | None = None,
    *,
    fmt: str | None = None,
    datefmt: str | None = None,
) -> None:
    """Initialise logging with optional file output and console mirroring."""

    log_level = getattr(logging, str(level).upper(), logging.INFO)
    log_kwargs: dict[str, Any] = {
        "level": log_level,
        "format": fmt or DEFAULT_FORMAT,
        "datefmt": datefmt,
    }

    log_path: Path | None = None
    if filename:
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_kwargs["filename"] = str(log_path)
        log_kwargs["filemode"] = "a"

    logging.basicConfig(**log_kwargs)

    if log_path is not None:
        root_logger = logging.getLogger()
        console_formatter = logging.Formatter(fmt or DEFAULT_FORMAT, datefmt=datefmt)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)


def configure_logging(settings: Mapping[str, object] | None) -> None:
    """Configure global logging based on config settings."""

    settings = settings or {}
    setup_logging(
        level=str(settings.get("level", "INFO")),
        filename=settings.get("file"),
        fmt=settings.get("format"),
        datefmt=settings.get("datefmt"),
    )
