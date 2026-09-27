"""Generate model performance report for expected CAR."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import project_root
from src.return_models.expected_car import (
    export_predictions_csv,
    predict_expected_car,
    predict_with_wong_prior,
    train_expected_car_models,
)
from src.return_models.walk_forward import run_walk_forward, summarize_walk_forward


def generate_model_report(rerun_walk_forward: bool = False) -> Path:
    from src.return_models.dataset import load_catalyst_modeling_frame
    import sqlite3

    bundle = train_expected_car_models(feature_set="market_only")
    df = load_catalyst_modeling_frame()
    full = predict_expected_car(df, bundle)
    wong = predict_with_wong_prior(df)

    if rerun_walk_forward:
        ledger = run_walk_forward()
    else:
        db = project_root() / "data" / "processed" / "research.db"
        conn = sqlite3.connect(db)
        ledger = pd.read_sql("SELECT * FROM walk_forward_ledger", conn)
        conn.close()
    wf_summary = summarize_walk_forward(ledger)

    n = bundle.metrics.get("n", len(df))
    lines = [
        "# Model Performance Report",
        "",
        "## Expected CAR framework",
        "",
        "```",
        "Expected CAR = P(success) × E(CAR|success) + (1 − P(success)) × E(CAR|failure)",
        "```",
        "",
        f"## In-sample ({n} catalysts with CAR + market features)",
        "",
        f"- N: {n}",
        f"- Mean realized CAR [-1,+1]: {bundle.metrics.get('realized_car_mean', 0):.4f}",
        f"- Mean expected CAR: {bundle.metrics.get('expected_car_mean', 0):.4f}",
        f"- Corr(expected, realized): {bundle.metrics.get('correlation_expected_vs_realized')}",
        f"- Market features verified at cutoff: {bundle.metrics.get('market_features_verified_at_cutoff')}/{n}",
        f"- Trial snapshots verified at cutoff: {bundle.metrics.get('trial_features_verified_at_cutoff')}/{n}",
        "- Unverified feature values are nulled before fitting.",
        "",
        "## Baseline comparison (in-sample)",
        "",
        f"- Wong prior corr(expected, realized): {wong['expected_car'].corr(wong['realized_car']):.4f}",
        f"- Full model corr(expected, realized): {full['expected_car'].corr(full['realized_car']):.4f}",
        "",
        "## Walk-forward OOS",
        "",
    ]
    if wf_summary.get("n_oos", 0) == 0:
        lines.append("_Insufficient temporal spread for walk-forward folds._")
    else:
        for k, v in wf_summary.items():
            lines.append(f"- {k}: {v}")

    lines.extend(
        [
            "",
            "## Conditional CAR by outcome (realized, descriptive)",
            "",
            df.groupby("clinical_success")["realized_car"]
            .agg(["count", "mean", "median"])
            .to_string(),
            "",
            "## Notes",
            "",
            "- Models B/C use Ridge on pre-catalyst market features only (Stage 5).",
            "- P(success) uses logistic on same features (Model A provisional).",
            "- The 2019–2021 period is a legacy evaluation, not a pristine holdout; see holdout_evaluation.md.",
            f"- Priced sample: {n}/112 catalysts with event-study CAR.",
        ]
    )

    out = project_root() / "reports" / "model_performance.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")

    export_predictions_csv(full, project_root() / "data" / "processed" / "expected_car_predictions.csv")
    return out
