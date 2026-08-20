"""Shared trade signal classification for walk-forward and ranking."""

from __future__ import annotations

import pandas as pd


def classify_signal_from_percentile(pct: float, cfg: dict) -> str:
    rk = cfg["ranking"]
    if pct >= rk["strong_long_percentile"]:
        return "STRONG LONG"
    if pct >= rk["long_percentile"]:
        return "LONG"
    if pct <= rk["strong_short_percentile"]:
        return "STRONG SHORT"
    if pct <= rk["short_percentile"]:
        return "SHORT"
    return "NO TRADE"


def assign_percentile_signals(preds: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Assign cross-sectional percentile signals within each test_year group."""
    out = preds.copy()
    out["expected_car_pct"] = out.groupby("test_year")["expected_car_adj"].rank(pct=True)
    out["trade_signal"] = out["expected_car_pct"].apply(
        lambda p: classify_signal_from_percentile(float(p), cfg)
    )
    return out


def assign_fixed_signals(expected_car_adj: float, cfg: dict) -> str:
    """Fixed absolute thresholds (legacy)."""
    if expected_car_adj > 0.05:
        return "STRONG LONG"
    if expected_car_adj > 0.03:
        return "LONG"
    if expected_car_adj < -0.05:
        return "STRONG SHORT"
    if expected_car_adj < -0.03:
        return "SHORT"
    return "NO_TRADE"
