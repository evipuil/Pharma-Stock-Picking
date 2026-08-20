"""Tests for backtest grid."""

import pandas as pd

from src.backtest.grid import apply_slippage, bootstrap_significance


def test_apply_slippage_reduces_returns():
    trades = pd.DataFrame({"side": [1, -1], "realized_car": [0.10, -0.05]})
    out = apply_slippage(trades, slippage_bps=25)
    assert out["net_return"].iloc[0] < 0.10
    assert out["slippage_cost"].iloc[0] == 0.005


def test_bootstrap_significance_positive_mean():
    returns = pd.Series([0.05, 0.03, 0.02, 0.04, 0.01]).values
    result = bootstrap_significance(returns, n_boot=200, seed=42)
    assert result["observed_mean"] > 0
    assert "p_value" in result
