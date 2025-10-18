from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import yaml

logger = logging.getLogger(__name__)

DEFAULT_SIMPLE_CONFIG = Path("configs/simple.yaml")


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
    """Load the simple pipeline configuration and apply optional overrides."""

    supplied_paths = list(config_paths or [])

    if supplied_paths:
        base_path = Path(supplied_paths[0])
        extra_paths = supplied_paths[1:]
    else:
        base_path = DEFAULT_SIMPLE_CONFIG
        extra_paths = []

    if not base_path.exists():
        raise FileNotFoundError(
            f"The base configuration file {base_path} was not found."
        )

    config = _load_yaml(base_path)

    for path_str in extra_paths:
        override_path = Path(path_str)
        if not override_path.exists():
            raise FileNotFoundError(f"Config override not found: {override_path}")
        override = _load_yaml(override_path)
        config = _deep_update(config, override)
        logger.info("Loaded configuration override from %s", override_path)

    return config
