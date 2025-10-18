"""Harmonic regression scoring utilities."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Sequence

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)


@dataclass
class HarmonicConfig:
    harmonics: Sequence[int] = field(default_factory=lambda: [1, 2])
    regularization: float = 1e-3


def harmonic_regression(series: pd.Series, period: float, config: HarmonicConfig) -> Dict[str, float]:
    """Fit harmonic regression and compute goodness-of-fit metrics."""

    if np.isnan(period) or period <= 0:
        return {"r2": np.nan, "amplitude": np.nan, "rmse": np.nan}

    times = np.arange(len(series), dtype=float)
    omega = 2 * np.pi / period

    design_columns = [np.ones(len(series))]
    for harmonic in config.harmonics:
        design_columns.append(np.sin(harmonic * omega * times))
        design_columns.append(np.cos(harmonic * omega * times))
    X = np.column_stack(design_columns)

    y = series.to_numpy(dtype=float)
    y = y - np.nanmean(y)

    ridge = config.regularization * np.eye(X.shape[1])
    beta = np.linalg.pinv(X.T @ X + ridge) @ X.T @ y
    yhat = X @ beta
    residuals = y - yhat

    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else np.nan
    rmse = float(np.sqrt(ss_res / len(series)))

    amplitude = float(np.sqrt(np.sum(beta[1:] ** 2))) if len(beta) > 1 else 0.0

    return {"r2": r2, "amplitude": amplitude, "rmse": rmse}


__all__ = ["HarmonicConfig", "harmonic_regression"]
