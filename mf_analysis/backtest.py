from __future__ import annotations

import logging

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from tqdm import tqdm

from .pipeline import ingest_data

logger = logging.getLogger(__name__)


def _prepare_signals(signals_path: Path, schemes: Iterable[str] | None) -> pd.DataFrame:
    if not signals_path.exists():
        raise FileNotFoundError(
            "Signal file not found. Run the analyze command first to generate signals."
        )
    logger.info("Loading precomputed signals from %s", signals_path)
    signals = pd.read_csv(signals_path, parse_dates=["date"])
    if schemes:
        schemes_set = set(schemes)
        signals = signals[signals["scheme_code"].isin(schemes_set)]
    if signals.empty:
        raise ValueError("No signals available for requested schemes.")
    return signals


def run_backtest(
    config: dict,
    signals_path: Path,
    schemes: Iterable[str] | None = None,
) -> pd.DataFrame:
    signals = _prepare_signals(signals_path, schemes)
    metadata_path = Path(config["data"]["metadata"])
    nav_history_path = Path(config["data"]["nav_history"])
    _, nav_history = ingest_data(metadata_path, nav_history_path, schemes)

    nav_history = nav_history[["scheme_code", "date", "nav"]]
    nav_history = nav_history.sort_values(["scheme_code", "date"])

    merged = signals.merge(nav_history, on=["scheme_code", "date"], how="left", suffixes=("_sig", ""))
    merged.rename(columns={"return_sig": "return"}, inplace=True)

    transaction_cost = float(config["backtest"].get("transaction_cost", 0.0))
    entry_threshold = float(config["backtest"].get("entry_threshold", 0.0))
    exit_threshold = float(config["backtest"].get("exit_threshold", entry_threshold))

    results: list[pd.DataFrame] = []
    for scheme_code, group in tqdm(
        merged.groupby("scheme_code"),
        desc="Running backtests",
        unit="fund",
    ):
        group = group.sort_values("date").copy()
        group["nav_return"] = group["nav"].pct_change().fillna(0.0)
        positions = np.zeros(len(group))
        open_position = False
        for idx, score in enumerate(group["score"].tolist()):
            if open_position:
                if score < exit_threshold:
                    open_position = False
                else:
                    positions[idx] = 1.0
            else:
                if score > entry_threshold:
                    open_position = True
                    positions[idx] = 1.0
        position_series = pd.Series(positions, index=group.index)
        group["position"] = position_series
        group["position_change"] = group["position"].diff().abs().fillna(0.0)
        group["strategy_return"] = (
            group["position"].shift(1).fillna(0.0) * group["nav_return"]
            - group["position_change"] * transaction_cost
        )
        group["cumulative_return"] = (1 + group["strategy_return"]).cumprod()
        group["drawdown"] = group["cumulative_return"].cummax() - group["cumulative_return"]
        results.append(group)

    backtest_df = pd.concat(results, ignore_index=True)
    base_dir = Path(config["output"].get("base_dir", "outputs"))
    backtest_dir = base_dir / config["output"].get("backtest_dir", "backtests")
    backtest_dir.mkdir(parents=True, exist_ok=True)
    results_path = backtest_dir / "backtest_timeseries.csv"
    summary_path = backtest_dir / "backtest_summary.csv"

    backtest_df.to_csv(results_path, index=False)

    def _sharpe(series: pd.Series) -> float:
        std = series.std()
        if std == 0 or np.isnan(std):
            return float("nan")
        return float(np.sqrt(252) * series.mean() / std)

    summary = (
        backtest_df.groupby("scheme_code")
        .agg(
            total_return=("strategy_return", lambda s: (1 + s).prod() - 1),
            volatility=("strategy_return", "std"),
            sharpe=("strategy_return", _sharpe),
            max_drawdown=("drawdown", "max"),
        )
        .reset_index()
    )
    summary.to_csv(summary_path, index=False)
    logger.info("Wrote backtest time series to %s", results_path)
    logger.info("Wrote backtest summary to %s", summary_path)
    return backtest_df
