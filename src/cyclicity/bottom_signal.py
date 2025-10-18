"""Bottom signal voting utilities."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Mapping

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)


@dataclass
class BottomSignalConfig:
    min_votes: int = 2
    lookback_months: int = 6


def vote_bottom_signal(
    scheme_code: str,
    price_series: pd.Series,
    turning_points: pd.DataFrame,
    hilbert_result: Mapping[str, pd.Series | float] | None,
    state_result: Mapping[str, pd.Series | float] | None,
    config: BottomSignalConfig,
) -> Dict[str, object]:
    """Aggregate several indicators to flag potential bottoms."""

    votes: Dict[str, bool] = {}
    latest_date = price_series.index.max()

    if turning_points is not None and not turning_points.empty:
        troughs = turning_points[turning_points["type"] == "trough"]
        if not troughs.empty:
            last_trough = troughs.iloc[-1]
            months_since = (latest_date.to_period("M") - last_trough["date"].to_period("M")).n
            votes["recent_trough"] = months_since <= config.lookback_months
        else:
            votes["recent_trough"] = False
    else:
        votes["recent_trough"] = False

    if hilbert_result:
        phase = hilbert_result.get("phase")
        if isinstance(phase, pd.Series) and not phase.empty:
            last_phase = float(np.mod(phase.iloc[-1], 2 * np.pi))
            votes["hilbert_phase"] = last_phase > np.pi * 1.5 or last_phase < np.pi / 2
        else:
            votes["hilbert_phase"] = False
        coherence = hilbert_result.get("phase_coherence")
    else:
        votes["hilbert_phase"] = False
        coherence = np.nan

    if state_result:
        cycle = state_result.get("cycle")
        if isinstance(cycle, pd.Series) and len(cycle) > 1:
            votes["state_cycle"] = cycle.iloc[-1] < 0 and cycle.diff().iloc[-1] > 0
        else:
            votes["state_cycle"] = False
        persistence = state_result.get("persistence")
    else:
        votes["state_cycle"] = False
        persistence = np.nan

    affirmative_votes = sum(votes.values())
    signal = affirmative_votes >= config.min_votes

    return {
        "scheme_code": scheme_code,
        "signal": bool(signal),
        "votes": votes,
        "vote_count": affirmative_votes,
        "phase_coherence": coherence,
        "state_persistence": persistence,
    }


__all__ = ["BottomSignalConfig", "vote_bottom_signal"]
