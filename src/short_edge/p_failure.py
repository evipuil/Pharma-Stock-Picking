"""Model A: P(failure) with calibration diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def _make_logistic(seed: int = 42) -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    penalty="l2",
                    C=1.0,
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=seed,
                ),
            ),
        ]
    )


@dataclass
class FailureModelBundle:
    model: Pipeline
    feature_cols: list[str]
    seed: int = 42
    metrics: dict = field(default_factory=dict)


def fit_p_failure(
    train: pd.DataFrame,
    feature_cols: list[str],
    seed: int = 42,
    target_col: str = "clinical_failure",
) -> FailureModelBundle:
    model = _make_logistic(seed)
    y = train[target_col].astype(int).values
    model.fit(train[feature_cols], y)
    return FailureModelBundle(model=model, feature_cols=feature_cols, seed=seed)


def predict_p_failure(df: pd.DataFrame, bundle: FailureModelBundle) -> np.ndarray:
    return bundle.model.predict_proba(df[bundle.feature_cols])[:, 1]


def evaluate_p_failure(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    label: str = "eval",
) -> dict:
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    out: dict = {"label": label, "n": len(y_true), "n_failures": int(y_true.sum())}

    if len(np.unique(y_true)) < 2:
        out["roc_auc"] = None
        out["pr_auc"] = None
    else:
        out["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        out["pr_auc"] = float(average_precision_score(y_true, y_prob))

    out["brier"] = float(brier_score_loss(y_true, y_prob))
    out["log_loss"] = float(log_loss(y_true, np.clip(y_prob, 1e-6, 1 - 1e-6)))

    # Calibration slope via logistic regression on logit(p)
    eps = 1e-6
    logit_p = np.log(np.clip(y_prob, eps, 1 - eps) / np.clip(1 - y_prob, eps, 1 - eps))
    if len(y_true) >= 10 and len(np.unique(y_true)) == 2:
        from sklearn.linear_model import LinearRegression

        lr = LinearRegression().fit(logit_p.reshape(-1, 1), y_true)
        out["calibration_slope"] = float(lr.coef_[0])
        out["calibration_intercept"] = float(lr.intercept_)
    else:
        out["calibration_slope"] = None
        out["calibration_intercept"] = None

    return out


def reliability_bins(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 5) -> pd.DataFrame:
    if len(y_true) < n_bins * 2:
        return pd.DataFrame()
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="quantile")
    return pd.DataFrame({"predicted_mean": prob_pred, "observed_rate": prob_true})
