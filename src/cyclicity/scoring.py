"""Score aggregation utilities."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping

import numpy as np
import pandas as pd

from .utils import robust_zscore, weighted_average

LOGGER = logging.getLogger(__name__)


@dataclass
class GuardrailConfig:
    min_cycles: int = 3
    min_score: float = 0.0


@dataclass
class ScoringConfig:
    weights: Mapping[str, float] = field(default_factory=dict)
    guardrails: GuardrailConfig = field(default_factory=GuardrailConfig)


def combine_scores(records: Iterable[Mapping[str, float]], config: ScoringConfig) -> pd.DataFrame:
    """Combine per-scheme metrics into a summary score."""

    frame = pd.DataFrame(records)
    if frame.empty:
        return frame

    if "scheme_code" not in frame.columns:
        raise ValueError("Records must include scheme_code column")

    frame = frame.set_index("scheme_code")

    scaled_scores: Dict[str, np.ndarray] = {}
    for metric in config.weights:
        if metric not in frame.columns:
            LOGGER.warning("Missing metric %s for scoring", metric)
            continue
        scaled_scores[metric] = robust_zscore(frame[metric].to_numpy())
        frame[f"{metric}_scaled"] = scaled_scores[metric]

    aggregated: List[Dict[str, float]] = []
    for scheme, row in frame.iterrows():
        scaled = {metric: row.get(f"{metric}_scaled", np.nan) for metric in config.weights}
        raw_score = weighted_average(scaled, config.weights)
        num_cycles = row.get("num_cycles", np.nan)
        if not np.isnan(num_cycles) and num_cycles < config.guardrails.min_cycles:
            LOGGER.debug("Scheme %s failed guardrail: insufficient cycles", scheme)
            final_score = np.nan
        else:
            final_score = max(config.guardrails.min_score, raw_score)
        aggregated.append(
            {
                "scheme_code": scheme,
                "score": final_score,
                **{k: row.get(k) for k in frame.columns if not k.endswith("_scaled")},
            }
        )

    summary = pd.DataFrame(aggregated).set_index("scheme_code")
    summary.sort_values("score", ascending=False, inplace=True)
    return summary


__all__ = ["ScoringConfig", "GuardrailConfig", "combine_scores"]
