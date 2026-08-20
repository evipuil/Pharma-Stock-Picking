"""Portfolio-level simulation for short-only catalyst strategy."""

from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_short_portfolio(
    trades: pd.DataFrame,
    starting_capital: float = 100_000.0,
    max_position_pct: float = 0.02,
    max_total_short_exposure: float = 0.20,
    slippage_bps: float = 25.0,
) -> dict:
    """
    Simple event-driven portfolio: each trade opens at announcement-1d proxy,
    closes at announcement window. Positions sized at min(max_position_pct, remaining capacity).
    """
    if trades.empty:
        return {"n_trades": 0}

    df = trades.sort_values("announcement_date").copy()
    capital = starting_capital
    nav_history = []
    exposures = []

    for _, row in df.iterrows():
        current_exposure = sum(p["notional"] for p in nav_history if p.get("open", False))
        capacity = max(0.0, starting_capital * max_total_short_exposure - current_exposure)
        notional = min(starting_capital * max_position_pct, capacity)
        if notional <= 0:
            continue
        slip = 2 * slippage_bps / 10_000
        gross = -row["realized_car"] * notional
        cost = notional * slip
        pnl = gross - cost
        capital += pnl
        nav_history.append({
            "date": row["announcement_date"],
            "catalyst_id": row["catalyst_id"],
            "ticker": row.get("ticker"),
            "notional": notional,
            "pnl": pnl,
            "capital_after": capital,
            "open": False,
        })
        exposures.append(notional / starting_capital)

    if not nav_history:
        return {"n_trades": 0}

    nav_df = pd.DataFrame(nav_history)
    nav_series = nav_df["capital_after"].values
    returns = np.diff(np.insert(nav_series, 0, starting_capital)) / starting_capital
    total_return = (capital - starting_capital) / starting_capital
    vol = float(np.std(returns)) if len(returns) > 1 else 0.0
    sharpe = float(np.mean(returns) / vol * np.sqrt(252)) if vol > 0 else None
    downside = returns[returns < 0]
    sortino = float(np.mean(returns) / np.std(downside) * np.sqrt(252)) if len(downside) > 1 and np.std(downside) > 0 else None
    peak = np.maximum.accumulate(nav_series)
    dd = (nav_series - peak) / peak
    max_dd = float(dd.min()) if len(dd) else 0.0

    return {
        "n_trades": len(nav_df),
        "starting_capital": starting_capital,
        "ending_capital": float(capital),
        "total_return": float(total_return),
        "mean_exposure": float(np.mean(exposures)) if exposures else 0.0,
        "max_exposure": float(np.max(exposures)) if exposures else 0.0,
        "volatility_approx": vol,
        "sharpe_approx": sharpe,
        "sortino_approx": sortino,
        "max_drawdown": max_dd,
        "nav_history": nav_df,
    }
