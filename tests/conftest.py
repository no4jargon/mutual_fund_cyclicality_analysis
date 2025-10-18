"""Common test configuration for deterministic behaviour."""
from __future__ import annotations

import random


def pytest_configure() -> None:
    random.seed(0)
