from __future__ import annotations

from datetime import date
import math
import random

import pytest

from simple_cyclicity import CyclicalityAnalyzer, NavSeries


@pytest.fixture
def monthly_dates() -> list[date]:
    dates = []
    year = 2000
    month = 1
    for _ in range(120):
        if month > 12:
            month = 1
            year += 1
        if month == 2:
            day = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
        elif month in {1, 3, 5, 7, 8, 10, 12}:
            day = 31
        else:
            day = 30
        dates.append(date(year, month, day))
        month += 1
    return dates


@pytest.fixture
def drifting_sine_nav(monthly_dates: list[date]) -> NavSeries:
    rng = random.Random(0)
    values = []
    for i in range(len(monthly_dates)):
        drift = 0.12 * i
        seasonal = 12.0 * math.sin(2 * math.pi * i / 12.0)
        noise = rng.gauss(0.0, 0.6)
        values.append(100.0 + drift + seasonal + noise)
    return NavSeries(monthly_dates, values)


@pytest.fixture
def white_noise_nav(monthly_dates: list[date]) -> NavSeries:
    rng = random.Random(1)
    level = 100.0
    values = []
    for _ in monthly_dates:
        level += rng.gauss(0.0, 0.8)
        values.append(level)
    return NavSeries(monthly_dates, values)


@pytest.fixture
def step_regime_nav(monthly_dates: list[date]) -> NavSeries:
    rng = random.Random(2)
    values = []
    for i, _ in enumerate(monthly_dates):
        base = 100.0 if i < len(monthly_dates) // 2 else 112.0
        values.append(base + 0.05 * i + rng.gauss(0.0, 0.5))
    return NavSeries(monthly_dates, values)


def test_drifting_sine_has_high_cyclicality(drifting_sine_nav: NavSeries) -> None:
    analyzer = CyclicalityAnalyzer(min_cycle=6, max_cycle=24)
    result = analyzer.analyze(drifting_sine_nav)

    assert 10 <= result.cycle_length <= 14
    assert result.score > 4.0
    assert 8 <= len(result.troughs) <= 12


def test_white_noise_has_low_cyclicality(white_noise_nav: NavSeries) -> None:
    analyzer = CyclicalityAnalyzer(min_cycle=6, max_cycle=24)
    result = analyzer.analyze(white_noise_nav)

    assert result.score < 4.0
    assert len(result.troughs) > 10


def test_step_regime_degrades_cyclicality_metrics(
    drifting_sine_nav: NavSeries, step_regime_nav: NavSeries
) -> None:
    analyzer = CyclicalityAnalyzer(min_cycle=6, max_cycle=24)
    sine_result = analyzer.analyze(drifting_sine_nav)
    step_result = analyzer.analyze(step_regime_nav)

    assert step_result.score < sine_result.score
    assert step_result.cycle_length > 20 or math.isinf(step_result.cycle_length)
