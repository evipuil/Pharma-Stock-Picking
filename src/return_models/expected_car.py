"""Models B/C: E(CAR | success/failure) and expected CAR assembly."""

from __future__ import annotations

import pickle
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import load_yaml, project_root
from src.models.baselines import load_benchmark_rates, lookup_pos_rate
from src.return_models.dataset import (
    load_catalyst_modeling_frame,
    resolve_split_feature_cols,
)


@dataclass
class ExpectedCarBundle:
    version: str = "expected_car_v1"
    p_success_model: Pipeline | None = None
    car_success_model: Pipeline | None = None
    car_failure_model: Pipeline | None = None
    feature_cols: list[str] = field(default_factory=list)
    p_feature_cols: list[str] = field(default_factory=list)
    car_feature_cols: list[str] = field(default_factory=list)
    car_success_fallback: float = 0.0
    car_failure_fallback: float = -0.10
    training_data_policy: str = "unverified"
    metrics: dict = field(default_factory=dict)


def _make_ridge() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=1.0)),
        ]
    )


def _make_logistic(seed: int) -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    penalty="l2",
                    C=1.0,
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=seed,
                ),
            ),
        ]
    )


def _fit_conditional_car(
    df: pd.DataFrame,
    feature_cols: list[str],
    outcome: int,
) -> Pipeline | None:
    sub = df[df["clinical_success"] == outcome].dropna(subset=["realized_car"])
    if len(sub) < 5:
        return None
    X = sub[feature_cols]
    y = sub["realized_car"].values
    model = _make_ridge()
    model.fit(X, y)
    return model


def conditional_car_fallbacks(
    train: pd.DataFrame,
    *,
    success_default: float = 0.0,
    failure_default: float = -0.10,
) -> tuple[float, float]:
    """Freeze conditional-return fallbacks from training data only."""
    success = train.loc[train["clinical_success"] == 1, "realized_car"].dropna()
    failure = train.loc[train["clinical_success"] == 0, "realized_car"].dropna()
    success_mean = float(success.mean()) if len(success) else float(success_default)
    failure_mean = float(failure.mean()) if len(failure) else float(failure_default)
    return success_mean, failure_mean


