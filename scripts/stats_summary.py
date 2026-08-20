"""One-off statistical summary for stock-picking pipeline."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "research.db"


def bootstrap_ci(x: np.ndarray, n_boot: int = 5000, alpha: float = 0.05, seed: int = 42) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    means = [rng.choice(x, size=len(x), replace=True).mean() for _ in range(n_boot)]
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def main() -> None:
    conn = sqlite3.connect(DB)

    es = pd.read_sql(
        """
        SELECT c.catalyst_id, c.clinical_success, es.car
        FROM catalysts c
        JOIN catalyst_event_study es ON c.catalyst_id = es.catalyst_id
        WHERE es.window_label = '[-1,+1]' AND es.benchmark = 'MARKET_MODEL' AND es.car IS NOT NULL
        """,
        conn,
    )
    n_cat = pd.read_sql("SELECT COUNT(*) AS n FROM catalysts", conn).iloc[0]["n"]
    print("=== EVENT STUDY ===")
    print(f"Catalysts total: {n_cat}, with CAR: {len(es)} ({100*len(es)/n_cat:.1f}%)")
    print(f"Mean CAR: {es['car'].mean():.4f}, Median: {es['car'].median():.4f}, Std: {es['car'].std():.4f}")
    fail = es[es.clinical_success == 0]["car"]
    succ = es[es.clinical_success == 1]["car"]
    t, p = stats.ttest_ind(fail, succ, equal_var=False)
    print(f"Failure n={len(fail)} mean={fail.mean():.4f}; Success n={len(succ)} mean={succ.mean():.4f}")
    print(f"Welch t-test (fail vs success): t={t:.3f}, p={p:.4f}")
    d = (succ.mean() - fail.mean()) / np.sqrt((fail.var() + succ.var()) / 2)
    print(f"Cohen's d (success - failure): {d:.3f}")

    wf = pd.read_sql("SELECT * FROM walk_forward_ledger", conn)
    print("\n=== WALK-FORWARD OOS ===")
    print(f"OOS rows: {len(wf)}")
    mask = wf["realized_car"].notna() & wf["expected_car"].notna()
    if mask.sum() > 2:
        r = wf.loc[mask, "expected_car"].corr(wf.loc[mask, "realized_car"])
        print(f"Corr(expected, realized) all OOS: {r:.4f} (n={mask.sum()})")
    trade = wf[wf["trade_signal"].isin(["LONG", "SHORT", "STRONG LONG", "STRONG SHORT"])]
    print(f"Trade signals: {len(trade)}")
    mask2 = trade["realized_car"].notna() & trade["expected_car"].notna()
    if mask2.sum() > 2:
        r2 = trade.loc[mask2, "expected_car"].corr(trade.loc[mask2, "realized_car"])
        print(f"Corr on signaled trades: {r2:.4f} (n={mask2.sum()})")
    print(f"Mean realized CAR (all OOS): {wf['realized_car'].mean():.4f}")
    print(f"Mean expected CAR (all OOS): {wf['expected_car'].mean():.4f}")
    longs = trade[trade["trade_signal"].str.contains("LONG", na=False)]
    shorts = trade[trade["trade_signal"].str.contains("SHORT", na=False)]
    print(f"Long signals n={len(longs)} mean realized={longs['realized_car'].mean():.4f}")
    print(f"Short signals n={len(shorts)} mean realized={shorts['realized_car'].mean():.4f}")

    bt_path = ROOT / "data" / "trade_ledger.csv"
    if bt_path.exists():
        bt = pd.read_csv(bt_path)
        print("\n=== BACKTEST (trade ledger) ===")
        print(f"Trades: {len(bt)}, Win rate: {(bt['net_return'] > 0).mean():.1%}")
        print(f"Mean net return/trade: {bt['net_return'].mean():.4f}, Median: {bt['net_return'].median():.4f}")
        se = bt["net_return"].std() / np.sqrt(len(bt))
        tstat = bt["net_return"].mean() / se if se > 0 else np.nan
        pval = 2 * (1 - stats.t.cdf(abs(tstat), len(bt) - 1)) if se > 0 else np.nan
        print(f"t-stat (mean=0): {tstat:.3f}, p={pval:.4f}")
        lo, hi = bootstrap_ci(bt["net_return"].values)
        print(f"Bootstrap 95% CI mean return: ({lo:.4f}, {hi:.4f})")
        print(f"Total equal-weight return (sum): {bt['net_return'].sum():.4f}")
        if bt["net_return"].std() > 0:
            sharpe = bt["net_return"].mean() / bt["net_return"].std()
            print(f"Per-trade Sharpe (not annualized): {sharpe:.4f}")
        if "side" in bt.columns:
            print(f"Long mean net: {bt[bt['side'] == 1]['net_return'].mean():.4f}")
            print(f"Short mean net: {bt[bt['side'] == -1]['net_return'].mean():.4f}")

    preds = pd.read_sql(
        "SELECT expected_car, realized_car, split FROM predictions WHERE realized_car IS NOT NULL",
        conn,
    )
    if not preds.empty:
        print("\n=== PREDICTIONS TABLE ===")
        for split in preds["split"].dropna().unique():
            sub = preds[preds["split"] == split].dropna(subset=["expected_car", "realized_car"])
            if len(sub) > 2:
                print(f"{split}: n={len(sub)}, corr={sub['expected_car'].corr(sub['realized_car']):.4f}")

    conn.close()


if __name__ == "__main__":
    main()
