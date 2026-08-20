"""Event study CAR computation (Phase 3)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def estimate_market_model_beta(
    stock_returns: pd.Series,
    market_returns: pd.Series,
) -> tuple[float, float]:
    """OLS estimate of alpha and beta for market model."""
    aligned = pd.concat([stock_returns, market_returns], axis=1, join="inner").dropna()
    if len(aligned) < 10:
        return 0.0, 1.0
    y = aligned.iloc[:, 0].values
    x = aligned.iloc[:, 1].values
    x_with_const = np.column_stack([np.ones(len(x)), x])
    coef, _, _, _ = np.linalg.lstsq(x_with_const, y, rcond=None)
    return float(coef[0]), float(coef[1])


def cumulative_abnormal_return(
    stock_returns: pd.Series,
    market_returns: pd.Series,
    alpha: float,
    beta: float,
    event_idx: pd.DatetimeIndex,
) -> float:
    ar = stock_returns.loc[event_idx] - (alpha + beta * market_returns.loc[event_idx])
    return float(ar.sum())
