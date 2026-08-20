"""Inference: predict clinical success from animal features."""

from __future__ import annotations

import pickle
import sqlite3
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import project_root
from src.feature_engineering.build_matrix import aggregate_program_features, build_study_level_frame
from src.models.train import TrainedModelBundle, resolve_baseline_clinical_cols


def load_model(model_path: Path | None = None) -> TrainedModelBundle:
    if model_path is None:
        model_path = (
            project_root()
            / "data"
            / "processed"
            / "models"
            / "logistic_preclinical_all_preclinical.pkl"
        )
    with open(model_path, "rb") as f:
        bundle = pickle.load(f)
    return bundle


def features_for_program(program_id: str, db_path: Path | None = None) -> pd.DataFrame:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    try:
        studies = build_study_level_frame(conn)
        programs = aggregate_program_features(studies)
    finally:
        conn.close()
    row = programs[programs["program_id"] == program_id]
    if row.empty:
        raise ValueError(f"Program {program_id} not found or has no verified animal studies")
    return row


def predict_program(
    program_id: str,
    model_path: Path | None = None,
    save_to_db: bool = True,
) -> dict:
    bundle = load_model(model_path)
    row = features_for_program(program_id)

    for col in bundle.feature_columns:
        if col not in row.columns:
            row[col] = np.nan

    X = row[bundle.feature_columns].copy()
    X = X.apply(pd.to_numeric, errors="ignore")
    p_success = float(bundle.pipeline.predict_proba(X)[0, 1])

    result = {
        "program_id": program_id,
        "drug_name": row.iloc[0]["drug_name"],
        "p_model": p_success,
        "model_name": bundle.name,
        "feature_set": bundle.feature_set,
        "actual_clinical_success": int(row.iloc[0]["clinical_success"]),
    }

    if save_to_db:
        db_path = project_root() / "data" / "processed" / "research.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            INSERT INTO model_predictions (
                prediction_id, program_id, model_name, model_version, p_model, feature_set
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                program_id,
                bundle.name,
                bundle.version,
                p_success,
                bundle.feature_set,
            ),
        )
        conn.commit()
        conn.close()

    return result


def predict_all(model_path: Path | None = None) -> pd.DataFrame:
    bundle = load_model(model_path)
    db_path = project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    studies = build_study_level_frame(conn)
    conn.close()
    programs = aggregate_program_features(studies)

    for col in bundle.feature_columns:
        if col not in programs.columns:
            programs[col] = np.nan

    X = programs[bundle.feature_columns].copy()
    for col in X.columns:
        if X[col].dtype == object:
            X[col] = X[col].astype(str).replace("nan", np.nan)
    X = X.apply(pd.to_numeric, errors="ignore")

    programs["p_model"] = bundle.pipeline.predict_proba(X)[:, 1]
    return programs[
        ["program_id", "drug_name", "indication", "clinical_success", "p_model", "n_animal_studies"]
    ]


def main() -> None:
    df = predict_all()
    out = project_root() / "data" / "processed" / "predictions.csv"
    df.to_csv(out, index=False)
    print(df.to_string(index=False))
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
