"""Series detrending utilities."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from statsmodels.tsa.filters.hp_filter import hpfilter
except ImportError:  # pragma: no cover
    hpfilter = None  # type: ignore


@dataclass
class DetrendConfig:
    method: str = "hp"
    hp_lambda: float = 129600.0
    returns_window: int = 3


def detrend_series(series: pd.Series, config: DetrendConfig) -> Tuple[pd.Series, pd.Series]:
    """Detrend a time-series using the configured method.

    Parameters
    ----------
    series:
        Series of prices (preferably in log-scale).
    config:
        :class:`DetrendConfig` specifying the detrending strategy.

    Returns
    -------
    residuals, trend:
        Two series aligned with the input index.
    """

    if config.method.lower() == "hp":
        return _hp_detrend(series, config.hp_lambda)
    if config.method.lower() == "returns":
        return _returns_detrend(series, config.returns_window)
    raise ValueError(f"Unknown detrending method: {config.method}")


def _hp_detrend(series: pd.Series, hp_lambda: float) -> Tuple[pd.Series, pd.Series]:
    if hpfilter is None:  # pragma: no cover - fallback path
        LOGGER.warning("statsmodels is not installed; falling back to moving average detrending")
        trend = series.rolling(window=12, min_periods=1, center=True).mean()
        residuals = series - trend
        return residuals, trend

    cycle, trend = hpfilter(series, lamb=hp_lambda)
    residuals = cycle
    residuals.name = f"{series.name}_resid"
    trend.name = f"{series.name}_trend"
    return residuals, trend


def _returns_detrend(series: pd.Series, window: int) -> Tuple[pd.Series, pd.Series]:
    if window <= 1:
        raise ValueError("returns_window must be greater than 1")

    positive = (series > 0).all()
    log_values = np.log(series) if positive else series
    returns = log_values.diff()
    trend_returns = returns.rolling(window=window, min_periods=1).mean()
    trend_component = trend_returns.cumsum().fillna(0) + log_values.iloc[0]

    if positive:
        trend = np.exp(trend_component)
        residuals = log_values - trend_component
    else:
        trend = trend_component
        residuals = log_values - trend_component

    residuals.name = f"{series.name}_resid"
    trend = pd.Series(trend, index=series.index, name=f"{series.name}_trend")
    residuals = pd.Series(residuals, index=series.index)
    return residuals, trend


__all__ = ["DetrendConfig", "detrend_series"]
