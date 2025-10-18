"""Reporting utilities for the mutual fund cyclicality pipeline."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Mapping

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from .backtest import BacktestConfig, backtest_bottom_signals
from .bottom_signal import BottomSignalConfig, vote_bottom_signal
from .detrend import DetrendConfig, detrend_series
from .hilbert_cycle import HilbertConfig, hilbert_cycle
from .io import load_nav_history
from .scoring import GuardrailConfig, ScoringConfig, combine_scores
from .spectrum import LombScargleConfig, SpectrumBand, SpectrumConfig, WelchConfig, compute_spectrum
from .state_space import StateSpaceConfig, estimate_cycle
from .turning_points import TurningPointConfig, detect_turning_points
from .harmonic import HarmonicConfig, harmonic_regression
from .utils import CacheConfig, CacheManager, ensure_directory, setup_logging, with_progress

LOGGER = logging.getLogger(__name__)


def _load_yaml(path: str | Path) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _build_configs(raw: Mapping[str, object]) -> Dict[str, object]:
    return {
        "logging": raw.get("logging", {}),
        "io": raw.get("io", {}),
        "detrend": DetrendConfig(**raw.get("detrend", {})),
        "spectrum": SpectrumConfig(
            method=raw.get("spectrum", {}).get("method", "welch"),
            welch=WelchConfig(**raw.get("spectrum", {}).get("welch", {})),
            lomb_scargle=LombScargleConfig(**raw.get("spectrum", {}).get("lomb_scargle", {})),
            band=SpectrumBand(**raw.get("spectrum", {}).get("band", {})),
        ),
        "harmonic": HarmonicConfig(**raw.get("harmonic", {})),
        "hilbert": HilbertConfig(**raw.get("hilbert", {})),
        "state_space": StateSpaceConfig(**raw.get("state_space", {})),
        "scoring": ScoringConfig(
            weights=raw.get("scoring", {}).get("weights", {}),
            guardrails=GuardrailConfig(**raw.get("scoring", {}).get("guardrails", {})),
        ),
        "turning_points": TurningPointConfig(**raw.get("turning_points", {})),
        "bottom_signal": BottomSignalConfig(**raw.get("bottom_signal", {})),
        "backtest": BacktestConfig(**raw.get("backtest", {})),
        "report": raw.get("report", {}),
        "cache": CacheConfig(**raw.get("cache", {})),
    }


def generate_reports(config_path: str = "configs/default.yml") -> Dict[str, pd.DataFrame]:
    """Run the entire cyclicality pipeline and persist outputs."""

    raw_config = _load_yaml(config_path)
    cfg = _build_configs(raw_config)

    log_cfg = cfg["logging"]
    setup_logging(level=log_cfg.get("level", "INFO"), filename=log_cfg.get("file"))

    report_cfg = cfg["report"]
    ensure_directory(report_cfg.get("plots_dir", "outputs/plots"))
    ensure_directory(Path(report_cfg.get("summary_csv", "outputs/csv/cyclicity_summary.csv")).parent)

    cache_manager = CacheManager(cfg["cache"])

    nav_history = load_nav_history(cfg["io"], cache=cfg["cache"])

    summary_records: List[Dict[str, object]] = []
    turning_records: List[pd.DataFrame] = []
    backtest_records: List[pd.DataFrame] = []
    bottom_records: List[Dict[str, object]] = []

    schemes = nav_history.index.get_level_values(0).unique()
    LOGGER.info("Starting per-scheme analysis for %d schemes", len(schemes))

    for scheme_code in with_progress(schemes, "Schemes"):
        try:
            scheme_df = nav_history.xs(scheme_code)
            log_nav = scheme_df["log_nav"].copy()
            nav_values = scheme_df["nav"].copy()

            residuals, trend = detrend_series(log_nav, cfg["detrend"])
            detrended = residuals.dropna()

            spectrum_res = compute_spectrum(detrended, cfg["spectrum"])
            harmonic_metrics = harmonic_regression(detrended, spectrum_res.dominant_period, cfg["harmonic"])

            hilbert_input = detrended.fillna(method="ffill").fillna(method="bfill")
            hilbert_res = hilbert_cycle(hilbert_input, cfg["hilbert"])

            state_res = estimate_cycle(detrended.fillna(method="ffill").fillna(method="bfill"), cfg["state_space"])

            turning_df = detect_turning_points(hilbert_res["cycle"], cfg["turning_points"])
            if not turning_df.empty:
                turning_df.insert(0, "scheme_code", scheme_code)
                turning_records.append(turning_df)
            num_cycles = max(1, int((turning_df["type"] == "trough").sum())) if not turning_df.empty else 0

            bottom_res = vote_bottom_signal(
                scheme_code,
                nav_values,
                turning_df,
                hilbert_res,
                state_res,
                cfg["bottom_signal"],
            )
            bottom_records.append(bottom_res)

            trough_dates = turning_df[turning_df["type"] == "trough"]["date"] if not turning_df.empty else []
            signal_series = pd.Series(False, index=nav_values.index)
            signal_series.loc[signal_series.index.isin(list(trough_dates))] = True
            backtest_df = backtest_bottom_signals(scheme_code, nav_values, signal_series, cfg["backtest"])
            if not backtest_df.empty:
                backtest_records.append(backtest_df)

            summary_records.append(
                {
                    "scheme_code": scheme_code,
                    "spectrum": spectrum_res.sharpness,
                    "harmonic": harmonic_metrics.get("r2", np.nan),
                    "hilbert": hilbert_res.get("phase_coherence", np.nan),
                    "state_space": state_res.get("persistence", np.nan),
                    "turning_points": float(num_cycles),
                    "num_cycles": float(num_cycles),
                    "dominant_period": spectrum_res.dominant_period,
                    "vote_count": bottom_res["vote_count"],
                    "bottom_signal": bottom_res["signal"],
                    "median_period_hilbert": hilbert_res.get("median_period", np.nan),
                }
            )

            _plot_scheme(
                scheme_code,
                nav_values,
                trend,
                hilbert_res["cycle"],
                turning_df,
                Path(report_cfg.get("plots_dir", "outputs/plots")) / f"{scheme_code}_cycle.png",
            )

            if cfg["cache"].enabled:
                cache_manager.dump_json(
                    f"metrics_{scheme_code}",
                    {
                        "spectrum": spectrum_res.dominant_frequency,
                        "harmonic": harmonic_metrics,
                        "bottom": {k: (v if not isinstance(v, dict) else json.dumps(v)) for k, v in bottom_res.items()},
                    },
                )
        except Exception as err:  # pragma: no cover - defensive guard
            LOGGER.exception("Failed to process scheme %s: %s", scheme_code, err)
            continue

    summary_df = combine_scores(summary_records, cfg["scoring"])

    summary_path = Path(report_cfg.get("summary_csv", "outputs/csv/cyclicity_summary.csv"))
    turning_path = Path(report_cfg.get("turning_points_csv", "outputs/csv/turning_points.csv"))
    backtest_path = Path(report_cfg.get("backtest_csv", "outputs/csv/backtest_results.csv"))

    summary_df.to_csv(summary_path)
    if turning_records:
        pd.concat(turning_records, ignore_index=True).to_csv(turning_path, index=False)
    else:
        Path(turning_path).touch()
    if backtest_records:
        pd.concat(backtest_records, ignore_index=True).to_csv(backtest_path, index=False)
    else:
        Path(backtest_path).touch()

    LOGGER.info("Reports written to %s", summary_path.parent)

    return {
        "summary": summary_df,
        "turning_points": pd.concat(turning_records, ignore_index=True) if turning_records else pd.DataFrame(),
        "backtest": pd.concat(backtest_records, ignore_index=True) if backtest_records else pd.DataFrame(),
        "bottom_signals": pd.DataFrame(bottom_records),
    }


def _plot_scheme(
    scheme_code: str,
    nav_series: pd.Series,
    trend_log: pd.Series,
    cycle_series: pd.Series,
    turning_points: pd.DataFrame,
    output_path: Path,
) -> None:
    ensure_directory(output_path.parent)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    axes[0].plot(nav_series.index, nav_series.values, label="NAV")
    if not trend_log.isna().all():
        nav_trend = np.exp(trend_log)
        axes[0].plot(trend_log.index, nav_trend, label="Trend", linestyle="--")
    axes[0].set_title(f"{scheme_code} NAV vs Trend")
    axes[0].legend()

    axes[1].plot(trend_log.index, trend_log.values, label="Log Trend")
    axes[1].set_title("Log Trend")

    axes[2].plot(cycle_series.index, cycle_series.values, label="Cycle Estimate")
    if turning_points is not None and not turning_points.empty:
        troughs = turning_points[turning_points["type"] == "trough"]
        axes[2].scatter(troughs["date"], troughs["value"], color="green", label="Troughs")
        peaks = turning_points[turning_points["type"] == "peak"]
        axes[2].scatter(peaks["date"], peaks["value"], color="red", label="Peaks")
    axes[2].set_title("Hilbert Cycle")
    axes[2].legend()

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


__all__ = ["generate_reports"]
