"""Simple backtester: walk-forward ledger → trade P&L with slippage."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_yaml, project_root
from src.return_models.expected_car import _bootstrap_interval


def build_trade_ledger(db_path: Path | None = None) -> pd.DataFrame:
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    slip = cfg["trading"]["default_slippage_bps"] / 10_000
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)

    ledger = pd.read_sql_query(
        """
        SELECT wf.*, c.drug_name, c.indication, ct.ticker_at_event,
               ae.company_dependency
        FROM walk_forward_ledger wf
        JOIN catalysts c ON wf.catalyst_id = c.catalyst_id
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        LEFT JOIN asset_exposure ae ON c.catalyst_id = ae.catalyst_id
        WHERE wf.trade_signal IN ('LONG', 'SHORT', 'STRONG LONG', 'STRONG SHORT')
           OR wf.expected_car IS NOT NULL
        """,
        conn,
    )
    conn.close()

    if ledger.empty:
        return pd.DataFrame()

    # Re-derive signals with exposure adjustment if not in ledger
    dep = ledger["company_dependency"].fillna(0.9)
    ledger["expected_car_adj"] = ledger["expected_car"] * dep

    def _side(row):
        sig = row.get("trade_signal", "NO_TRADE")
        if sig in ("LONG", "STRONG LONG"):
            return 1
        if sig in ("SHORT", "STRONG SHORT"):
            return -1
        if row["expected_car_adj"] > 0.03:
            return 1
        if row["expected_car_adj"] < -0.03:
            return -1
        return 0

    ledger["side"] = ledger.apply(_side, axis=1)
    traded = ledger[ledger["side"] != 0].copy()
    if traded.empty:
        return traded

    # P&L = side × realized CAR − round-trip slippage
    traded["gross_return"] = traded["side"] * traded["realized_car"]
    traded["slippage_cost"] = 2 * slip  # entry + exit
    traded["net_return"] = traded["gross_return"] - traded["slippage_cost"]
    traded["position_pct"] = cfg["trading"]["max_position_pct"]

    return traded.sort_values(["test_year", "net_return"], ascending=[True, False])


def summarize_backtest(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"n_trades": 0}
    rets = trades["net_return"]
    boot_lo, boot_hi = _bootstrap_interval(rets.values)
    return {
        "n_trades": len(trades),
        "win_rate": float((rets > 0).mean()),
        "mean_return_per_trade": float(rets.mean()),
        "mean_return_ci_95": (boot_lo, boot_hi),
        "median_return_per_trade": float(rets.median()),
        "total_return_equal_weight": float(rets.sum()),
        "sharpe_approx": float(rets.mean() / rets.std()) if rets.std() > 0 else None,
        "long_mean": float(trades.loc[trades["side"] == 1, "net_return"].mean())
        if (trades["side"] == 1).any()
        else None,
        "short_mean": float(trades.loc[trades["side"] == -1, "net_return"].mean())
        if (trades["side"] == -1).any()
        else None,
    }


def export_trade_ledger(trades: pd.DataFrame, path: Path | None = None) -> Path:
    path = path or project_root() / "data" / "trade_ledger.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    trades.to_csv(path, index=False)
    return path


def generate_backtest_report(trades: pd.DataFrame) -> Path:
    summary = summarize_backtest(trades)
    lines = [
        "# Backtest Report (Walk-Forward OOS)",
        "",
        "## Methodology",
        "- Signals from exposure-adjusted expected CAR",
        "- Entry before catalyst; exit on announcement window CAR",
        f"- Slippage: {load_yaml(project_root() / 'configs/stock_picking.yaml')['trading']['default_slippage_bps']} bps round-trip",
        "",
        "## Summary",
        "",
    ]
    for k, v in summary.items():
        lines.append(f"- {k}: {v}")

    if not trades.empty:
        lines.extend(["", "## Trades", "", trades.to_string(index=False)])

    out = project_root() / "reports" / "backtest.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
