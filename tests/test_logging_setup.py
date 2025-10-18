from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path


def _load_setup_logging():
    utils_path = Path(__file__).resolve().parents[1] / "src" / "cyclicity" / "utils.py"
    spec = importlib.util.spec_from_file_location("cyclicity.utils", utils_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.setup_logging


setup_logging = _load_setup_logging()


def test_setup_logging_creates_parent_directory(tmp_path) -> None:
    root_logger = logging.getLogger()
    previous_handlers = root_logger.handlers[:]
    previous_level = root_logger.level

    for handler in previous_handlers:
        root_logger.removeHandler(handler)

    log_file = tmp_path / "outputs" / "metrics" / "pipeline.log"

    try:
        setup_logging(filename=str(log_file))
        logging.getLogger(__name__).info("trigger file handler")

        for handler in root_logger.handlers:
            handler.flush()

        assert log_file.parent.exists()
        assert log_file.exists()
    finally:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()
        root_logger.setLevel(previous_level)
        for handler in previous_handlers:
            root_logger.addHandler(handler)
