"""Robustness tests: LOO, winsorization, bootstrap, era splits."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.return_models.expected_car import _bootstrap_interval


def leave_one_out_analysis(returns: np.ndarray, labels: np.ndarray | None = None) -> pd.DataFrame:
    returns = np.asarray(returns, dtype=float)
    base_mean = returns.mean()
    rows = []
    for i in range(len(returns)):
        mask = np.ones(len(returns), dtype=bool)
        mask[i] = False
        new_mean = returns[mask].mean()
        rows.append({
            "dropped_index": i,
            "label": labels[i] if labels is not None else None,
            "dropped_return": float(returns[i]),
            "mean_without": float(new_mean),
            "delta_mean": float(new_mean - base_mean),
        })
    return pd.DataFrame(rows)


def winsorized_mean(returns: np.ndarray, cap: float) -> float:
    r = np.clip(np.asarray(returns, dtype=float), -cap, cap)
    return float(r.mean())


def trimmed_mean(returns: np.ndarray, proportion: float = 0.10) -> float:
    r = np.sort(np.asarray(returns, dtype=float))
    k = int(len(r) * proportion)
    if k == 0:
        return float(r.mean())
    return float(r[k:-k].mean())


def bootstrap_short_strategy(
    returns: np.ndarray,
    n_boot: int = 5000,
    seed: int = 42,
) -> dict:
    returns = np.asarray(returns, dtype=float)
    if len(returns) == 0:
        return {"n": 0}
    rng = np.random.default_rng(seed)
    boot_means = [rng.choice(returns, size=len(returns), replace=True).mean() for _ in range(n_boot)]
    boot_means = np.array(boot_means)
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    p_positive = float(np.mean(boot_means > 0))
    # Permutation test H0: mean <= 0
    obs = returns.mean()
    perm_means = []
    for _ in range(min(n_boot, 2000)):
        signs = rng.choice([-1, 1], size=len(returns))
        perm_means.append((returns * signs).mean())
    p_perm = float(np.mean(np.array(perm_means) >= obs))
    se = returns.std(ddof=1) / np.sqrt(len(returns)) if len(returns) > 1 else np.nan
    t_stat = obs / se if se and se > 0 else np.nan
    p_ttest = 2 * (1 - stats.t.cdf(abs(t_stat), len(returns) - 1)) if se and se > 0 else np.nan
    return {
        "n": len(returns),
        "observed_mean": float(obs),
        "bootstrap_ci_95": (float(lo), float(hi)),
        "p_mean_positive": p_positive,
        "permutation_p_value": p_perm,
        "t_stat": float(t_stat) if t_stat == t_stat else None,
        "ttest_p_value": float(p_ttest) if p_ttest == p_ttest else None,
    }


def block_bootstrap_by_year(
    df: pd.DataFrame,
    return_col: str = "realized_short_return",
    year_col: str = "test_year",
    n_boot: int = 2000,
    seed: int = 42,
) -> dict:
    rng = np.random.default_rng(seed)
    years = df[year_col].unique().tolist()
    if not years:
        return {"n": 0}
    boot_means = []
    for _ in range(n_boot):
        sampled_years = rng.choice(years, size=len(years), replace=True)
        parts = [df.loc[df[year_col] == y, return_col].values for y in sampled_years]
        flat = np.concatenate(parts) if parts else np.array([])
        if len(flat):
            boot_means.append(flat.mean())
    if not boot_means:
        return {"n": 0}
    boot_means = np.array(boot_means)
    return {
        "n_years": len(years),
        "n_obs": len(df),
        "block_bootstrap_ci_95": (float(np.percentile(boot_means, 2.5)), float(np.percentile(boot_means, 97.5))),
        "p_mean_positive": float(np.mean(boot_means > 0)),
    }


def era_split_analysis(preds: pd.DataFrame, trades_mask: pd.Series) -> pd.DataFrame:
    traded = preds[trades_mask].copy()
    eras = [
        ("early_2010_2016", traded["catalyst_year"] <= 2016),
        ("middle_2017_2020", (traded["catalyst_year"] >= 2017) & (traded["catalyst_year"] <= 2020)),
        ("late_2021_plus", traded["catalyst_year"] >= 2021),
    ]
    rows = []
    for name, mask in eras:
        sub = traded[mask]
        if sub.empty:
            continue
        rets = sub["realized_short_return"]
        lo, hi = _bootstrap_interval(rets.values)
        rows.append({
            "era": name,
            "n": len(sub),
            "mean_short_return": float(rets.mean()),
            "ci_95": (lo, hi),
            "win_rate": float((rets > 0).mean()),
        })
    return pd.DataFrame(rows)


def slippage_stress_test(trades: pd.DataFrame, bps_list: list[float]) -> pd.DataFrame:
    from src.short_edge.short_score import realized_short_return

    rows = []
    for bps in bps_list:
        rets = realized_short_return(trades["realized_car"].values, bps)
        lo, hi = _bootstrap_interval(rets)
        rows.append({
            "slippage_bps": bps,
            "n": len(rets),
            "mean_short_return": float(rets.mean()),
            "ci_95": (lo, hi),
            "win_rate": float((rets > 0).mean()),
        })
    return pd.DataFrame(rows)


def run_robustness_suite(preds: pd.DataFrame, strategy_mask: pd.Series) -> dict:
    trades = preds[strategy_mask].copy()
    if trades.empty:
        return {"n_trades": 0}
    rets = trades["realized_short_return"].values
    labels = trades.get("drug_name", pd.Series([None] * len(trades))).values
    return {
        "n_trades": len(trades),
        "bootstrap": bootstrap_short_strategy(rets),
        "block_bootstrap": block_bootstrap_by_year(trades),
        "leave_one_out": leave_one_out_analysis(rets, labels),
        "winsorized_means": {
            "cap_50pct": winsorized_mean(rets, 0.50),
            "cap_30pct": winsorized_mean(rets, 0.30),
            "cap_20pct": winsorized_mean(rets, 0.20),
        },
        "trimmed_mean_10pct": trimmed_mean(rets, 0.10),
        "era_splits": era_split_analysis(preds, strategy_mask),
    }
