from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from cyclicity.report import generate_reports
from mf_analysis.backtest import run_backtest
from mf_analysis.pipeline import run_analysis_pipeline


@pytest.fixture(scope="module")
def sample_scheme_codes() -> list[str]:
    metadata = pd.read_csv(Path("mutual_fund_data.csv"))
    codes = metadata["Scheme_Code"].astype(str).dropna().unique()
    if len(codes) < 3:
        raise RuntimeError("Expected bundled metadata to contain at least three schemes")
    return list(codes[:3])


def _write_metadata(tmp_path: Path, scheme_codes: list[str]) -> Path:
    metadata = pd.read_csv(Path("mutual_fund_data.csv"))
    subset = metadata[metadata["Scheme_Code"].astype(str).isin(scheme_codes)]
    metadata_path = tmp_path / "metadata.csv"
    subset.to_csv(metadata_path, index=False)
    return metadata_path


def _write_nav_history(
    tmp_path: Path,
    scheme_codes: list[str],
    *,
    periods: int,
    freq: str,
    start: str,
) -> tuple[Path, int]:
    nav_dates = pd.date_range(start=start, periods=periods, freq=freq)
    frames: list[pd.DataFrame] = []
    for idx, scheme in enumerate(scheme_codes):
        baseline = 100.0 + idx * 5.0
        trend = np.linspace(0.0, 5.0, len(nav_dates))
        seasonal = 2.0 * np.sin(np.linspace(0.0, 8.0, len(nav_dates)))
        nav_values = baseline + trend + seasonal
        frames.append(
            pd.DataFrame(
                {
                    "scheme_code": scheme,
                    "date": nav_dates,
                    "nav": nav_values,
                }
            )
        )
    nav_history = pd.concat(frames, ignore_index=True).sort_values(["scheme_code", "date"])
    nav_path = tmp_path / "nav_history.parquet"
    nav_history.to_parquet(nav_path, index=False)
    return nav_path, len(nav_dates)


def test_analysis_pipeline_and_backtest_end_to_end(tmp_path: Path, sample_scheme_codes: list[str]) -> None:
    metadata_path = _write_metadata(tmp_path, sample_scheme_codes)
    nav_path, periods = _write_nav_history(
        tmp_path,
        sample_scheme_codes,
        periods=120,
        freq="D",
        start="2020-01-01",
    )

    base_dir = tmp_path / "outputs"
    config = {
        "data": {
            "metadata": str(metadata_path),
            "nav_history": str(nav_path),
        },
        "processing": {
            "detrend": {"window": 5},
            "scoring": {"lookback": 10, "zscore_min_std": 1e-6},
        },
        "output": {
            "base_dir": str(base_dir),
            "analysis_dir": "analysis",
            "tables_subdir": "tables",
            "plots_subdir": "plots",
            "backtest_dir": "backtests",
        },
        "backtest": {
            "transaction_cost": 0.001,
            "entry_threshold": 0.5,
            "exit_threshold": 0.25,
        },
    }

    artifacts = run_analysis_pipeline(config)
    expected_rows = len(sample_scheme_codes) * periods

    assert artifacts.scores.shape[0] == expected_rows
    assert set(["scheme_code", "date", "score"]).issubset(artifacts.scores.columns)
    assert artifacts.summary.shape[0] == len(sample_scheme_codes)
    assert set(["scheme_code", "latest_score", "mean_score", "volatility"]).issubset(
        artifacts.summary.columns
    )
    assert artifacts.signals_path.exists()

    signals_df = pd.read_csv(artifacts.signals_path)
    assert len(signals_df) == expected_rows

    summary_csv = artifacts.signals_path.parent / "fund_summary.csv"
    assert summary_csv.exists()
    summary_df = pd.read_csv(summary_csv)
    assert len(summary_df) == len(sample_scheme_codes)

    backtest_df = run_backtest(config, artifacts.signals_path)
    assert len(backtest_df) == expected_rows

    backtest_dir = base_dir / "backtests"
    timeseries_path = backtest_dir / "backtest_timeseries.csv"
    summary_path = backtest_dir / "backtest_summary.csv"
    assert timeseries_path.exists()
    assert summary_path.exists()

    backtest_summary = pd.read_csv(summary_path)
    assert len(backtest_summary) == len(sample_scheme_codes)


def test_cyclicity_generate_reports_smoke(tmp_path: Path, sample_scheme_codes: list[str]) -> None:
    # Use a single scheme for a lightweight smoke test.
    scheme_code = sample_scheme_codes[0]
    nav_path, periods = _write_nav_history(
        tmp_path,
        [scheme_code],
        periods=72,
        freq="ME",
        start="2015-01-31",
    )

    config_path = tmp_path / "cyclicity_config.yml"
    report_dir = tmp_path / "cyclicity"
    plots_dir = report_dir / "plots"
    summary_csv = report_dir / "summary.csv"
    turning_csv = report_dir / "turning_points.csv"
    backtest_csv = report_dir / "backtest.csv"

    config_payload = {
        "logging": {"level": "WARNING"},
        "io": {"parquet_path": str(nav_path), "min_points": 24},
        "detrend": {"method": "returns", "returns_window": 3},
        "spectrum": {
            "method": "welch",
            "welch": {"nperseg": 24, "noverlap": 12},
            "band": {"low": 0.05, "high": 0.5},
        },
        "harmonic": {},
        "hilbert": {},
        "state_space": {},
        "scoring": {
            "weights": {
                "spectrum": 1.0,
                "harmonic": 1.0,
                "hilbert": 1.0,
                "state_space": 1.0,
                "turning_points": 1.0,
            },
            "guardrails": {"min_cycles": 0, "min_score": -1.0},
        },
        "turning_points": {},
        "bottom_signal": {},
        "backtest": {},
        "report": {
            "plots_dir": str(plots_dir),
            "summary_csv": str(summary_csv),
            "turning_points_csv": str(turning_csv),
            "backtest_csv": str(backtest_csv),
        },
        "cache": {"enabled": False, "directory": str(tmp_path / "cache")},
    }

    with config_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config_payload, handle)

    results = generate_reports(str(config_path))

    assert set(results) == {"summary", "turning_points", "backtest", "bottom_signals"}
    assert scheme_code in results["summary"].index
    assert "score" in results["summary"].columns

    for output_path in (summary_csv, turning_csv, backtest_csv):
        assert output_path.exists()

    assert plots_dir.exists()
