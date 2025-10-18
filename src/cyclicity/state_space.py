"""State-space stochastic cycle estimation."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from statsmodels.tsa.statespace.structural import UnobservedComponents
except ImportError:  # pragma: no cover
    UnobservedComponents = None  # type: ignore


@dataclass
class StateSpaceConfig:
    cycle_period: float = 60.0
    damping: float = 0.9


def estimate_cycle(series: pd.Series, config: StateSpaceConfig) -> Dict[str, float | pd.Series]:
    """Fit a stochastic cycle state-space model and return diagnostics."""

    if UnobservedComponents is None:
        LOGGER.warning("statsmodels is not installed; state-space estimation disabled")
        return {
            "cycle": pd.Series(np.nan, index=series.index, name=f"{series.name}_cycle"),
            "persistence": np.nan,
            "signal_to_noise": np.nan,
        }

    mod = UnobservedComponents(
        series,
        level="local level",
        cycle=True,
        stochastic_cycle=True,
        damped_cycle=True,
        cycle_period=max(config.cycle_period, 2),
    )
    try:
        res = mod.fit(disp=False)
    except Exception as err:  # pragma: no cover - statsmodels specific
        LOGGER.error("State-space model failed: %s", err)
        return {
            "cycle": pd.Series(np.nan, index=series.index, name=f"{series.name}_cycle"),
            "persistence": np.nan,
            "signal_to_noise": np.nan,
        }

    cycle = pd.Series(res.cycle_smoothed, index=series.index, name=f"{series.name}_cycle")
    resid = pd.Series(res.resid, index=series.index)

    if cycle.isna().all() or resid.isna().all():
        persistence = np.nan
        snr = np.nan
    else:
        shifted = cycle.shift(1)
        valid = ~(cycle.isna() | shifted.isna())
        valid_cycle = cycle[valid]
        if len(valid_cycle) > 1:
            corr = np.corrcoef(valid_cycle.iloc[:-1], valid_cycle.iloc[1:])[0, 1]
            persistence = float(corr)
        else:
            persistence = np.nan
        signal_var = float(np.nanvar(cycle))
        noise_var = float(np.nanvar(resid))
        snr = float(signal_var / noise_var) if noise_var > 0 else np.nan

    return {"cycle": cycle, "persistence": persistence, "signal_to_noise": snr}


__all__ = ["StateSpaceConfig", "estimate_cycle"]
