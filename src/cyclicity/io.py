"""Data loading and preprocessing utilities."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Mapping, Optional

import numpy as np
import pandas as pd

from common.data_ingestion import prepare_nav_history
from .utils import CacheConfig, CacheManager

LOGGER = logging.getLogger(__name__)


def _ensure_cache_manager(cache: Optional[CacheConfig | Mapping[str, object]]) -> CacheManager:
    if cache is None:
        return CacheManager(CacheConfig(enabled=False))
    if isinstance(cache, CacheConfig):
        return CacheManager(cache)
    return CacheManager(CacheConfig(**cache))


def load_nav_history(
    config: Mapping[str, object],
    cache: Optional[CacheConfig | Mapping[str, object]] = None,
) -> pd.DataFrame:
    """Load and preprocess the mutual fund NAV history dataset.

    Parameters
    ----------
    config:
        Configuration dictionary with keys ``parquet_path`` and ``min_points``.
    cache:
        Optional cache configuration to reuse previously processed results.

    Returns
    -------
    pandas.DataFrame
        A tidy dataframe indexed by ``scheme_code`` and ``date`` containing
        monthly NAV and log NAV columns.
    """

    cache_manager = _ensure_cache_manager(cache)
    cached = cache_manager.load_frame("nav_history")
    if cached is not None:
        LOGGER.info("Loaded NAV history from cache")
        return cached

    parquet_path = Path(str(config.get("parquet_path", "data/mutual_fund_nav_history.parquet")))
    min_points = int(config.get("min_points", 60))

    if not parquet_path.exists():
        raise FileNotFoundError(f"NAV history file not found at {parquet_path}")

    LOGGER.info("Loading NAV history from %s", parquet_path)
    df = prepare_nav_history(pd.read_parquet(parquet_path))

    def _resample(group: pd.DataFrame) -> pd.DataFrame:
        scheme_code = group["scheme_code"].iloc[0]
        monthly = (
            group.set_index("date")["nav"].resample("ME").last().dropna().to_frame("nav")
        )
        monthly["scheme_code"] = scheme_code
        return monthly.reset_index()

    LOGGER.info("Resampling NAV history to month-end frequency")
    monthly_df = df.groupby("scheme_code", group_keys=False).apply(_resample)

    counts = monthly_df.groupby("scheme_code")["date"].count()
    valid_schemes = counts[counts >= min_points].index
    if not len(valid_schemes):
        raise ValueError("No schemes with sufficient history after resampling")

    monthly_df = monthly_df[monthly_df["scheme_code"].isin(valid_schemes)]
    monthly_df["log_nav"] = np.log(monthly_df["nav"])

    monthly_df = monthly_df.set_index(["scheme_code", "date"]).sort_index()

    cache_manager.dump_frame("nav_history", monthly_df)
    LOGGER.info("Loaded %d schemes for analysis", len(valid_schemes))

    return monthly_df


__all__ = ["load_nav_history"]
