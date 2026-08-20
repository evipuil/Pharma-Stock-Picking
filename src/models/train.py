"""Train animal-features → clinical success prediction models."""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import load_yaml, project_root
from src.feature_engineering.build_matrix import (
    assign_temporal_split,
    build_feature_matrix,
)
from src.models.baselines import load_benchmark_rates, lookup_pos_rate


@dataclass
class TrainedModelBundle:
    name: str
    feature_set: str
    pipeline: Pipeline | CalibratedClassifierCV
    feature_columns: list[str]
    categorical_columns: list[str] = field(default_factory=list)
    numeric_columns: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    version: str = "v1.0"


def _prepare_Xy(
    df: pd.DataFrame,
    feature_cols: list[str],
) -> tuple[pd.DataFrame, np.ndarray, list[str], list[str]]:
    label = "clinical_success"
    cat_cols = [c for c in feature_cols if c in ("indication", "modality", "indication_group")]
    num_cols = [c for c in feature_cols if c not in cat_cols]

    X = df[feature_cols].copy()
    y = df[label].astype(int).values
    return X, y, cat_cols, num_cols


def _make_preprocessor(cat_cols: list[str], num_cols: list[str]) -> ColumnTransformer:
    transformers = []
    if num_cols:
        transformers.append(
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                num_cols,
            )
        )
    if cat_cols:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "onehot",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                cat_cols,
            )
        )
    return ColumnTransformer(transformers=transformers)


def _evaluate(y_true: np.ndarray, p_pred: np.ndarray) -> dict:
    metrics: dict = {
        "brier_score": float(brier_score_loss(y_true, p_pred)),
        "log_loss": float(log_loss(y_true, p_pred, labels=[0, 1])),
        "n": int(len(y_true)),
        "n_events": int(y_true.sum()),
    }
    if len(np.unique(y_true)) > 1 and len(np.unique(p_pred)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_true, p_pred))
    else:
        metrics["roc_auc"] = None
    return metrics


def train_baseline_wong(df: pd.DataFrame, rates_path: Path) -> tuple[np.ndarray, dict]:
    rates = load_benchmark_rates(rates_path)
    preds = []
    for _, row in df.iterrows():
        p = lookup_pos_rate(rates, "PHASE2", row.get("indication_group", "oncology"), row.get("modality"))
        preds.append(p if p is not None else df["clinical_success"].mean())
    p = np.array(preds)
    y = df["clinical_success"].astype(int).values
    return p, _evaluate(y, p)


