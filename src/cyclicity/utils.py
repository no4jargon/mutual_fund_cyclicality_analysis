"""Utility helpers for the cyclicity analysis pipeline."""
from __future__ import annotations

import json
import logging
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

import numpy as np
import pandas as pd


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

    values = _series_to_floats(series)
    results: list[float] = []
    for idx in range(len(values)):
        if idx + 1 < window:
            results.append(math.nan)
            continue
        segment = values[idx - window + 1 : idx + 1]
        results.append(_segment_autocorrelation(segment, lag))
    return pd.Series(results, index=series.index)


def autocorrelation_strength(series: pd.Series, lags: Sequence[int]) -> Dict[int, float]:
    """Return lag autocorrelation coefficients for the provided lags."""

    centered = _centered_values(series)
    denom = sum(val * val for val in centered if not math.isnan(val))
    if denom == 0:
        return {lag: math.nan for lag in lags}

    result: Dict[int, float] = {}
    n = len(centered)
    for lag in lags:
        if lag <= 0 or lag >= n:
            result[lag] = math.nan
            continue
        total = 0.0
        count = 0
        for idx in range(n - lag):
            a = centered[idx]
            b = centered[idx + lag]
            if math.isnan(a) or math.isnan(b):
                continue
            total += a * b
            count += 1
        result[lag] = total / denom if count else math.nan
    return result


def partial_autocorrelation(series: pd.Series, lag: int) -> float:
    """Compute the partial autocorrelation using a Levinson-Durbin recursion."""

    if lag <= 0:
        raise ValueError("Lag must be positive")

    values = [val for val in _series_to_floats(series) if not math.isnan(val)]
    n = len(values)
    if n == 0 or n <= lag:
        return math.nan

    mean_val = sum(values) / n
    centered = [v - mean_val for v in values]

    def autocov(k: int) -> float:
        total = 0.0
        count = 0
        for idx in range(n - k):
            total += centered[idx] * centered[idx + k]
            count += 1
        return total / count if count else 0.0

    phi = [0.0] * (lag + 1)
    sigma_v = autocov(0)
    if sigma_v == 0:
        return math.nan

    for k in range(1, lag + 1):
        num = autocov(k)
        for j in range(1, k):
            num -= phi[j] * autocov(k - j)
        denom = sigma_v
        if denom == 0:
            return math.nan
        phi_k = num / denom
        new_phi = phi[:]
        new_phi[k] = phi_k
        for j in range(1, k):
            new_phi[j] = phi[j] - phi_k * phi[k - j]
        phi = new_phi
        sigma_v *= max(1.0 - phi_k ** 2, 0.0)

    return float(phi[lag])


def spectral_sharpness(frequencies: Sequence[float], power: Sequence[float], target_freq: float) -> float:
    """Estimate how sharp the dominant peak is around the target frequency."""

    freqs = list(frequencies)
    powers = list(power)
    if not freqs or not powers:
        return float("nan")
    distances = [abs(freq - target_freq) for freq in freqs]
    idx = distances.index(min(distances))
    if idx == 0 or idx == len(powers) - 1:
        return float("nan")
    peak_power = powers[idx]
    neighborhood = powers[max(0, idx - 2) : idx + 3]
    baseline_vals = [val for i, val in enumerate(neighborhood) if i != (idx - max(0, idx - 2)) and not math.isnan(val)]
    if not baseline_vals:
        return float("nan")
    baseline = sum(baseline_vals) / len(baseline_vals)
    if baseline == 0:
        return float("nan")
    return float((peak_power - baseline) / baseline)


def robust_zscore(values: Sequence[float]) -> list[float]:
    """Compute robust z-scores using the median and MAD."""

    data = [float(v) for v in values]
    if not data:
        return []
    valid = [v for v in data if not math.isnan(v)]
    if not valid:
        return [math.nan for _ in data]
    med = _median(valid)
    mad_values = [abs(v - med) for v in valid]
    mad = _median(mad_values)
    if mad == 0 or math.isnan(mad):
        return [0.0 if not math.isnan(v) else math.nan for v in data]
    scale = 0.6745 / mad
    return [scale * (v - med) if not math.isnan(v) else math.nan for v in data]


def weighted_average(scores: Mapping[str, float], weights: Mapping[str, float]) -> float:
    total_weight = 0.0
    total_score = 0.0
    for key, weight in weights.items():
        score = scores.get(key)
        if score is None or (isinstance(score, float) and math.isnan(score)):
            continue
        total_weight += weight
        total_score += score * weight
    if total_weight == 0:
        return float("nan")
    return total_score / total_weight


def ensure_directory(path: str | os.PathLike[str]) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def with_progress(iterable: Iterable[Any], description: str) -> Iterable[Any]:
    try:
        from tqdm import tqdm

        return tqdm(iterable, desc=description)
    except ImportError:  # pragma: no cover - tqdm may be absent
        LOGGER.warning("tqdm is not installed; progress bars will be disabled")
        return iterable


def _series_to_floats(series: pd.Series) -> list[float]:
    values = []
    for value in series:
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            values.append(float("nan"))
    return values


def _centered_values(series: pd.Series) -> list[float]:
    values = _series_to_floats(series)
    valid = [v for v in values if not math.isnan(v)]
    if not valid:
        return values
    mean_val = sum(valid) / len(valid)
    return [v - mean_val if not math.isnan(v) else math.nan for v in values]


def _segment_autocorrelation(segment: list[float], lag: int) -> float:
    if len(segment) <= lag:
        return math.nan
    pairs = []
    for idx in range(len(segment) - lag):
        x = segment[idx]
        y = segment[idx + lag]
        if math.isnan(x) or math.isnan(y):
            continue
        pairs.append((x, y))
    if not pairs:
        return math.nan
    xs, ys = zip(*pairs)
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denom_x = sum((x - mean_x) ** 2 for x in xs)
    denom_y = sum((y - mean_y) ** 2 for y in ys)
    denom = math.sqrt(denom_x * denom_y)
    if denom == 0:
        return math.nan
    return numerator / denom


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        return math.nan
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[mid])
    return float((ordered[mid - 1] + ordered[mid]) / 2)
def setup_logging(
    level: str = "INFO",
    filename: str | os.PathLike[str] | None = None,
    *,
    fmt: str | None = None,
    datefmt: str | None = None,
) -> None:
    """Lightweight logging configuration used within the cyclicity module."""

    log_level = getattr(logging, str(level).upper(), logging.INFO)
    formatter = logging.Formatter(fmt or "%(levelname)s:%(name)s:%(message)s", datefmt=datefmt)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Ensure existing handlers are cleared to avoid duplicate logs.
    if not root_logger.handlers:
        console = logging.StreamHandler()
        console.setLevel(log_level)
        console.setFormatter(formatter)
        root_logger.addHandler(console)

    if filename:
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
