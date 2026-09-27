"""Feature ablation for short strategy OOS performance."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import project_root

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


def generate_ablation_report(
    feature_sets: list[str] | None = None,
    output_path: Path | None = None,
) -> Path:
    """Run feature ablations and write markdown report."""
    df = run_feature_ablations(feature_sets=feature_sets)
    output_path = output_path or project_root() / "reports" / "short_edge_ablation.md"

    lines = [
        "# Short-Edge Feature Ablation",
        "",
        "Compares OOS short strategy performance across predefined feature sets.",
        "No hyperparameter tuning on test outcomes.",
        "",
    ]
    if df.empty:
        lines.append("_No ablation results._")
    else:
        pivot = df.sort_values(["feature_set", "strategy"])
        lines.append("## OOS short returns by feature set")
        lines.append("")
        lines.append(
            pivot[
                [
                    "feature_set",
                    "strategy",
                    "n_trades",
                    "mean_short_return",
                    "win_rate",
                    "hit_rate_car_below_10pct",
                ]
            ].to_string(index=False)
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    csv_path = project_root() / "data" / "processed" / "short_edge_ablation.csv"
    df.to_csv(csv_path, index=False)
    return output_path
