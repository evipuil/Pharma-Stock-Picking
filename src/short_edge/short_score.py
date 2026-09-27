"""Expected short return score and net return after costs."""

from __future__ import annotations

import numpy as np
import pandas as pd


def top_fraction_mask(
    df: pd.DataFrame,
    score_col: str,
    fraction: float,
    group_col: str = "test_year",
) -> pd.Series:
    """Select the top score fraction independently inside each OOS fold.

    A cutoff computed across the complete OOS history can use the distribution of
    future scores to decide whether an earlier observation was tradable.  Ranking
    inside each test-year fold preserves the decision set that was available then.
    """
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    if score_col not in df.columns:
        raise KeyError(f"missing score column: {score_col}")

    selected = pd.Series(False, index=df.index, dtype=bool)
    groups = df.groupby(group_col, sort=True) if group_col in df.columns else [(None, df)]
    for _, group in groups:
        valid = group.dropna(subset=[score_col])
        if valid.empty:
            continue
        n_select = max(1, int(np.ceil(len(valid) * fraction)))
        chosen = valid.nlargest(n_select, score_col, keep="first").index
        selected.loc[chosen] = True
    return selected


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


def realized_short_return(
    realized_car: np.ndarray,
    slippage_bps: float = 25.0,
    borrow_bps_annual: float = 300.0,
    hold_days: float = 3.0,
) -> np.ndarray:
    """Realized short P&L after round-trip slippage and prorated borrow."""
    slip = 2 * slippage_bps / 10_000
    borrow = (borrow_bps_annual / 10_000) * (hold_days / 252)
    return -np.asarray(realized_car, dtype=float) - slip - borrow


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
        side.loc[top_fraction_mask(df, score_col, 0.10)] = -1
    elif strategy == "short_top_20pct":
        side.loc[top_fraction_mask(df, score_col, 0.20)] = -1
    elif (
        strategy == "min_esr_10pct"
        or strategy == "min_esr_20pct"
        or strategy == "major_drop_threshold"
    ):
        side.loc[df[score_col] >= param] = -1
    return side
