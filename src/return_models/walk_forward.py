"""Walk-forward OOS evaluation for expected CAR models."""

from __future__ import annotations

import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_yaml, project_root
from src.fundamentals.exposure import load_exposure_frame
from src.return_models.dataset import load_catalyst_modeling_frame, resolve_split_feature_cols
from src.ranking.signals import assign_percentile_signals
from src.return_models.expected_car import (
    ExpectedCarBundle,
    _fit_conditional_car,
    _make_logistic,
    export_predictions_csv,
    predict_expected_car,
    predict_with_wong_prior,
)


def run_walk_forward(
    initial_train_end: int | None = None,
    step_years: int | None = None,
    feature_set: str = "market_plus_trial",
) -> pd.DataFrame:
    """
    Expanding-window walk-forward:
    Train on catalysts with year <= train_end, predict on test_year = train_end + 1.
    """
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    wf = cfg["walk_forward"]
    initial_train_end = initial_train_end or wf["initial_train_end_year"]
    step_years = step_years or wf["step_years"]
    seed = cfg["random_seed"]

    df = load_catalyst_modeling_frame()
    df = df.dropna(subset=["catalyst_year"]).copy()
    max_year = int(df["catalyst_year"].max())
    p_cols, car_cols = resolve_split_feature_cols(feature_set)

    ledger_rows: list[dict] = []
    oos_preds: list[pd.DataFrame] = []

    train_end = initial_train_end
    while train_end < max_year:
        test_year = train_end + step_years
        train = df[df["catalyst_year"] <= train_end]
        test = df[df["catalyst_year"] == test_year]
        if len(train) < 10 or test.empty:
            train_end += step_years
            continue

        # Fit models on train only
        p_model = _make_logistic(seed)
        p_model.fit(train[p_cols], train["clinical_success"].astype(int))

        bundle = ExpectedCarBundle(
            version=f"wf_{train_end}",
            feature_cols=p_cols,
            p_feature_cols=p_cols,
            car_feature_cols=car_cols,
            p_success_model=p_model,
            car_success_model=_fit_conditional_car(train, car_cols, 1),
            car_failure_model=_fit_conditional_car(train, car_cols, 0),
        )

        preds = predict_expected_car(test, bundle)
        exposure = load_exposure_frame()
        preds = preds.merge(
            exposure[["catalyst_id", "company_dependency"]], on="catalyst_id", how="left"
        )
        preds["company_dependency"] = preds["company_dependency"].fillna(0.9)
        preds["expected_car_adj"] = preds["expected_car"] * preds["company_dependency"]
        preds["train_end_year"] = train_end
        preds["test_year"] = test_year
        preds["split"] = "oos"
        preds = assign_percentile_signals(preds, cfg)
        oos_preds.append(preds)

        for _, row in preds.iterrows():
            ledger_rows.append(
                {
                    "ledger_id": str(uuid.uuid4()),
                    "catalyst_id": row["catalyst_id"],
                    "train_end_year": train_end,
                    "test_year": test_year,
                    "p_success": float(row["p_success"]),
                    "expected_car": float(row["expected_car_adj"]),
                    "realized_car": float(row["realized_car"]),
                    "clinical_success": int(row["clinical_success"]),
                    "trade_signal": row["trade_signal"],
                    "model_version": bundle.version,
                }
            )
        train_end += step_years

    ledger = pd.DataFrame(ledger_rows)
    if not ledger.empty:
        _persist_ledger(ledger)
        all_oos = pd.concat(oos_preds, ignore_index=True)
        export_predictions_csv(all_oos, project_root() / "data" / "out_of_sample_predictions.csv")

    return ledger


def _signal_percentile(preds: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Deprecated alias — use assign_percentile_signals."""
    return assign_percentile_signals(preds, cfg)


def _persist_ledger(ledger: pd.DataFrame) -> None:
    import sqlite3

    db_path = project_root() / "data" / "processed" / "research.db"
    schema = project_root() / "sql" / "schema_predictions.sql"
    conn = sqlite3.connect(db_path)
    conn.executescript(schema.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM walk_forward_ledger")
    for _, row in ledger.iterrows():
        conn.execute(
            """
            INSERT OR REPLACE INTO walk_forward_ledger (
                ledger_id, catalyst_id, train_end_year, test_year,
                p_success, expected_car, realized_car, clinical_success,
                trade_signal, model_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["ledger_id"],
                row["catalyst_id"],
                int(row["train_end_year"]),
                int(row["test_year"]),
                row["p_success"],
                row["expected_car"],
                row["realized_car"],
                row["clinical_success"],
                row["trade_signal"],
                row["model_version"],
            ),
        )
    conn.commit()
    conn.close()


def summarize_walk_forward(ledger: pd.DataFrame) -> dict:
    if ledger.empty:
        return {"n_oos": 0}
    longs = ledger[ledger["trade_signal"].isin(["LONG", "STRONG LONG"])]
    shorts = ledger[ledger["trade_signal"].isin(["SHORT", "STRONG SHORT"])]
    return {
        "n_oos": len(ledger),
        "mean_realized_car_all": float(ledger["realized_car"].mean()),
        "mean_realized_car_long": float(longs["realized_car"].mean()) if len(longs) else None,
        "mean_realized_car_short": float(shorts["realized_car"].mean()) if len(shorts) else None,
        "correlation_expected_realized": float(
            ledger["expected_car"].corr(ledger["realized_car"])
        ),
        "n_long_signals": len(longs),
        "n_short_signals": len(shorts),
    }


def compare_baselines() -> dict:
    """Compare full model vs Wong prior on same OOS ledger structure."""
    df = load_catalyst_modeling_frame()
    full = predict_expected_car(
        df,
        __import__("src.return_models.expected_car", fromlist=["train_expected_car_models"]).train_expected_car_models(),
    )
    wong = predict_with_wong_prior(df)
    return {
        "full_model_corr": float(full["expected_car"].corr(full["realized_car"])),
        "wong_prior_corr": float(wong["expected_car"].corr(wong["realized_car"])),
        "full_mean_expected": float(full["expected_car"].mean()),
        "wong_mean_expected": float(wong["expected_car"].mean()),
    }
