"""Shared data ingestion utilities."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

__all__ = ["normalise_columns", "prepare_nav_history"]


def normalise_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``frame`` with normalised column names."""
    renamed = frame.copy()
    renamed.columns = [col.strip().lower().replace(" ", "_") for col in renamed.columns]
    return renamed


def _normalise_label(label: str | None) -> str | None:
    if label is None:
        return None
    return label.strip().lower().replace(" ", "_")


def prepare_nav_history(frame: pd.DataFrame, *, required_columns: Iterable[str] | None = None) -> pd.DataFrame:
    """Normalise and clean a NAV history dataframe.

    Parameters
    ----------
    frame:
        Raw NAV history dataframe containing scheme identifier, date and NAV values.
    required_columns:
        Optional collection of column names that must be present after normalisation.

    Returns
    -------
    pandas.DataFrame
        Cleaned dataframe sorted by ``scheme_code`` and ``date`` with essential columns
        converted to appropriate types and duplicates removed.
    """

    if frame.index.name and _normalise_label(frame.index.name) == "scheme_code":
        frame = frame.reset_index()

    normalised = normalise_columns(frame)

    required = set(required_columns or ("scheme_code", "date", "nav"))
    missing = required - set(normalised.columns)
    if missing:
        raise ValueError(f"Missing required columns in NAV history: {sorted(missing)}")

    cleaned = normalised.copy()
    cleaned["scheme_code"] = cleaned["scheme_code"].astype(str)
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce", utc=True)
    cleaned["date"] = cleaned["date"].dt.tz_localize(None)
    cleaned["nav"] = pd.to_numeric(cleaned["nav"], errors="coerce")

    cleaned = cleaned.dropna(subset=["scheme_code", "date", "nav"])
    cleaned = cleaned.sort_values(["scheme_code", "date"])
    cleaned = cleaned.drop_duplicates(subset=["scheme_code", "date"], keep="last")
    cleaned = cleaned.reset_index(drop=True)

    return cleaned
