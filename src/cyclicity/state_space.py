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

    prepared = series.copy()
    if isinstance(prepared.index, (pd.DatetimeIndex, pd.PeriodIndex)):
        freq = getattr(prepared.index, "freq", None)
        if freq is None:
            inferred = pd.infer_freq(prepared.index)
            if inferred is not None:
                try:
                    prepared = prepared.asfreq(inferred)
                except (ValueError, TypeError):
                    LOGGER.debug("Unable to asfreq series to inferred frequency %s", inferred)
    period = float(max(config.cycle_period, 2.0))
    lower_bound = max(period * 0.8, 2.0)
    upper_bound = max(period * 1.2, lower_bound + 1.0)

    mod = UnobservedComponents(
        prepared,
        level="local level",
        cycle=True,
        stochastic_cycle=True,
        damped_cycle=True,
        cycle_period_bounds=(lower_bound, upper_bound),
    )
    try:
        res = mod.fit(disp=False)
    except Exception as err:  # pragma: no cover - statsmodels specific
        LOGGER.error("State-space model failed: %s", err)
        return {
            "cycle": pd.Series(np.nan, index=prepared.index, name=f"{series.name}_cycle"),
            "persistence": np.nan,
            "signal_to_noise": np.nan,
        }

    if hasattr(res, "cycle_smoothed"):
        cycle_values = res.cycle_smoothed
    elif hasattr(res, "cycle") and hasattr(res.cycle, "smoothed"):
        cycle_values = res.cycle.smoothed
    else:
        LOGGER.warning("State-space results do not expose smoothed cycle; returning NaNs")
        cycle_values = np.full(len(prepared), np.nan)

    cycle = pd.Series(cycle_values, index=prepared.index, name=f"{series.name}_cycle")
    resid = pd.Series(res.resid, index=prepared.index)

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
