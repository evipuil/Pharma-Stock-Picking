"""Models B/C: conditional CAR given failure/success with shrinkage."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.short_edge.dataset import shrinkage_mean


def _make_ridge() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=5.0)),
        ]
    )


@dataclass
class ConditionalCarBundle:
    failure_model: Pipeline | None
    success_model: Pipeline | None
    feature_cols: list[str]
    failure_shrinkage_mean: float = -0.10
    success_shrinkage_mean: float = -0.003
    metrics: dict = field(default_factory=dict)


def fit_conditional_car(
    train: pd.DataFrame,
    feature_cols: list[str],
    shrinkage_k: float = 8.0,
) -> ConditionalCarBundle:
    failures = train[train["clinical_failure"] == 1].dropna(subset=["realized_car"])
    successes = train[train["clinical_failure"] == 0].dropna(subset=["realized_car"])

    global_fail = (
        float(train.loc[train["clinical_failure"] == 1, "realized_car"].mean())
        if (train["clinical_failure"] == 1).any()
        else -0.10
    )
    global_succ = (
        float(train.loc[train["clinical_failure"] == 0, "realized_car"].mean())
        if (train["clinical_failure"] == 0).any()
        else -0.003
    )

    fail_model = None
    succ_model = None

    if len(failures) >= 8:
        fail_model = _make_ridge()
        fail_model.fit(failures[feature_cols], failures["realized_car"].values)
    if len(successes) >= 8:
        succ_model = _make_ridge()
        succ_model.fit(successes[feature_cols], successes["realized_car"].values)

    return ConditionalCarBundle(
        failure_model=fail_model,
        success_model=succ_model,
        feature_cols=feature_cols,
        failure_shrinkage_mean=shrinkage_mean(failures["realized_car"], global_fail, shrinkage_k),
        success_shrinkage_mean=shrinkage_mean(successes["realized_car"], global_succ, shrinkage_k),
    )


def predict_car_failure(df: pd.DataFrame, bundle: ConditionalCarBundle) -> np.ndarray:
    if bundle.failure_model is not None:
        raw = bundle.failure_model.predict(df[bundle.feature_cols])
        return np.minimum(raw, 0.0)  # failures should not predict positive CAR on average
    return np.full(len(df), bundle.failure_shrinkage_mean)


def predict_car_success(df: pd.DataFrame, bundle: ConditionalCarBundle) -> np.ndarray:
    if bundle.success_model is not None:
        return bundle.success_model.predict(df[bundle.feature_cols])
    return np.full(len(df), bundle.success_shrinkage_mean)
