"""Exploratory analysis and baseline models for MVP cohort."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.preprocessing import LabelEncoder

from src.config import project_root
from src.models.baselines import load_benchmark_rates, lookup_pos_rate


def load_program_table(db_path: Path) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        """
        SELECT
            p.program_id,
            p.drug_name,
            p.indication,
            p.modality,
            c.ticker,
            t0.t0_date,
            o.clinical_success,
            o.met_primary_endpoint,
            pf.n_animal_studies,
            pf.pct_studies_randomized,
            ct.phase,
            ct.enrollment
        FROM programs p
        JOIN companies c ON p.company_id = c.company_id
        JOIN program_t0 t0 ON p.program_id = t0.program_id
        LEFT JOIN trial_outcomes o ON p.program_id = o.program_id AND o.outcome_level = 'PHASE2'
        LEFT JOIN program_preclinical_features pf ON p.program_id = pf.program_id
        LEFT JOIN clinical_trials ct ON p.primary_nct_id = ct.nct_id
        """,
        conn,
    )
    conn.close()
    return df


def run_exploratory(db_path: Path | None = None) -> dict:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    df = load_program_table(db_path)

    if df.empty:
        return {"error": "no programs in database"}

    rates_path = project_root() / "data" / "external" / "wong2019_pos_rates.csv"
    rates = load_benchmark_rates(rates_path)

    y = df["clinical_success"].astype(float)
    n = len(df)
    n_events = int(y.sum())

    # Baseline B1: marginal rate
    p_marginal = y.mean()
    brier_marginal = brier_score_loss(y, np.full(n, p_marginal))

    # Baseline B2: Wong lookup
    p_wong = []
    for _, row in df.iterrows():
        p = lookup_pos_rate(rates, "PHASE2", "oncology", row.get("modality"))
        p_wong.append(p if p is not None else p_marginal)
    brier_wong = brier_score_loss(y, p_wong)

    # Logistic on available features (MVP — mostly structural)
    features = df[["modality", "indication", "n_animal_studies", "enrollment"]].copy()
    features["n_animal_studies"] = features["n_animal_studies"].fillna(0)
    features["enrollment"] = features["enrollment"].fillna(features["enrollment"].median())

    le_mod = LabelEncoder()
    le_ind = LabelEncoder()
    X = pd.DataFrame({
        "modality_enc": le_mod.fit_transform(features["modality"].astype(str)),
        "indication_enc": le_ind.fit_transform(features["indication"].astype(str)),
        "n_animal_studies": features["n_animal_studies"],
        "log_enrollment": np.log1p(features["enrollment"]),
    })

    results = {
        "n_programs": n,
        "n_success": n_events,
        "success_rate": float(p_marginal),
        "brier_marginal": float(brier_marginal),
        "brier_wong_baseline": float(brier_wong),
        "mean_pre_t0_publications": float(df["n_animal_studies"].mean()),
    }

    if n >= 4 and n_events >= 2 and (n - n_events) >= 2:
        lr = LogisticRegression(max_iter=1000, C=1.0)
        lr.fit(X, y)
        p_lr = lr.predict_proba(X)[:, 1]
        results["brier_logistic"] = float(brier_score_loss(y, p_lr))
        try:
            results["roc_auc_logistic"] = float(roc_auc_score(y, p_lr))
        except ValueError:
            results["roc_auc_logistic"] = None
        results["logistic_coefficients"] = dict(zip(X.columns, lr.coef_[0].tolist()))
    else:
        results["note"] = "Too few programs for stable logistic fit; descriptive only"

    # Save report
    out_dir = project_root() / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "exploratory_report.json"
    import json
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    df.to_csv(out_dir / "programs_analysis.csv", index=False)

    return results


def main() -> None:
    results = run_exploratory()
    print("Exploratory analysis results:")
    for k, v in results.items():
        print(f"  {k}: {v}")
