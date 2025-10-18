from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from tqdm import tqdm

from common.data_ingestion import normalise_columns, prepare_nav_history

logger = logging.getLogger(__name__)


@dataclass
class PipelineArtifacts:
    scores: pd.DataFrame
    summary: pd.DataFrame
    signals_path: Path
def _ensure_column(frame: pd.DataFrame, candidates: list[str], target: str) -> None:
    for candidate in candidates:
        if candidate in frame.columns:
            if candidate != target:
                frame.rename(columns={candidate: target}, inplace=True)
            return
    raise KeyError(f"Expected column not found. Tried {candidates} in {frame.columns.tolist()}")


def ingest_data(
    metadata_path: Path,
    nav_history_path: Path,
    schemes: Iterable[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("Loading metadata from %s", metadata_path)
    metadata = normalise_columns(pd.read_csv(metadata_path))
    _ensure_column(metadata, ["scheme_code"], "scheme_code")
    metadata["scheme_code"] = metadata["scheme_code"].astype(str)
    logger.info("Loading NAV history from %s", nav_history_path)
    try:
        nav_history = prepare_nav_history(pd.read_parquet(nav_history_path))
        logger.info(f"Normalized NAV history columns: {nav_history.columns.tolist()}")
    except ImportError as exc:
        raise RuntimeError(
            "Reading parquet files requires the `pyarrow` or `fastparquet` packages."
        ) from exc
    
    schemes_set = set(schemes or [])
    if schemes_set:
        metadata = metadata[metadata["scheme_code"].isin(schemes_set)]
        nav_history = nav_history[nav_history["scheme_code"].isin(schemes_set)]
        logger.info("Filtered datasets down to %d schemes", len(schemes_set))

    if metadata.empty or nav_history.empty:
        raise ValueError("No data available after applying scheme filters.")

    nav_history["date"] = pd.to_datetime(nav_history["date"])
    nav_history = nav_history.sort_values(["scheme_code", "date"]).reset_index(drop=True)

    return metadata, nav_history


def detrend_nav_history(
    nav_history: pd.DataFrame,
    window: int,
) -> pd.DataFrame:
    logger.info("Applying detrending window of %s days", window)
    processed_frames: list[pd.DataFrame] = []
    for scheme_code, group in tqdm(
        nav_history.groupby("scheme_code"),
        desc="Detrending NAV series",
        unit="fund",
    ):
        group = group.sort_values("date").copy()
        group["return"] = group["nav"].pct_change().fillna(0.0)
        group["trend"] = group["return"].rolling(window, min_periods=1).mean()
        group["detrended_return"] = group["return"] - group["trend"]
        processed_frames.append(group)
    detrended = pd.concat(processed_frames, ignore_index=True)
    return detrended


def score_signals(
    detrended: pd.DataFrame,
    lookback: int,
    min_std: float,
) -> pd.DataFrame:
    logger.info("Scoring funds using lookback of %s days", lookback)
    scored_frames: list[pd.DataFrame] = []
    for scheme_code, group in tqdm(
        detrended.groupby("scheme_code"),
        desc="Scoring signals",
        unit="fund",
    ):
        group = group.sort_values("date").copy()
        rolling_mean = group["detrended_return"].rolling(lookback, min_periods=1).mean()
        rolling_std = group["detrended_return"].rolling(lookback, min_periods=1).std()
        rolling_std = rolling_std.clip(lower=min_std)
        group["score"] = (group["detrended_return"] - rolling_mean) / rolling_std
        group["score"] = group["score"].replace([np.inf, -np.inf], 0.0).fillna(0.0)
        scored_frames.append(group)
    scored = pd.concat(scored_frames, ignore_index=True)
    return scored


def summarise_scores(scored: pd.DataFrame) -> pd.DataFrame:
    summary = (
        scored.groupby("scheme_code")
        .agg(
            latest_score=("score", "last"),
            mean_score=("score", "mean"),
            volatility=("detrended_return", "std"),
        )
        .sort_values("latest_score", ascending=False)
    )
    summary.reset_index(inplace=True)
    return summary


def _analysis_directories(output_config: dict) -> tuple[Path, Path, Path]:
    base_dir = Path(output_config.get("base_dir", "outputs"))
    analysis_dir = base_dir / output_config.get("analysis_dir", "analysis")
    tables_dir = analysis_dir / output_config.get("tables_subdir", "tables")
    plots_dir = analysis_dir / output_config.get("plots_subdir", "plots")
    return analysis_dir, tables_dir, plots_dir


def _plot_datapoint_histogram(nav_history: pd.DataFrame, output_config: dict) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib is not installed; skipping datapoint histogram plot.")
        return

    _, _, plots_dir = _analysis_directories(output_config)
    plots_dir.mkdir(parents=True, exist_ok=True)

    counts = nav_history.groupby("scheme_code").size()
    if counts.empty:
        logger.warning("No NAV history data available for histogram plot.")
        return

    figure, axis = plt.subplots(figsize=(10, 6))
    axis.hist(counts.values, bins=min(50, len(counts)), edgecolor="black")
    axis.set_title("NAV observations per scheme")
    axis.set_xlabel("Number of data points")
    axis.set_ylabel("Number of schemes")
    plot_path = plots_dir / "scheme_datapoints_histogram.png"
    figure.savefig(plot_path, bbox_inches="tight")
    plt.close(figure)
    logger.info("Wrote datapoint histogram to %s", plot_path)


def generate_outputs(
    scored: pd.DataFrame,
    summary: pd.DataFrame,
    output_config: dict,
) -> Path:
    analysis_dir, tables_dir, plots_dir = _analysis_directories(output_config)

    for directory in (analysis_dir, tables_dir, plots_dir):
        directory.mkdir(parents=True, exist_ok=True)

    scores_path = tables_dir / "fund_signals.csv"
    summary_path = tables_dir / "fund_summary.csv"
    scored.to_csv(scores_path, index=False)
    summary.to_csv(summary_path, index=False)
    logger.info("Wrote score details to %s", scores_path)
    logger.info("Wrote summary table to %s", summary_path)

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning(
            "matplotlib is not installed; skipping plot generation."
        )
    else:
        top_funds = summary.head(5)["scheme_code"].tolist()
        figure, axis = plt.subplots(figsize=(10, 6))
        for scheme_code in top_funds:
            subset = scored[scored["scheme_code"] == scheme_code]
            axis.plot(subset["date"], subset["score"], label=str(scheme_code))
        axis.set_title("Signal scores for top funds")
        axis.set_xlabel("Date")
        axis.set_ylabel("Score")
        axis.legend()
        figure.autofmt_xdate()
        plot_path = plots_dir / "top_fund_scores.png"
        figure.savefig(plot_path, bbox_inches="tight")
        plt.close(figure)
        logger.info("Wrote score plot to %s", plot_path)

    return analysis_dir


def get_signals_path(config: dict) -> Path:
    _, tables_dir, _ = _analysis_directories(config["output"])
    return tables_dir / "fund_signals.csv"


def run_analysis_pipeline(config: dict, schemes: Iterable[str] | None = None) -> PipelineArtifacts:
    metadata_path = Path(config["data"]["metadata"])
    nav_history_path = Path(config["data"]["nav_history"])
    metadata, nav_history = ingest_data(metadata_path, nav_history_path, schemes)
    _plot_datapoint_histogram(nav_history, config["output"])
    logger.info(
        "Processing %d schemes across %d NAV observations",
        metadata["scheme_code"].nunique(),
        len(nav_history),
    )

    detrended = detrend_nav_history(nav_history, window=int(config["processing"]["detrend"]["window"]))
    scored = score_signals(
        detrended,
        lookback=int(config["processing"]["scoring"]["lookback"]),
        min_std=float(config["processing"]["scoring"].get("zscore_min_std", 1e-6)),
    )
    summary = summarise_scores(scored)
    analysis_dir = generate_outputs(scored, summary, config["output"])

    signals_path = get_signals_path(config)
    return PipelineArtifacts(scores=scored, summary=summary, signals_path=signals_path)