def train_logistic_model(
    programs_df: pd.DataFrame | None = None,
    feature_set: str = "all_preclinical",
    calibrate: bool = True,
) -> TrainedModelBundle:
    cfg = load_yaml(project_root() / "configs" / "modeling.yaml")
    if programs_df is None:
        programs_df, feature_cols = build_feature_matrix(feature_set=feature_set)
    else:
        _, feature_cols = build_feature_matrix(feature_set=feature_set)
    if programs_df.empty:
        raise ValueError("No programs available for training")

    df = programs_df.copy()
    df["split"] = assign_temporal_split(df, cfg)

    # Include baseline clinical covariates for ablation comparison
    if feature_set == "baseline_plus_preclinical":
        feature_cols = list(
            dict.fromkeys(
                resolve_baseline_clinical_cols()
                + [c for c in feature_cols if c not in resolve_baseline_clinical_cols()]
            )
        )
        # Only use columns that exist or are added as NaN below
        feature_cols = [c for c in feature_cols if c in df.columns or c in resolve_baseline_clinical_cols()]
    elif feature_set == "baseline_clinical":
        feature_cols = resolve_baseline_clinical_cols()

    X, y, cat_cols, num_cols = _prepare_Xy(df, feature_cols)
    preprocessor = _make_preprocessor(cat_cols, num_cols)

    base_lr = LogisticRegression(
        penalty="l2",
        C=cfg["models"]["logistic"]["C"],
        max_iter=cfg["models"]["logistic"]["max_iter"],
        class_weight="balanced",
        random_state=cfg["random_seed"],
    )
    pipe: Pipeline | CalibratedClassifierCV
    estimator: Pipeline = Pipeline([("prep", preprocessor), ("clf", base_lr)])

    train_mask = df["split"] == "train"
    val_mask = df["split"] == "validation"
    test_mask = df["split"] == "test"

    # Small-N fallback: train on all data if train fold too small
    if train_mask.sum() < 4 or y[train_mask].sum() == 0 or (1 - y[train_mask]).sum() == 0:
        train_idx = np.ones(len(df), dtype=bool)
        val_idx = np.zeros(len(df), dtype=bool)
        test_idx = np.zeros(len(df), dtype=bool)
        note = "temporal_split_bypassed_small_n"
    else:
        train_idx = train_mask.values
        val_idx = val_mask.values
        test_idx = test_mask.values
        note = "temporal_split"

    estimator.fit(X[train_idx], y[train_idx])

    if calibrate and val_idx.sum() >= 3 and len(np.unique(y[val_idx])) > 1:
        pipe = CalibratedClassifierCV(estimator, method="isotonic", cv="prefit")
        pipe.fit(X[val_idx], y[val_idx])
    else:
        pipe = estimator

    # Evaluate on all available data (MVP) + holdout if exists
    p_all = pipe.predict_proba(X)[:, 1]
    metrics = {"train_note": note, "overall": _evaluate(y, p_all)}

    if test_idx.sum() >= 2 and len(np.unique(y[test_idx])) > 1:
        p_test = pipe.predict_proba(X[test_idx])[:, 1]
        metrics["test"] = _evaluate(y[test_idx], p_test)
    elif test_idx.sum() >= 1:
        p_test = pipe.predict_proba(X[test_idx])[:, 1]
        metrics["test"] = {
            "n": int(test_idx.sum()),
            "predictions": p_test.tolist(),
            "labels": y[test_idx].tolist(),
        }

    # Leave-one-out CV for small sample honest estimate
    if len(df) >= 5:
        loo_probs = []
        loo_true = []
        for i in range(len(df)):
            mask = np.ones(len(df), dtype=bool)
            mask[i] = False
            if len(np.unique(y[mask])) < 2:
                continue
            fold_pipe = Pipeline([("prep", preprocessor), ("clf", LogisticRegression(
                penalty="l2", C=1.0, max_iter=1000, class_weight="balanced",
                random_state=cfg["random_seed"],
            ))])
            fold_pipe.fit(X[mask], y[mask])
            loo_probs.append(fold_pipe.predict_proba(X.iloc[[i]])[0, 1])
            loo_true.append(y[i])
        if loo_probs and len(np.unique(loo_true)) > 1:
            metrics["loo_cv"] = _evaluate(np.array(loo_true), np.array(loo_probs))

    return TrainedModelBundle(
        name="logistic_preclinical",
        feature_set=feature_set,
        pipeline=pipe,
        feature_columns=feature_cols,
        categorical_columns=cat_cols,
        numeric_columns=num_cols,
        metrics=metrics,
    )


def resolve_baseline_clinical_cols() -> list[str]:
    return ["indication", "modality", "t0_year", "n_animal_studies"]


def save_model_bundle(bundle: TrainedModelBundle, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / f"{bundle.name}_{bundle.feature_set}.pkl"
    meta_path = out_dir / f"{bundle.name}_{bundle.feature_set}_metrics.json"

    with open(model_path, "wb") as f:
        pickle.dump(bundle, f)

    meta = {
        "name": bundle.name,
        "feature_set": bundle.feature_set,
        "feature_columns": bundle.feature_columns,
        "metrics": bundle.metrics,
        "version": bundle.version,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return model_path


def train_all_models(out_dir: Path | None = None) -> dict:
    out_dir = out_dir or project_root() / "data" / "processed" / "models"
    rates_path = project_root() / "data" / "external" / "wong2019_pos_rates.csv"

    programs, _ = build_feature_matrix(feature_set="all_preclinical")
    results: dict = {"models": {}}

    p_wong, wong_metrics = train_baseline_wong(programs, rates_path)
    results["baselines"] = {"wong_pos": wong_metrics}

    for feature_set in ["baseline_clinical", "all_preclinical", "baseline_plus_preclinical"]:
        try:
            bundle = train_logistic_model(programs_df=programs, feature_set=feature_set)
            path = save_model_bundle(bundle, out_dir)
            results["models"][feature_set] = {
                "path": str(path),
                "metrics": bundle.metrics,
            }
        except Exception as exc:
            results["models"][feature_set] = {"error": str(exc)}

    report_path = out_dir / "training_report.json"
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def main() -> None:
    results = train_all_models()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
