"""Hilbert transform based cycle extraction."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd
from scipy import signal

LOGGER = logging.getLogger(__name__)


@dataclass
class HilbertConfig:
    lowcut: float = 0.02
    highcut: float = 0.35
    fs: float = 1.0
    order: int = 3


def hilbert_cycle(series: pd.Series, config: HilbertConfig) -> Dict[str, np.ndarray | float]:
    """Compute the analytic signal and cycle metrics."""

    if config.highcut <= config.lowcut:
        raise ValueError("highcut must be greater than lowcut")

    nyquist = 0.5 * config.fs
    low = config.lowcut / nyquist
    high = min(config.highcut / nyquist, 0.999)
    if high <= 0 or low <= 0:
        raise ValueError("Band-pass cutoff must be positive")

    b, a = signal.butter(config.order, [low, high], btype="band")
    values = series.to_numpy(dtype=float)
    values = values - np.nanmean(values)
    filtered = signal.filtfilt(b, a, values)
    analytic = signal.hilbert(filtered)
    amplitude_envelope = np.abs(analytic)
    instantaneous_phase = np.unwrap(np.angle(analytic))
    phase_coherence = float(np.abs(np.mean(np.exp(1j * instantaneous_phase))))

    cycle_estimate = pd.Series(filtered, index=series.index, name=f"{series.name}_cycle")
    amplitude = pd.Series(amplitude_envelope, index=series.index, name=f"{series.name}_amplitude")
    phase = pd.Series(instantaneous_phase, index=series.index, name=f"{series.name}_phase")

    inst_freq = np.diff(instantaneous_phase) / (2 * np.pi) * config.fs
    if len(inst_freq) == 0 or np.all(np.isnan(inst_freq)):
        median_period = float("nan")
    else:
        median_freq = np.nanmedian(np.abs(inst_freq))
        median_period = float(np.inf if median_freq == 0 else 1.0 / median_freq)

    return {
        "cycle": cycle_estimate,
        "amplitude": amplitude,
        "phase": phase,
        "phase_coherence": phase_coherence,
        "median_period": median_period,
    }


__all__ = ["HilbertConfig", "hilbert_cycle"]
