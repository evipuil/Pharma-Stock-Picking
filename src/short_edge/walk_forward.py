"""Strict expanding-window walk-forward for short-edge models."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_yaml, project_root
from src.short_edge.conditional_car import (
    fit_conditional_car,
    predict_car_failure,
    predict_car_success,
)
from src.short_edge.dataset import load_short_edge_frame, resolve_features
from src.short_edge.p_failure import fit_p_failure, predict_p_failure
from src.short_edge.short_score import (
    apply_trading_costs,
    compute_expected_short_return,
    realized_short_return,
)
from src.short_edge.tail_risk import fit_tail_risk, predict_tail_risk


def _exclude_locked_holdout(df: pd.DataFrame, final_holdout_start: str) -> pd.DataFrame:
    """Return development rows strictly before the configured final holdout."""
    cutoff = pd.Timestamp(final_holdout_start)
    dates = pd.to_datetime(df["announcement_date"], errors="coerce")
    return df.loc[dates < cutoff].copy()


def _nested_major_drop_threshold(train: pd.DataFrame, feature_cols: list[str], seed: int) -> float:
    """Choose P(major drop) threshold using training data only via internal year CV."""
    cfg = load_yaml(project_root() / "configs" / "short_edge.yaml")
    candidates = [0.35, 0.45, 0.50, 0.55, 0.65]
    years = sorted(train["catalyst_year"].dropna().unique())
    if len(years) < 3:
        return cfg["strategies"]["major_drop_threshold"]

    best_t = candidates[0]
    best_score = -np.inf
    for t in candidates:
        scores = []
        for y in years[-3:]:
            inner_train = train[train["catalyst_year"] < y]
            inner_test = train[train["catalyst_year"] == y]
            if len(inner_train) < 15 or inner_test.empty:
                continue
            if (inner_train["realized_car"] <= -0.20).sum() < 2:
                continue
            try:
                bundle = fit_tail_risk(inner_train, feature_cols, seed=seed)
                preds = predict_tail_risk(inner_test, bundle)
            except ValueError:
                continue
            mask = preds["p_major_drop"] >= t
            if mask.sum() == 0:
                continue
            # Short return on flagged
            rets = realized_short_return(inner_test.loc[mask, "realized_car"].values)
            scores.append(rets.mean())
        if scores and np.mean(scores) > best_score:
            best_score = float(np.mean(scores))
            best_t = t
    return best_t


def run_short_walk_forward(
    feature_set: str = "everything_no_preclinical",
    db_path: Path | None = None,
    include_final_holdout: bool = False,
) -> pd.DataFrame:
    """Run development OOS folds, excluding the locked holdout by default.

    ``include_final_holdout`` is intentionally explicit so routine reports and
    feature ablations cannot consume the final evaluation period accidentally.
    """
    cfg = load_yaml(project_root() / "configs" / "short_edge.yaml")
    sp_cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    seed = cfg.get("random_seed", 42)
    initial_train_end = sp_cfg["walk_forward"]["initial_train_end_year"]
    step = sp_cfg["walk_forward"]["step_years"]
    slip = cfg["costs"]["default_slippage_bps"]
    borrow = cfg["costs"]["borrow_cost_bps_annual"]
    hold = cfg["costs"]["hold_days"]

    df = load_short_edge_frame(db_path)
    df = df.dropna(subset=["catalyst_year"]).copy()
    if not include_final_holdout:
        df = _exclude_locked_holdout(df, cfg["holdout"]["final_locked_start"])
    p_cols = resolve_features(feature_set)
    car_cols = resolve_features("market_plus_company")

    rows: list[dict] = []
    train_end = initial_train_end
    max_year = int(df["catalyst_year"].max())

    while train_end < max_year:
        test_year = train_end + step
        train = df[df["catalyst_year"] <= train_end].copy()
        test = df[df["catalyst_year"] == test_year].copy()
        if len(train) < 15 or test.empty:
            train_end += step
            continue

        p_bundle = fit_p_failure(train, p_cols, seed=seed)
        car_bundle = fit_conditional_car(train, car_cols)
        tail_bundle = fit_tail_risk(train, p_cols, seed=seed)
        major_thresh = _nested_major_drop_threshold(train, p_cols, seed)

        p_fail = predict_p_failure(test, p_bundle)
        car_fail = predict_car_failure(test, car_bundle)
        car_succ = predict_car_success(test, car_bundle)
        dep = test["company_dependency"].values

        exp_car, exp_short = compute_expected_short_return(p_fail, car_fail, car_succ, dep)
        net_short = apply_trading_costs(exp_short, slip, borrow, hold)

        tail_preds = predict_tail_risk(test, tail_bundle)

        for i, (_, row) in enumerate(test.iterrows()):
            real_short = float(
                realized_short_return(
                    np.array([row["realized_car"]]),
                    slip,
                    borrow,
                    hold,
                )[0]
            )
            rows.append(
                {
                    "prediction_id": str(uuid.uuid4()),
                    "catalyst_id": row["catalyst_id"],
                    "ticker": row["ticker"],
                    "drug_name": row["drug_name"],
                    "announcement_date": row["announcement_date"],
                    "train_end_year": train_end,
                    "test_year": test_year,
                    "catalyst_year": int(row["catalyst_year"]),
                    "feature_timestamp": row.get("feature_as_of_date"),
                    "p_failure": float(p_fail[i]),
                    "p_success": float(1 - p_fail[i]),
                    "car_failure_pred": float(car_fail[i]),
                    "car_success_pred": float(car_succ[i]),
                    "expected_car": float(exp_car[i]),
                    "expected_short_return": float(exp_short[i]),
                    "net_expected_short_return": float(net_short[i]),
                    "p_major_drop": float(tail_preds.iloc[i]["p_major_drop"]),
                    "tail_risk_score": float(tail_preds.iloc[i]["tail_risk_score"]),
                    "major_drop_threshold": major_thresh,
                    "company_dependency": float(dep[i]),
                    "realized_car": float(row["realized_car"]),
                    "realized_short_return": real_short,
                    "clinical_failure": int(row["clinical_failure"]),
                    "major_negative_event": int(row["major_negative_event"]),
                    "model_version": f"short_wf_{train_end}",
                    "feature_set": feature_set,
                }
            )
        train_end += step

    return pd.DataFrame(rows)


def persist_short_predictions(preds: pd.DataFrame, db_path: Path | None = None) -> None:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS short_oos_predictions (
            prediction_id TEXT PRIMARY KEY,
            catalyst_id TEXT,
            ticker TEXT,
            train_end_year INTEGER,
            test_year INTEGER,
            p_failure REAL,
            expected_short_return REAL,
            net_expected_short_return REAL,
            p_major_drop REAL,
            tail_risk_score REAL,
            realized_car REAL,
            realized_short_return REAL,
            model_version TEXT
        )
        """
    )
    conn.execute("DELETE FROM short_oos_predictions")
    for _, row in preds.iterrows():
        conn.execute(
            """
            INSERT INTO short_oos_predictions (
                prediction_id, catalyst_id, ticker, train_end_year, test_year,
                p_failure, expected_short_return, net_expected_short_return,
                p_major_drop, tail_risk_score, realized_car, realized_short_return,
                model_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["prediction_id"],
                row["catalyst_id"],
                row["ticker"],
                int(row["train_end_year"]),
                int(row["test_year"]),
                row["p_failure"],
                row["expected_short_return"],
                row["net_expected_short_return"],
                row["p_major_drop"],
                row["tail_risk_score"],
                row["realized_car"],
                row["realized_short_return"],
                row["model_version"],
            ),
        )
    conn.commit()
    conn.close()


def export_short_predictions(preds: pd.DataFrame, path: Path | None = None) -> Path:
    path = path or project_root() / "data" / "oos_short_predictions.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    preds.to_csv(path, index=False)
    return path
