from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

from mf_analysis.backtest import run_backtest
from mf_analysis.config import load_config
from mf_analysis.logging_utils import configure_logging
from mf_analysis.pipeline import get_signals_path, run_analysis_pipeline

logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mutual fund cyclicality analysis and backtesting CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def _add_shared_arguments(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--config",
            action="append",
            default=[],
            help="Optional configuration override YAML file. Can be supplied multiple times.",
        )
        subparser.add_argument(
            "--schemes",
            nargs="+",
            help="Optional list of scheme codes to filter the analysis/backtest.",
        )

    analyze_parser = subparsers.add_parser("analyze", help="Run the analysis pipeline")
    _add_shared_arguments(analyze_parser)

    backtest_parser = subparsers.add_parser("backtest", help="Run the backtesting workflow")
    _add_shared_arguments(backtest_parser)

    backtest_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Recompute analysis outputs before running the backtest.",
    )

    return parser.parse_args()


def _load_configuration(paths: Iterable[str]) -> dict:
    return load_config(paths)


def _ensure_signals(config: dict, schemes: Iterable[str] | None, refresh: bool) -> Path:
    signals_path = get_signals_path(config)
    if refresh or not signals_path.exists():
        if refresh:
            logger.info("Refreshing analysis outputs prior to backtest.")
        else:
            logger.info("Signals not found; running analysis pipeline to generate them.")
        artifacts = run_analysis_pipeline(config, schemes)
        signals_path = artifacts.signals_path
    return signals_path


def main() -> None:
    args = _parse_args()
    config = _load_configuration(args.config)
    configure_logging(config.get("logging"))

    schemes = args.schemes

    if args.command == "analyze":
        artifacts = run_analysis_pipeline(config, schemes)
        logger.info("Analysis complete. Signals written to %s", artifacts.signals_path)
    elif args.command == "backtest":
        signals_path = _ensure_signals(config, schemes, getattr(args, "refresh", False))
        backtest_df = run_backtest(config, signals_path, schemes)
        logger.info("Backtest complete for %d rows of data.", len(backtest_df))
    else:
        raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    main()
