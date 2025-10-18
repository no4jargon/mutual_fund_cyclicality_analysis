"""Spectral analysis utilities."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
from scipy import signal

from .utils import spectral_sharpness

LOGGER = logging.getLogger(__name__)


@dataclass
class WelchConfig:
    nperseg: int = 64
    noverlap: int = 32


@dataclass
class LombScargleConfig:
    minimum_frequency: float = 0.02
    maximum_frequency: float = 0.5
    samples_per_peak: int = 5


@dataclass
class SpectrumBand:
    low: float = 0.02
    high: float = 0.35


@dataclass
class SpectrumConfig:
    method: str = "welch"
    welch: WelchConfig = WelchConfig()
    lomb_scargle: LombScargleConfig = LombScargleConfig()
    band: SpectrumBand = SpectrumBand()


@dataclass
class SpectrumResult:
    frequencies: np.ndarray
    power: np.ndarray
    dominant_frequency: float
    dominant_period: float
    sharpness: float


def compute_spectrum(series: pd.Series, config: SpectrumConfig) -> SpectrumResult:
    method = config.method.lower()
    if method == "welch":
        freq, power = _welch_spectrum(series, config.welch)
    elif method in {"lomb", "lomb_scargle"}:
        freq, power = _lomb_scargle_spectrum(series, config.lomb_scargle)
    else:
        raise ValueError(f"Unknown spectrum method: {config.method}")

    LOGGER.debug("Computed spectrum using %s method", method)

    band_mask = (freq >= config.band.low) & (freq <= config.band.high)
    if not np.any(band_mask):
        LOGGER.warning("No spectral content in configured band %s", config.band)
        dominant_freq = float("nan")
        dominant_period = float("nan")
        sharpness = float("nan")
    else:
        band_freq = freq[band_mask]
        band_power = power[band_mask]
        idx = int(np.argmax(band_power))
        dominant_freq = float(band_freq[idx])
        dominant_period = float(np.inf if dominant_freq == 0 else 1.0 / dominant_freq)
        sharpness = spectral_sharpness(band_freq, band_power, dominant_freq)

    return SpectrumResult(freq, power, dominant_freq, dominant_period, sharpness)


def _welch_spectrum(series: pd.Series, config: WelchConfig) -> Tuple[np.ndarray, np.ndarray]:
    values = series.to_numpy(dtype=float)
    values = values - np.nanmean(values)
    freq, power = signal.welch(
        values,
        nperseg=min(len(values), config.nperseg),
        noverlap=config.noverlap,
        return_onesided=True,
        detrend="constant",
        scaling="density",
    )
    if len(freq) > 1:
        return freq[1:], power[1:]
    return freq, power


def _lomb_scargle_spectrum(series: pd.Series, config: LombScargleConfig) -> Tuple[np.ndarray, np.ndarray]:
    times = np.arange(len(series), dtype=float)
    values = series.to_numpy(dtype=float)
    values = values - np.nanmean(values)

    min_freq = config.minimum_frequency
    max_freq = config.maximum_frequency
    if max_freq <= min_freq:
        raise ValueError("maximum_frequency must be greater than minimum_frequency")

    freq = np.linspace(min_freq, max_freq, int((max_freq - min_freq) * config.samples_per_peak * len(series)))
    if len(freq) == 0:
        raise ValueError("Frequency grid for Lomb-Scargle is empty")
    power = signal.lombscargle(times, values, freq)
    return freq, power


__all__ = [
    "SpectrumConfig",
    "SpectrumResult",
    "compute_spectrum",
]
