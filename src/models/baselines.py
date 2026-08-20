"""Baseline PoS lookup from Wong/BIO tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_benchmark_rates(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def lookup_pos_rate(
    rates: pd.DataFrame,
    phase: str,
    indication_group: str,
    modality: str | None = None,
) -> float | None:
    """Hierarchical fallback lookup for baseline probability."""
    filters = [
        rates[
            (rates["phase"] == phase)
            & (rates["indication_group"] == indication_group)
            & (rates["modality"] == modality)
        ],
        rates[(rates["phase"] == phase) & (rates["indication_group"] == indication_group)],
        rates[(rates["phase"] == phase) & (rates["modality"] == modality)],
        rates[rates["phase"] == phase],
    ]
    for subset in filters:
        if not subset.empty:
            return float(subset.iloc[0]["success_rate"])
    return None
