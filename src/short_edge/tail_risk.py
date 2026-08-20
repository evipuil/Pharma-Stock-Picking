"""Tail-risk models: P(CAR <= -20%) and catastrophic drop."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.short_edge.p_failure import _make_logistic


def _make_ridge_pos() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=5.0)),
        ]
    )


@dataclass
class TailRiskBundle:
    classifier: Pipeline
    magnitude_model: Pipeline | None
    feature_cols: list[str]
    drop_threshold: float = -0.20
    metrics: dict = field(default_factory=dict)


def fit_tail_risk(
    train: pd.DataFrame,
    feature_cols: list[str],
    drop_threshold: float = -0.20,
    seed: int = 42,
) -> TailRiskBundle:
    y_cls = (train["realized_car"] <= drop_threshold).astype(int).values
    clf = _make_logistic(seed)
    if len(np.unique(y_cls)) < 2:
        # Degenerate: fit constant-probability stub via dummy fit on subset
        clf.fit(train[feature_cols].iloc[: max(2, len(train))], np.array([0, 1])[: max(2, len(train))])
    else:
        clf.fit(train[feature_cols], y_cls)

    mag_model = None
    majors = train[train["realized_car"] <= drop_threshold]
    if len(majors) >= 5:
        mag_model = _make_ridge_pos()
        mag_model.fit(majors[feature_cols], majors["realized_car"].values)

    return TailRiskBundle(
        classifier=clf,
        magnitude_model=mag_model,
        feature_cols=feature_cols,
        drop_threshold=drop_threshold,
    )


def predict_tail_risk(df: pd.DataFrame, bundle: TailRiskBundle) -> pd.DataFrame:
    out = df.copy()
    out["p_major_drop"] = bundle.classifier.predict_proba(df[bundle.feature_cols])[:, 1]
    if bundle.magnitude_model is not None:
        out["expected_drop_magnitude"] = bundle.magnitude_model.predict(df[bundle.feature_cols])
    else:
        out["expected_drop_magnitude"] = float(
            df.loc[df["realized_car"] <= bundle.drop_threshold, "realized_car"].mean()
            if "realized_car" in df.columns and (df["realized_car"] <= bundle.drop_threshold).any()
            else bundle.drop_threshold
        )
    out["tail_risk_score"] = out["p_major_drop"] * (-out["expected_drop_magnitude"].clip(upper=0))
    return out


def evaluate_tail_classifier(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    if len(np.unique(y_true)) < 2:
        return {"roc_auc": None, "pr_auc": None, "base_rate": float(y_true.mean())}
    return {
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "pr_auc": float(average_precision_score(y_true, y_prob)),
        "base_rate": float(y_true.mean()),
    }


def precision_at_k(y_true: np.ndarray, scores: np.ndarray, k: int) -> float:
    if k <= 0 or len(scores) == 0:
        return float("nan")
    k = min(k, len(scores))
    idx = np.argsort(scores)[::-1][:k]
    return float(np.asarray(y_true)[idx].mean())
