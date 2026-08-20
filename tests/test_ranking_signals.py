"""Tests for percentile trade signals."""

import pandas as pd

from src.config import load_yaml, project_root
from src.ranking.signals import assign_percentile_signals, classify_signal_from_percentile


def test_percentile_signals_within_year():
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    # Need n>=10 so rank(pct=True) yields 0.10 for the minimum (strong short cutoff).
    preds = pd.DataFrame(
        {
            "test_year": [2020] * 10,
            "expected_car_adj": [-0.05, -0.04, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.05, 0.08],
        }
    )
    out = assign_percentile_signals(preds, cfg)
    assert out["trade_signal"].iloc[0] == "STRONG SHORT"
    assert out["trade_signal"].iloc[-1] == "STRONG LONG"


def test_classify_signal_thresholds():
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    assert classify_signal_from_percentile(0.95, cfg) == "STRONG LONG"
    assert classify_signal_from_percentile(0.50, cfg) == "NO TRADE"
