"""Naive short baselines for comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.short_edge.short_score import realized_short_return

BASELINE_NAMES = [
    "short_all_catalysts",
    "short_phase_2",
    "short_phase_3",
    "short_small_cap",
    "short_high_dependency",
    "short_high_volatility",
    "short_negative_momentum",
    "random_short",
]


def assign_baseline_side(df: pd.DataFrame, name: str, seed: int = 42) -> pd.Series:
    side = pd.Series(0, index=df.index)
    if name == "short_all_catalysts":
        side[:] = -1
    elif name == "short_phase_2":
        side.loc[df["phase_2"] == 1] = -1
    elif name == "short_phase_3":
        side.loc[df["phase_3"] == 1] = -1
    elif name == "short_small_cap":
        side.loc[df["is_small_cap"] == 1] = -1
    elif name == "short_high_dependency":
        side.loc[df["high_dependency"] == 1] = -1
    elif name == "short_high_volatility":
        side.loc[df["high_volatility"] == 1] = -1
    elif name == "short_negative_momentum":
        side.loc[df["pre_catalyst_runup_60d"].fillna(0) < 0] = -1
    elif name == "random_short":
        rng = np.random.default_rng(seed)
        n = max(1, len(df) // 5)
        idx = rng.choice(df.index, size=min(n, len(df)), replace=False)
        side.loc[idx] = -1
    return side


def evaluate_baseline(
    df: pd.DataFrame, name: str, slippage_bps: float = 25.0, seed: int = 42
) -> dict:
    side = assign_baseline_side(df, name, seed)
    traded = df[side == -1].copy()
    if traded.empty:
        return {"baseline": name, "n_trades": 0}
    rets = realized_short_return(traded["realized_car"].values, slippage_bps)
    return {
        "baseline": name,
        "n_trades": len(traded),
        "mean_short_return": float(rets.mean()),
        "median_short_return": float(np.median(rets)),
        "win_rate": float((rets > 0).mean()),
        "hit_rate_car_below_10pct": float((traded["realized_car"] <= -0.10).mean()),
        "hit_rate_car_below_20pct": float((traded["realized_car"] <= -0.20).mean()),
    }


def evaluate_model_short_strategy(
    preds: pd.DataFrame,
    score_col: str = "net_expected_short_return",
    strategy: str = "short_top_20pct",
    param: float = 0.10,
    slippage_bps: float = 25.0,
) -> dict:
    from src.short_edge.short_score import assign_short_trades

    df = preds.copy()
    if strategy == "major_drop_threshold":
        mask = df["p_major_drop"] >= df["major_drop_threshold"]
    else:
        mask = assign_short_trades(df, score_col, strategy, param) == -1

    traded = df[mask]
    if traded.empty:
        return {"strategy": strategy, "n_trades": 0}
    rets = (
        traded["realized_short_return"].values
        if "realized_short_return" in traded.columns
        else realized_short_return(traded["realized_car"].values, slippage_bps)
    )
    return {
        "strategy": strategy,
        "score_col": score_col,
        "n_trades": len(traded),
        "mean_short_return": float(np.mean(rets)),
        "median_short_return": float(np.median(rets)),
        "win_rate": float((rets > 0).mean()),
        "hit_rate_car_below_10pct": float((traded["realized_car"] <= -0.10).mean()),
        "hit_rate_car_below_20pct": float((traded["realized_car"] <= -0.20).mean()),
        "precision_major_drop": float(traded["major_negative_event"].mean())
        if "major_negative_event" in traded.columns
        else None,
    }


def run_all_baselines(preds: pd.DataFrame, slippage_bps: float = 25.0) -> pd.DataFrame:
    from src.short_edge.dataset import load_short_edge_frame

    # Merge stratification columns if missing
    extra_cols = [
        "phase_2",
        "phase_3",
        "is_small_cap",
        "high_dependency",
        "high_volatility",
        "pre_catalyst_runup_60d",
        "realized_car",
        "major_negative_event",
        "clinical_failure",
    ]
    missing = [c for c in extra_cols if c not in preds.columns]
    if missing:
        frame = load_short_edge_frame()[
            ["catalyst_id"] + [c for c in missing if c in load_short_edge_frame().columns]
        ]
        preds = preds.merge(frame, on="catalyst_id", how="left", suffixes=("", "_dup"))
        preds = preds[[c for c in preds.columns if not c.endswith("_dup")]]

    rows = []
    for name in BASELINE_NAMES:
        rows.append(evaluate_baseline(preds, name, slippage_bps))
    # Model-ranked shorts
    for strat in [
        "short_top_10pct",
        "short_top_20pct",
        "min_esr_10pct",
        "min_esr_20pct",
        "major_drop_threshold",
    ]:
        param = 0.10 if "10" in strat else 0.20
        r = evaluate_model_short_strategy(
            preds, strategy=strat, param=param, slippage_bps=slippage_bps
        )
        r["baseline"] = f"model_{strat}"
        rows.append(r)
    return pd.DataFrame(rows)
