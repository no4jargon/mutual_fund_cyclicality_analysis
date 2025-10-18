from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

from cyclicity.report import generate_reports

from mf_analysis.backtest import run_backtest
from mf_analysis.config import load_config
from mf_analysis.logging_utils import configure_logging
from mf_analysis.pipeline import get_signals_path, run_analysis_pipeline

logger = logging.getLogger(__name__)


DEFAULT_SIMPLE_CONFIG = "configs/simple.yaml"
DEFAULT_ADVANCED_CONFIG = "configs/default.yml"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mutual fund cyclicality analysis and backtesting CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def _add_simple_arguments(subparser: argparse.ArgumentParser) -> None:
        subparser.set_defaults(default_config=DEFAULT_SIMPLE_CONFIG)
        subparser.add_argument(
            "--config",
            action="append",
            dest="config_overrides",
            help=(
                "Optional configuration override YAML file for the simple pipeline. "
                "Can be supplied multiple times."
            ),
        )
        subparser.add_argument(
            "--schemes",
            nargs="+",
            help="Optional list of scheme codes to filter the analysis/backtest.",
        )

    report_parser = subparsers.add_parser(
        "report",
        help="Run the advanced cyclicality report pipeline",
    )
    report_parser.add_argument(
        "--config",
        default=DEFAULT_ADVANCED_CONFIG,
        help=(
            "Path to the advanced cyclicality configuration file."
            f" Defaults to {DEFAULT_ADVANCED_CONFIG}."
        ),
    )

    analyze_parser = subparsers.add_parser("analyze", help="Run the simple analysis pipeline")
    _add_simple_arguments(analyze_parser)

    backtest_parser = subparsers.add_parser("backtest", help="Run the backtesting workflow")
    _add_simple_arguments(backtest_parser)

    backtest_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Recompute analysis outputs before running the backtest.",
    )

    return parser.parse_args()


def _load_configuration(default_config: str, overrides: Iterable[str]) -> dict:
    config_paths = [default_config, *overrides]
    return load_config(config_paths)


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
    if args.command == "report":
        config_path = Path(args.config)
        logger.info("Running advanced cyclicality reports using %s", config_path)
        generate_reports(str(config_path))
        return

    overrides = args.config_overrides or []
    config = _load_configuration(args.default_config, overrides)
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
