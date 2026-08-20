"""Multi-strategy backtest grid: slippage sensitivity + signal variants."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest.ledger import summarize_backtest
from src.config import load_yaml, project_root
from src.return_models.expected_car import _bootstrap_interval


def _load_oos_ledger(db_path: Path | None = None) -> pd.DataFrame:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    ledger = pd.read_sql_query(
        """
        SELECT wf.*, c.drug_name, c.indication, c.announcement_date,
               ct.ticker_at_event, ae.company_dependency
        FROM walk_forward_ledger wf
        JOIN catalysts c ON wf.catalyst_id = c.catalyst_id
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        LEFT JOIN asset_exposure ae ON c.catalyst_id = ae.catalyst_id
        """,
        conn,
    )
    conn.close()
    if ledger.empty:
        return ledger
    dep = ledger["company_dependency"].fillna(0.9)
    ledger["expected_car_adj"] = ledger["expected_car"] * dep
    return ledger


def apply_slippage(trades: pd.DataFrame, slippage_bps: float) -> pd.DataFrame:
    slip = slippage_bps / 10_000
    out = trades.copy()
    out["slippage_bps"] = slippage_bps
    out["gross_return"] = out["side"] * out["realized_car"]
    out["slippage_cost"] = 2 * slip
    out["net_return"] = out["gross_return"] - out["slippage_cost"]
    return out


def _assign_sides_threshold(ledger: pd.DataFrame, min_expected_car: float) -> pd.DataFrame:
    out = ledger.copy()
    out["side"] = 0
    out.loc[out["expected_car_adj"] >= min_expected_car, "side"] = 1
    out.loc[out["expected_car_adj"] <= -min_expected_car, "side"] = -1
    return out


def _assign_sides_top_k(ledger: pd.DataFrame, k: int) -> pd.DataFrame:
    out = ledger.copy()
    out["side"] = 0
    for year, grp in out.groupby("test_year"):
        longs = grp.nlargest(k, "expected_car_adj")
        shorts = grp.nsmallest(k, "expected_car_adj")
        out.loc[longs.index, "side"] = 1
        out.loc[shorts.index, "side"] = -1
    return out


def _assign_sides_walkforward(ledger: pd.DataFrame) -> pd.DataFrame:
    out = ledger.copy()

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

    out["side"] = out.apply(_side, axis=1)
    return out


def run_slippage_grid(
    slippage_bps_list: list[float] | None = None,
    db_path: Path | None = None,
) -> pd.DataFrame:
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    slippage_bps_list = slippage_bps_list or cfg.get("trading", {}).get(
        "slippage_grid_bps", [0, 25, 50, 75, 100]
    )
    ledger = _load_oos_ledger(db_path)
    if ledger.empty:
        return pd.DataFrame()

    base = _assign_sides_walkforward(ledger)
    traded = base[base["side"] != 0].copy()
    rows = []
    for bps in slippage_bps_list:
        t = apply_slippage(traded, bps)
        summary = summarize_backtest(t)
        summary["strategy"] = "walkforward_threshold"
        summary["slippage_bps"] = bps
        rows.append(summary)
    return pd.DataFrame(rows)


def run_strategy_grid(db_path: Path | None = None) -> pd.DataFrame:
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    slip = cfg["trading"]["default_slippage_bps"]
    grid_cfg = cfg.get("strategies", {}).get("predefined_grid", [])
    ledger = _load_oos_ledger(db_path)
    if ledger.empty:
        return pd.DataFrame()

    rows: list[dict] = []

    # Baseline walk-forward signals
    base = _assign_sides_walkforward(ledger)
    traded = base[base["side"] != 0]
    if not traded.empty:
        summary = summarize_backtest(apply_slippage(traded, slip))
        summary["strategy"] = "walkforward_threshold"
        summary["param"] = "default"
        rows.append(summary)

    for spec in grid_cfg:
        name = spec["name"]
        if name == "long_top_k":
            for k in spec.get("k", [3]):
                sided = _assign_sides_top_k(ledger, k)
                t = apply_slippage(sided[sided["side"] != 0], slip)
                if t.empty:
                    continue
                summary = summarize_backtest(t)
                summary["strategy"] = name
                summary["param"] = f"k={k}"
                rows.append(summary)
        elif name == "threshold":
            for thresh in spec.get("min_expected_car", [0.05]):
                sided = _assign_sides_threshold(ledger, thresh)
                t = apply_slippage(sided[sided["side"] != 0], slip)
                if t.empty:
                    continue
                summary = summarize_backtest(t)
                summary["strategy"] = name
                summary["param"] = f"min={thresh:.0%}"
                rows.append(summary)

    return pd.DataFrame(rows)


def bootstrap_significance(returns: np.ndarray, n_boot: int = 1000, seed: int = 42) -> dict:
    """Test H0: mean return <= 0 via bootstrap."""
    if len(returns) == 0:
        return {"p_value": None, "significant_05": False}
    rng = np.random.default_rng(seed)
    obs = float(np.mean(returns))
    boot_means = []
    for _ in range(n_boot):
        sample = rng.choice(returns, size=len(returns), replace=True)
        boot_means.append(float(np.mean(sample)))
    p_value = float(np.mean(np.array(boot_means) <= 0))
    return {
        "observed_mean": obs,
        "p_value": p_value,
        "significant_05": p_value < 0.05,
        "ci_95": _bootstrap_interval(returns, n_boot=n_boot, seed=seed),
    }


def generate_backtest_grid_report(db_path: Path | None = None) -> Path:
    slip_df = run_slippage_grid(db_path=db_path)
    strat_df = run_strategy_grid(db_path=db_path)

    ledger = _load_oos_ledger(db_path)
    sig = {}
    if not ledger.empty:
        sided = _assign_sides_walkforward(ledger)
        traded = sided[sided["side"] != 0]
        if not traded.empty:
            traded = apply_slippage(
                traded,
                load_yaml(project_root() / "configs" / "stock_picking.yaml")["trading"][
                    "default_slippage_bps"
                ],
            )
            sig = bootstrap_significance(traded["net_return"].values)

    lines = [
        "# Backtest Grid Report",
        "",
        "## Bootstrap significance (walk-forward OOS, default slippage)",
        "",
    ]
    for k, v in sig.items():
        lines.append(f"- {k}: {v}")

    lines.extend(["", "## Slippage sensitivity", ""])
    if not slip_df.empty:
        lines.append(slip_df.to_string(index=False))
    else:
        lines.append("No OOS trades.")

    lines.extend(["", "## Strategy variants", ""])
    if not strat_df.empty:
        lines.append(strat_df.to_string(index=False))
    else:
        lines.append("No strategy results.")

    out = project_root() / "reports" / "backtest_grid.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")

    csv_path = project_root() / "data" / "processed" / "backtest_grid.csv"
    combined = pd.concat([slip_df, strat_df], ignore_index=True, sort=False)
    combined.to_csv(csv_path, index=False)
    return out
