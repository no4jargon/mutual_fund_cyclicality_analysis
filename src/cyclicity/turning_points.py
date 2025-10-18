"""Turning point detection utilities."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import signal

LOGGER = logging.getLogger(__name__)


@dataclass
class TurningPointConfig:
    prominence: float = 0.5
    distance: int = 3


def detect_turning_points(series: pd.Series, config: TurningPointConfig) -> pd.DataFrame:
    values = series.to_numpy(dtype=float)
    peaks, peak_props = signal.find_peaks(values, prominence=config.prominence, distance=config.distance)
    troughs, trough_props = signal.find_peaks(-values, prominence=config.prominence, distance=config.distance)

    records = []
    for idx, prominence in zip(peaks, peak_props.get("prominences", np.repeat(np.nan, len(peaks)))):
        records.append(
            {
                "date": series.index[idx],
                "value": values[idx],
                "type": "peak",
                "prominence": float(prominence),
            }
        )
    for idx, prominence in zip(troughs, trough_props.get("prominences", np.repeat(np.nan, len(troughs)))):
        records.append(
            {
                "date": series.index[idx],
                "value": values[idx],
                "type": "trough",
                "prominence": float(prominence),
            }
        )

    if records:
        turning_points = pd.DataFrame(records).sort_values("date")
        turning_points.reset_index(drop=True, inplace=True)
    else:
        turning_points = pd.DataFrame(columns=["date", "value", "type", "prominence"])
    return turning_points


__all__ = ["TurningPointConfig", "detect_turning_points"]
