from __future__ import annotations

import importlib.util
import sys
from types import ModuleType
from pathlib import Path

import pandas as pd
import pytest

BACKTEST_MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "cyclicity" / "backtest.py"
spec = importlib.util.spec_from_file_location("cyclicity.backtest", BACKTEST_MODULE_PATH)
assert spec is not None and spec.loader is not None
backtest_module = importlib.util.module_from_spec(spec)
if "cyclicity" not in sys.modules:
    package = ModuleType("cyclicity")
    package.__path__ = [str(BACKTEST_MODULE_PATH.parent)]
    sys.modules["cyclicity"] = package
sys.modules["cyclicity.backtest"] = backtest_module
spec.loader.exec_module(backtest_module)
BacktestConfig = backtest_module.BacktestConfig
backtest_bottom_signals = backtest_module.backtest_bottom_signals


def test_backtest_bottom_signals_with_minimal_series() -> None:
    dates = pd.date_range("2020-01-31", periods=5, freq="ME")
    nav_series = pd.Series([100.0, 110.0, 121.0, 133.1, 146.41], index=dates)
    signal_series = pd.Series([False, True, False, True, False], index=dates)

    result = backtest_bottom_signals(
        scheme_code="TEST",
        nav_series=nav_series,
        signal_series=signal_series,
        config=BacktestConfig(holding_period_months=1),
    )

    assert len(result) == 2
    assert list(result["signal_date"]) == [dates[1], dates[3]]
    assert list(result["exit_date"]) == [dates[2], dates[4]]
    assert result["forward_return"].tolist() == pytest.approx([0.1, 0.1])
