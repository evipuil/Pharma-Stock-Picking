"""Feature ablation for short strategy OOS performance."""

from __future__ import annotations

import pandas as pd

from src.short_edge.baselines import evaluate_model_short_strategy
from src.short_edge.dataset import FEATURE_SETS
from src.short_edge.walk_forward import run_short_walk_forward


def run_feature_ablations(
    feature_sets: list[str] | None = None,
) -> pd.DataFrame:
    feature_sets = feature_sets or [
        "company_only",
        "market_only",
        "clinical_only",
        "preclinical_only",
        "market_plus_company",
        "clinical_plus_market",
        "everything_no_preclinical",
        "everything",
    ]
    rows = []
    for fs in feature_sets:
        if fs not in FEATURE_SETS and fs != "everything_no_preclinical":
            continue
        preds = run_short_walk_forward(feature_set=fs)
        for strat in ["short_top_20pct", "short_top_10pct"]:
            r = evaluate_model_short_strategy(preds, strategy=strat)
            r["feature_set"] = fs
            rows.append(r)
    return pd.DataFrame(rows)
