"""Ablation: compare feature sets for investment-return prediction."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import project_root
from src.return_models.dataset import load_catalyst_modeling_frame
from src.return_models.expected_car import (
    predict_expected_car,
    predict_with_wong_prior,
    train_expected_car_models,
)
from src.validation.holdout_eval import summarize_holdout


def run_ablation(db_path: Path | None = None) -> pd.DataFrame:
    """In-sample correlation by model variant (monitoring only)."""
    df = load_catalyst_modeling_frame(db_path)
    rows: list[dict] = []

    for feature_set in (
        "market_only",
        "market_plus_trial",
        "market_plus_preclinical",
        "market_plus_trial_plus_preclinical",
    ):
        bundle = train_expected_car_models(feature_set=feature_set)
        preds = predict_expected_car(df, bundle)
        corr = preds["expected_car"].corr(preds["realized_car"])
        rows.append(
            {
                "model": feature_set,
                "split": "in_sample",
                "n": len(preds),
                "correlation": corr,
                "mean_expected_car": float(preds["expected_car"].mean()),
                "mean_realized_car": float(preds["realized_car"].mean()),
            }
        )

    wong = predict_with_wong_prior(df)
    rows.append(
        {
            "model": "wong_prior",
            "split": "in_sample",
            "n": len(wong),
            "correlation": wong["expected_car"].corr(wong["realized_car"]),
            "mean_expected_car": float(wong["expected_car"].mean()),
            "mean_realized_car": float(wong["realized_car"].mean()),
        }
    )

    # Locked holdout comparison
    from src.validation.holdout_eval import run_holdout_baselines

    holdout = run_holdout_baselines(db_path)
    for name, preds in holdout.items():
        summary = summarize_holdout(preds)
        rows.append(
            {
                "model": name,
                "split": "locked_holdout",
                "n": summary.get("n", 0),
                "correlation": summary.get("correlation_expected_realized"),
                "mean_expected_car": summary.get("mean_expected_car_adj"),
                "mean_realized_car": summary.get("mean_realized_car"),
            }
        )

    return pd.DataFrame(rows)


def generate_ablation_report(db_path: Path | None = None) -> Path:
    df = run_ablation(db_path)
    lines = [
        "# Ablation Study: Expected CAR Models",
        "",
        "Compares market-only, market+preclinical, and Wong prior baselines.",
        "",
        df.to_string(index=False),
        "",
    ]
    out = project_root() / "reports" / "ablation_study.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")

    csv_path = project_root() / "data" / "processed" / "ablation_results.csv"
    df.to_csv(csv_path, index=False)
    return out
