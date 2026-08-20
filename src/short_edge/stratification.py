"""Prespecified stratification diagnostics for downside asymmetry."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.return_models.expected_car import _bootstrap_interval
from src.short_edge.short_score import realized_short_return


STRATIFICATIONS = {
    "small_cap_vs_large_cap": lambda df: np.where(df["is_small_cap"] == 1, "small_cap", "large_or_mid"),
    "lead_vs_diversified": lambda df: np.where(df["high_dependency"] == 1, "high_dependency", "low_dependency"),
    "phase_2_vs_phase_3": lambda df: np.where(df["phase_3"] == 1, "phase_3", np.where(df["phase_2"] == 1, "phase_2", "other")),
    "momentum_positive_vs_negative": lambda df: np.where(df["high_momentum"] == 1, "positive_momentum", "negative_or_flat"),
    "high_vs_low_volatility": lambda df: np.where(df["high_volatility"] == 1, "high_vol", "low_vol"),
    "oncology_vs_other": lambda df: np.where(df["indication"].str.contains("NSCLC|melanoma|breast|AML|DLBCL|RCC|ovarian|TNBC|lymphoma|myeloma|HCC|CLL", case=False, na=False), "oncology_like", "other"),
}


def run_stratification_report(df: pd.DataFrame, slippage_bps: float = 25.0) -> pd.DataFrame:
    rows = []
    for strat_name, fn in STRATIFICATIONS.items():
        df = df.copy()
        df["_bucket"] = fn(df)
        for bucket, grp in df.groupby("_bucket"):
            if len(grp) < 3:
                continue
            fail = grp[grp["clinical_failure"] == 1]
            succ = grp[grp["clinical_failure"] == 0]
            short_rets = realized_short_return(grp["realized_car"].values, slippage_bps)
            lo, hi = _bootstrap_interval(short_rets)
            rows.append({
                "stratification": strat_name,
                "bucket": bucket,
                "n": len(grp),
                "failure_rate": float(grp["clinical_failure"].mean()),
                "success_mean_car": float(succ["realized_car"].mean()) if len(succ) else None,
                "failure_mean_car": float(fail["realized_car"].mean()) if len(fail) else None,
                "short_all_mean_return": float(short_rets.mean()),
                "short_all_ci_95": (lo, hi),
            })
    return pd.DataFrame(rows)