def _bootstrap_interval(
    values: np.ndarray, n_boot: int = 500, seed: int = 42
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    if len(values) == 0:
        return np.nan, np.nan
    means = []
    for _ in range(n_boot):
        sample = rng.choice(values, size=len(values), replace=True)
        means.append(sample.mean())
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def train_expected_car_models(
    feature_set: str = "market_plus_trial",
) -> ExpectedCarBundle:
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    seed = cfg["random_seed"]
    df = load_catalyst_modeling_frame()

    p_cols, car_cols = resolve_split_feature_cols(feature_set)

    # Model A: P(success) — trial design + optional preclinical/market
    p_model = _make_logistic(seed)
    y = df["clinical_success"].astype(int).values
    p_model.fit(df[p_cols], y)

    # Models B/C: conditional CAR regressions — market expectations only
    car_success = _fit_conditional_car(df, car_cols, outcome=1)
    car_failure = _fit_conditional_car(df, car_cols, outcome=0)
    success_fallback, failure_fallback = conditional_car_fallbacks(df)

    bundle = ExpectedCarBundle(
        feature_cols=p_cols,
        p_feature_cols=p_cols,
        car_feature_cols=car_cols,
        p_success_model=p_model,
        car_success_model=car_success,
        car_failure_model=car_failure,
        car_success_fallback=success_fallback,
        car_failure_fallback=failure_fallback,
        training_data_policy="strict_point_in_time_sanitized",
    )

    # In-sample metrics for monitoring (not for final claims)
    preds = predict_expected_car(df, bundle)
    bundle.metrics = {
        "n": len(df),
        "n_success": int(y.sum()),
        "realized_car_mean": float(df["realized_car"].mean()),
        "expected_car_mean": float(preds["expected_car"].mean()),
        "correlation_expected_vs_realized": float(preds["expected_car"].corr(preds["realized_car"]))
        if preds["expected_car"].notna().sum() > 2
        else None,
        "market_features_verified_at_cutoff": int(
            df.get("market_features_point_in_time", pd.Series(False)).sum()
        ),
        "trial_features_verified_at_cutoff": int(
            df.get("trial_features_point_in_time", pd.Series(False)).sum()
        ),
        "unverified_features_nulled": True,
    }
    return bundle


def predict_expected_car(df: pd.DataFrame, bundle: ExpectedCarBundle) -> pd.DataFrame:
    """Return dataframe with p_success, e_car_success, e_car_failure, expected_car."""
    out = df.copy()
    p_cols = bundle.p_feature_cols or bundle.feature_cols
    car_cols = bundle.car_feature_cols or bundle.feature_cols

    out["p_success"] = bundle.p_success_model.predict_proba(df[p_cols])[:, 1]

    if bundle.car_success_model is not None:
        out["e_car_given_success"] = bundle.car_success_model.predict(df[car_cols])
    else:
        out["e_car_given_success"] = bundle.car_success_fallback

    if bundle.car_failure_model is not None:
        out["e_car_given_failure"] = bundle.car_failure_model.predict(df[car_cols])
    else:
        out["e_car_given_failure"] = bundle.car_failure_fallback

    out["expected_car"] = (
        out["p_success"] * out["e_car_given_success"]
        + (1 - out["p_success"]) * out["e_car_given_failure"]
    )
    return out


def predict_with_wong_prior(
    df: pd.DataFrame,
    calibration_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Baseline using Wong PoS and conditional CAR frozen on calibration data."""
    rates = load_benchmark_rates(project_root() / "data" / "external" / "wong2019_pos_rates.csv")
    out = df.copy()
    calibration = calibration_df if calibration_df is not None else df
    ps = []
    for _, row in out.iterrows():
        p = lookup_pos_rate(rates, "PHASE2", "oncology", row.get("modality"))
        ps.append(p if p is not None else calibration["clinical_success"].mean())
    out["p_success"] = ps
    succ_mean, fail_mean = conditional_car_fallbacks(calibration)
    out["e_car_given_success"] = succ_mean
    out["e_car_given_failure"] = fail_mean
    out["expected_car"] = (
        out["p_success"] * out["e_car_given_success"]
        + (1 - out["p_success"]) * out["e_car_given_failure"]
    )
    return out


def save_bundle(bundle: ExpectedCarBundle, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(bundle, f)


def load_bundle(path: Path) -> ExpectedCarBundle:
    with path.open("rb") as f:
        return pickle.load(f)


def persist_predictions(
    preds: pd.DataFrame,
    train_cutoff_year: int | None,
    split: str,
    model_version: str,
) -> int:
    db_path = project_root() / "data" / "processed" / "research.db"
    import sqlite3

    conn = sqlite3.connect(db_path)
    schema = project_root() / "sql" / "schema_predictions.sql"
    conn.executescript(schema.read_text(encoding="utf-8"))
    n = 0
    for _, row in preds.iterrows():
        conn.execute(
            """
            INSERT OR REPLACE INTO catalyst_predictions (
                prediction_id, catalyst_id, model_version, p_success,
                e_car_given_success, e_car_given_failure, expected_car,
                train_cutoff_year, prediction_split, feature_set
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                row["catalyst_id"],
                model_version,
                float(row["p_success"]),
                float(row["e_car_given_success"]) if pd.notna(row["e_car_given_success"]) else None,
                float(row["e_car_given_failure"]) if pd.notna(row["e_car_given_failure"]) else None,
                float(row["expected_car"]),
                train_cutoff_year,
                split,
                model_version,
            ),
        )
        n += 1
    conn.commit()
    conn.close()
    return n


def export_predictions_csv(preds: pd.DataFrame, path: Path | None = None) -> Path:
    path = path or project_root() / "data" / "out_of_sample_predictions.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "catalyst_id",
        "drug_name",
        "indication",
        "ticker",
        "catalyst_year",
        "clinical_success",
        "realized_car",
        "p_success",
        "e_car_given_success",
        "e_car_given_failure",
        "expected_car",
    ]
    preds[[c for c in cols if c in preds.columns]].to_csv(path, index=False)
    return path
