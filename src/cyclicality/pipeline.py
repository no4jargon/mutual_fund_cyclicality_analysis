"""Core utilities for detecting cyclicality in NAV time series."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Sequence


@dataclass
class NavSeries:
    """Minimal representation of a monthly NAV time series."""

    dates: Sequence[date]
    values: Sequence[float]

    def __post_init__(self) -> None:
        if len(self.dates) != len(self.values):
            raise ValueError("dates and values must have the same length")
        if len(self.dates) == 0:
            raise ValueError("NavSeries requires at least one observation")

    def __len__(self) -> int:
        return len(self.values)

    def iter_values(self) -> Iterable[float]:
        return iter(self.values)

    def iter_dates(self) -> Iterable[date]:
        return iter(self.dates)


@dataclass
class CycleAnalysisResult:
    """Holds the outputs of a cyclicality analysis run."""

    cycle_length: float
    score: float
    troughs: List[date]


class CyclicalityAnalyzer:
    """Compute simple cyclicality diagnostics for NAV series."""

    def __init__(self, min_cycle: int = 6, max_cycle: int = 36) -> None:
        if min_cycle < 2:
            raise ValueError("min_cycle must be at least 2 months")
        if max_cycle <= min_cycle:
            raise ValueError("max_cycle must be greater than min_cycle")
        self.min_cycle = float(min_cycle)
        self.max_cycle = float(max_cycle)

    def analyze(self, nav_series: NavSeries) -> CycleAnalysisResult:
        """Run the cyclicality analysis on a monthly NAV series."""

        values = list(float(v) for v in nav_series.iter_values())
        detrended = self._remove_trend(values)
        windowed = self._apply_window(detrended)
        freqs, amplitudes = self._periodogram(windowed)
        cycle_length, score = self._derive_cycle_metrics(freqs, amplitudes)
        troughs = self._detect_troughs(detrended, nav_series.dates)
        return CycleAnalysisResult(cycle_length=cycle_length, score=score, troughs=troughs)

    def _remove_trend(self, values: Sequence[float]) -> List[float]:
        n = len(values)
        if n == 1:
            return [values[0] - values[0]]
        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n)) or 1.0
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        return [v - (slope * i + intercept) for i, v in enumerate(values)]

    def _apply_window(self, detrended: Sequence[float]) -> List[float]:
        n = len(detrended)
        if n <= 1:
            return list(detrended)
        windowed = []
        for i, value in enumerate(detrended):
            weight = 0.5 - 0.5 * math.cos(2.0 * math.pi * i / (n - 1))
            windowed.append(value * weight)
        return windowed

    def _periodogram(self, values: Sequence[float]) -> tuple[List[float], List[float]]:
        n = len(values)
        if n == 0:
            return [], []
        freqs: List[float] = []
        amplitudes: List[float] = []
        for k in range(n // 2 + 1):
            real = 0.0
            imag = 0.0
            for t, sample in enumerate(values):
                angle = 2.0 * math.pi * k * t / n
                real += sample * math.cos(angle)
                imag -= sample * math.sin(angle)
            amplitude = math.sqrt(real * real + imag * imag)
            freqs.append(k / n)
            amplitudes.append(amplitude)
        if amplitudes:
            amplitudes[0] = 0.0
        return freqs, amplitudes

    def _derive_cycle_metrics(self, freqs: Sequence[float], amplitudes: Sequence[float]) -> tuple[float, float]:
        if not freqs or not amplitudes:
            return float("nan"), 0.0

        min_freq = 1.0 / self.max_cycle
        max_freq = 1.0 / self.min_cycle
        usable: List[tuple[float, float]] = [
            (f, a)
            for f, a in zip(freqs, amplitudes)
            if min_freq <= f <= max_freq
        ]

        if not usable:
            peak_index = max(range(len(amplitudes)), key=lambda i: amplitudes[i])
            peak_freq = freqs[peak_index]
            cycle_length = float("inf") if peak_freq == 0 else 1.0 / peak_freq
            return cycle_length, 0.0

        peak_freq, peak_amplitude = max(usable, key=lambda fa: fa[1])
        background_values = [a for _, a in usable if a > 0]
        if not background_values:
            score = 0.0
        else:
            sorted_bg = sorted(background_values)
            mid = len(sorted_bg) // 2
            if len(sorted_bg) % 2 == 0:
                background = 0.5 * (sorted_bg[mid - 1] + sorted_bg[mid])
            else:
                background = sorted_bg[mid]
            background = background if background != 0 else 1e-12
            score = float(peak_amplitude / background)
        cycle_length = float("inf") if peak_freq == 0 else float(1.0 / peak_freq)
        return cycle_length, score

    def _detect_troughs(self, detrended: Sequence[float], dates: Sequence[date]) -> List[date]:
        troughs: List[date] = []
        for i in range(1, len(detrended) - 1):
            if detrended[i] <= detrended[i - 1] and detrended[i] < detrended[i + 1]:
                troughs.append(dates[i])
        return troughs
