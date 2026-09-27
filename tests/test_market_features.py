"""Tests for pre-catalyst market feature computation."""

from __future__ import annotations

import pandas as pd

from src.market_expectations.features import compute_features_for_catalyst


def test_features_use_only_pre_cutoff_data():
    dates = pd.date_range("2020-01-01", periods=100, freq="B")
    prices = pd.DataFrame(
        {
            "date": dates,
            "adj_close": [100 + i * 0.5 for i in range(100)],
            "volume": [1_000_000] * 100,
        }
    )
    xbi = pd.Series(0.001, index=dates[1:])
    cutoff = pd.Timestamp("2020-04-01")
    feats = compute_features_for_catalyst("TEST", cutoff, prices, xbi)
    assert feats is not None
    assert feats["return_20d"] is not None
    assert feats["price_at_cutoff"] > 100
    assert pd.Timestamp(feats["feature_as_of_date"]) < cutoff


def test_insufficient_history_returns_none():
    dates = pd.date_range("2020-01-01", periods=10, freq="B")
    prices = pd.DataFrame({"date": dates, "adj_close": range(10), "volume": [1] * 10})
    xbi = pd.Series(dtype=float)
    feats = compute_features_for_catalyst("TEST", pd.Timestamp("2020-01-15"), prices, xbi)
    assert feats is None
