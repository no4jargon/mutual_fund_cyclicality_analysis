from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import yaml

logger = logging.getLogger(__name__)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _deep_update(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            base[key] = _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_config(config_paths: Iterable[str] | None = None) -> dict:
    """Load the default configuration and apply optional overrides."""
    config_paths = list(config_paths or [])
    default_path = Path("configs/default.yaml")
    if not default_path.exists():
        raise FileNotFoundError(
            "The default configuration file configs/default.yaml was not found."
        )

    config = _load_yaml(default_path)

    for path_str in config_paths:
        override_path = Path(path_str)
        if not override_path.exists():
            raise FileNotFoundError(f"Config override not found: {override_path}")
        override = _load_yaml(override_path)
        config = _deep_update(config, override)
        logger.info("Loaded configuration override from %s", override_path)

    return config
