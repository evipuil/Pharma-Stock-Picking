"""Expected short return score and net return after costs."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_expected_short_return(
    p_failure: np.ndarray,
    car_failure: np.ndarray,
    car_success: np.ndarray,
    company_dependency: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Expected stock CAR (negative => stock falls):
        E[CAR] = P_fail * CAR_fail + P_succ * CAR_succ

    Expected short return (before costs) = -E[CAR]

    If company_dependency provided, scale failure downside:
        E[CAR_adj] = P_fail * CAR_fail * dep + P_succ * CAR_succ * dep
    """
    p_failure = np.asarray(p_failure, dtype=float)
    p_success = 1.0 - p_failure
    car_failure = np.asarray(car_failure, dtype=float)
    car_success = np.asarray(car_success, dtype=float)

    if company_dependency is not None:
        dep = np.asarray(company_dependency, dtype=float)
        expected_car = p_failure * car_failure * dep + p_success * car_success * dep
    else:
        expected_car = p_failure * car_failure + p_success * car_success

    expected_short = -expected_car
    return expected_car, expected_short


def apply_trading_costs(
    expected_short: np.ndarray,
    slippage_bps: float = 25.0,
    borrow_bps_annual: float = 300.0,
    hold_days: float = 3.0,
) -> np.ndarray:
    """Subtract round-trip slippage and prorated borrow from expected short return."""
    slip = 2 * slippage_bps / 10_000
    borrow = (borrow_bps_annual / 10_000) * (hold_days / 252)
    return expected_short - slip - borrow


def realized_short_return(realized_car: np.ndarray, slippage_bps: float = 25.0) -> np.ndarray:
    """Realized short P&L = -realized_car - slippage."""
    slip = 2 * slippage_bps / 10_000
    return -np.asarray(realized_car, dtype=float) - slip


def assign_short_trades(
    df: pd.DataFrame,
    score_col: str,
    strategy: str,
    param: float,
) -> pd.Series:
    """
    Predefined short strategies:
      short_top_10pct, short_top_20pct
      min_esr_10pct, min_esr_20pct  (expected short return thresholds)
    """
    side = pd.Series(0, index=df.index)
    if strategy == "short_top_10pct":
        cutoff = df[score_col].quantile(0.90)
        side.loc[df[score_col] >= cutoff] = -1
    elif strategy == "short_top_20pct":
        cutoff = df[score_col].quantile(0.80)
        side.loc[df[score_col] >= cutoff] = -1
    elif strategy == "min_esr_10pct":
        side.loc[df[score_col] >= param] = -1
    elif strategy == "min_esr_20pct":
        side.loc[df[score_col] >= param] = -1
    elif strategy == "major_drop_threshold":
        side.loc[df[score_col] >= param] = -1
    return side
