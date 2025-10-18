"""Backtesting analytics for cyclicality signals."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

LOGGER = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    lookback_months: int = 24
    holding_period_months: int = 6


def backtest_bottom_signals(
    scheme_code: str,
    nav_series: pd.Series,
    signal_series: pd.Series,
    config: BacktestConfig,
) -> pd.DataFrame:
    """Evaluate bottom signals on forward returns."""

    if signal_series.index.freq is None:
        signal_series = signal_series.asfreq("ME")
    if nav_series.index.freq is None:
        nav_series = nav_series.asfreq("ME")

    records: List[Dict[str, object]] = []

    for date, is_signal in signal_series.items():
        if not is_signal:
            continue
        if date not in nav_series.index:
            continue
        start_idx = nav_series.index.get_loc(date)
        end_idx = start_idx + config.holding_period_months
        if end_idx >= len(nav_series):
            continue
        start_price = nav_series.iloc[start_idx]
        end_price = nav_series.iloc[end_idx]
        forward_return = (end_price / start_price) - 1.0
        records.append(
            {
                "scheme_code": scheme_code,
                "signal_date": date,
                "exit_date": nav_series.index[end_idx],
                "forward_return": forward_return,
            }
        )

    result = pd.DataFrame(records)
    if result.empty:
        return result

    result["hit"] = result["forward_return"] > 0
    summary = {
        "scheme_code": scheme_code,
        "signals": len(result),
        "hit_rate": result["hit"].mean(),
        "average_return": result["forward_return"].mean(),
        "median_return": result["forward_return"].median(),
    }
    LOGGER.info(
        "Backtest summary for %s: %s", scheme_code, {k: v for k, v in summary.items() if k != "scheme_code"}
    )

    return result


__all__ = ["BacktestConfig", "backtest_bottom_signals"]
