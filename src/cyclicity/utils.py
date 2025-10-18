"""Utility helpers for the cyclicity analysis pipeline."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

import numpy as np
import pandas as pd
from scipy import signal
from scipy.linalg import toeplitz


LOGGER = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for caching intermediate artifacts."""

    enabled: bool = False
    directory: str = "cache"

    def cache_path(self, *parts: str) -> Path:
        path = Path(self.directory).joinpath(*parts)
        if self.enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
        return path


class CacheManager:
    """Simple JSON/Parquet cache for intermediate computations."""

    def __init__(self, config: CacheConfig) -> None:
        self.config = config

    def load_json(self, key: str) -> Optional[Dict[str, Any]]:
        if not self.config.enabled:
            return None
        path = self.config.cache_path(f"{key}.json")
        if not path.exists():
            return None
        LOGGER.debug("Loading cached JSON from %s", path)
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def dump_json(self, key: str, payload: Mapping[str, Any]) -> None:
        if not self.config.enabled:
            return
        path = self.config.cache_path(f"{key}.json")
        LOGGER.debug("Caching JSON payload to %s", path)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, default=_json_default, indent=2)

    def load_frame(self, key: str) -> Optional[pd.DataFrame]:
        if not self.config.enabled:
            return None
        path = self.config.cache_path(f"{key}.parquet")
        if not path.exists():
            return None
        LOGGER.debug("Loading cached frame from %s", path)
        return pd.read_parquet(path)

    def dump_frame(self, key: str, frame: pd.DataFrame) -> None:
        if not self.config.enabled:
            return
        path = self.config.cache_path(f"{key}.parquet")
        LOGGER.debug("Caching frame to %s", path)
        frame.to_parquet(path)


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)!r} is not JSON serializable")


def rolling_autocorrelation(series: pd.Series, window: int, lag: int) -> pd.Series:
    """Compute rolling autocorrelation for the provided lag."""

    if lag >= window:
        raise ValueError("Lag must be smaller than window size")

    def _acf(values: np.ndarray) -> float:
        if np.all(np.isnan(values)):
            return np.nan
        centered = values - np.nanmean(values)
        if np.nanstd(centered) == 0:
            return np.nan
        return np.nanmean(centered[lag:] * centered[:-lag]) / (np.nanstd(centered) ** 2)

    return series.rolling(window=window, min_periods=window).apply(_acf, raw=True)


def autocorrelation_strength(series: pd.Series, lags: Sequence[int]) -> Dict[int, float]:
    """Return lag autocorrelation coefficients for the provided lags."""

    result: Dict[int, float] = {}
    values = series.to_numpy(dtype=float)
    values = values - np.nanmean(values)
    denom = np.nansum(values ** 2)
    if denom == 0:
        return {lag: np.nan for lag in lags}
    for lag in lags:
        if lag <= 0 or lag >= len(values):
            result[lag] = np.nan
            continue
        num = np.nansum(values[lag:] * values[:-lag])
        result[lag] = float(num / denom)
    return result


def partial_autocorrelation(series: pd.Series, lag: int) -> float:
    """Compute the partial autocorrelation using a Yule-Walker regression."""

    if lag <= 0:
        raise ValueError("Lag must be positive")
    x = series.to_numpy(dtype=float)
    x = x - np.nanmean(x)
    if np.isnan(x).all():
        return np.nan
    if len(x) <= lag:
        return np.nan
    # Build Toeplitz matrix for autocovariances
    acov = [np.nansum(x[: len(x) - k] * x[k:]) / len(x) for k in range(lag + 1)]
    design = toeplitz(acov[:-1])
    rhs = np.asarray(acov[1:])
    try:
        coeffs = np.linalg.solve(design, rhs)
    except np.linalg.LinAlgError:
        return np.nan
    return float(coeffs[-1])


def spectral_sharpness(frequencies: np.ndarray, power: np.ndarray, target_freq: float) -> float:
    """Estimate how sharp the dominant peak is around the target frequency."""

    if len(frequencies) == 0 or len(power) == 0:
        return float("nan")
    idx = np.argmin(np.abs(frequencies - target_freq))
    peak_power = power[idx]
    if idx == 0 or idx == len(power) - 1:
        return float("nan")
    neighborhood = power[max(0, idx - 2) : idx + 3]
    baseline = np.nanmean(np.delete(neighborhood, idx - max(0, idx - 2)))
    if np.isnan(baseline) or baseline == 0:
        return float("nan")
    return float((peak_power - baseline) / baseline)


def robust_zscore(values: Sequence[float]) -> np.ndarray:
    """Compute robust z-scores using the median and MAD."""

    arr = np.asarray(list(values), dtype=float)
    median = np.nanmedian(arr)
    mad = np.nanmedian(np.abs(arr - median))
    if mad == 0 or np.isnan(mad):
        return np.zeros_like(arr)
    return 0.6745 * (arr - median) / mad


def weighted_average(scores: Mapping[str, float], weights: Mapping[str, float]) -> float:
    total_weight = 0.0
    total_score = 0.0
    for key, weight in weights.items():
        score = scores.get(key)
        if score is None or np.isnan(score):
            continue
        total_weight += weight
        total_score += score * weight
    if total_weight == 0:
        return float("nan")
    return total_score / total_weight


def setup_logging(level: str = "INFO", filename: Optional[str] = None) -> None:
    """Initialise logging and ensure the target directory exists."""

    log_kwargs: Dict[str, Any] = {
        "level": getattr(logging, level.upper(), logging.INFO),
        "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
        "filemode": "a",
    }

    if filename:
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_kwargs["filename"] = str(log_path)

    logging.basicConfig(**log_kwargs)
    if filename:
        # Also add console handler when logging to file
        console = logging.StreamHandler()
        console.setLevel(getattr(logging, level.upper(), logging.INFO))
        console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logging.getLogger().addHandler(console)


def ensure_directory(path: str | os.PathLike[str]) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def with_progress(iterable: Iterable[Any], description: str) -> Iterable[Any]:
    try:
        from tqdm import tqdm

        return tqdm(iterable, desc=description)
    except ImportError:  # pragma: no cover - tqdm may be absent
        LOGGER.warning("tqdm is not installed; progress bars will be disabled")
        return iterable
