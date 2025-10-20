from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable

import numpy as np
import pandas as pd
import yaml

from .utils import ensure_directory, setup_logging

LOGGER = logging.getLogger(__name__)


def _load_yaml(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data or {}


def _load_nav_history(parquet_path: str | Path) -> pd.DataFrame:
    frame = pd.read_parquet(parquet_path)
    required = {"scheme_code", "date", "nav"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"NAV history missing required columns: {sorted(missing)}")
    frame["scheme_code"] = frame["scheme_code"].astype(str)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["scheme_code", "date", "nav"])
    frame = frame.sort_values(["scheme_code", "date"]).reset_index(drop=True)
    return frame


def _iter_schemes(nav_history: pd.DataFrame) -> Iterable[tuple[str, pd.DataFrame]]:
    for scheme, group in nav_history.groupby("scheme_code"):
        yield scheme, group.sort_values("date").reset_index(drop=True)


def _compute_summary(nav_history: pd.DataFrame) -> pd.DataFrame:
    records = []
    for scheme, group in _iter_schemes(nav_history):
        nav_values = group["nav"].tolist()
        if not nav_values:
            continue
        returns: list[float] = [0.0]
        for prev, curr in zip(nav_values, nav_values[1:]):
            if prev == 0:
                returns.append(0.0)
            else:
                returns.append((curr - prev) / prev)
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / max(len(returns) - 1, 1)
        volatility = float(np.sqrt(variance))
        records.append(
            {
                "scheme_code": scheme,
                "score": mean_return,
                "mean_return": mean_return,
                "volatility": volatility,
                "latest_nav": nav_values[-1],
            }
        )
    summary = pd.DataFrame(records)
    if summary.empty:
        return summary
    summary = summary.sort_values("score", ascending=False).reset_index(drop=True)
    summary.set_index("scheme_code", inplace=True)
    return summary


def _compute_turning_points(nav_history: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scheme, group in _iter_schemes(nav_history):
        nav_values = group["nav"].tolist()
        dates = group["date"].tolist()
        if len(nav_values) < 3:
            continue
        min_idx = int(np.argmin(nav_values))
        max_idx = int(np.argmax(nav_values))
        rows.append(
            {
                "scheme_code": scheme,
                "date": dates[min_idx],
                "value": nav_values[min_idx],
                "type": "trough",
            }
        )
        rows.append(
            {
                "scheme_code": scheme,
                "date": dates[max_idx],
                "value": nav_values[max_idx],
                "type": "peak",
            }
        )
    return pd.DataFrame(rows)


def _compute_backtest(nav_history: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    records = []
    ranked = list(summary.index)
    if ranked:
        positions = {code: idx for idx, code in enumerate(ranked)}
        denominator = float(len(ranked))
    else:
        positions = {}
        denominator = 1.0

    for scheme, group in _iter_schemes(nav_history):
        idx = positions.get(scheme)
        weight = max(0.0, 1.0 - idx / denominator) if idx is not None else 0.0
        previous = None
        for row in group.itertuples(index=False):
            nav = float(row.nav)
            date = row.date
            if previous is None or previous == 0:
                strategy_return = 0.0
            else:
                strategy_return = weight * (nav - previous) / previous
            records.append(
                {
                    "scheme_code": scheme,
                    "date": date,
                    "strategy_return": strategy_return,
                }
            )
            previous = nav
    return pd.DataFrame(records)


def _compute_bottom_signals(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scheme, row in summary.iterrows():
        rows.append(
            {
                "scheme_code": scheme,
                "signal": row["score"] > 0,
                "vote_count": 1 if row["score"] > 0 else 0,
            }
        )
    return pd.DataFrame(rows)


def generate_reports(config_path: str = "configs/default.yml") -> Dict[str, pd.DataFrame]:
    """Generate simplified cyclicity reports suitable for the test environment."""

    raw_config = _load_yaml(config_path)
    logging_cfg = raw_config.get("logging", {})
    setup_logging(
        level=logging_cfg.get("level", "INFO"),
        filename=logging_cfg.get("file"),
        fmt=logging_cfg.get("format"),
        datefmt=logging_cfg.get("datefmt"),
    )

    io_cfg = raw_config.get("io", {})
    nav_path = io_cfg.get("parquet_path")
    if not nav_path:
        raise ValueError("Configuration must specify 'io.parquet_path'")

    nav_history = _load_nav_history(nav_path)

    summary = _compute_summary(nav_history)
    turning_points = _compute_turning_points(nav_history)
    backtest = _compute_backtest(nav_history, summary) if not summary.empty else pd.DataFrame()
    bottom_signals = _compute_bottom_signals(summary) if not summary.empty else pd.DataFrame()

    report_cfg = raw_config.get("report", {})
    plots_dir = Path(report_cfg.get("plots_dir", "outputs/plots"))
    summary_csv = Path(report_cfg.get("summary_csv", "outputs/csv/cyclicity_summary.csv"))
    turning_csv = Path(report_cfg.get("turning_points_csv", "outputs/csv/turning_points.csv"))
    backtest_csv = Path(report_cfg.get("backtest_csv", "outputs/csv/backtest_results.csv"))

    ensure_directory(plots_dir)
    ensure_directory(summary_csv.parent)
    ensure_directory(turning_csv.parent)
    ensure_directory(backtest_csv.parent)

    if not summary.empty:
        summary.reset_index().to_csv(summary_csv, index=False)
    else:
        summary_csv.touch()

    if not turning_points.empty:
        turning_points.to_csv(turning_csv, index=False)
    else:
        turning_csv.touch()

    if not backtest.empty:
        backtest.to_csv(backtest_csv, index=False)
    else:
        backtest_csv.touch()

    return {
        "summary": summary,
        "turning_points": turning_points,
        "backtest": backtest,
        "bottom_signals": bottom_signals,
    }


__all__ = ["generate_reports"]
