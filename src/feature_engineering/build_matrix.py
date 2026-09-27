"""Build program-level feature matrix from animal study data."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_yaml, project_root


def _mean_or_nan(values: list) -> float | None:
    clean = [v for v in values if v is not None]
    return float(np.mean(clean)) if clean else None


def _binary_any(values: pd.Series) -> int:
    """Return whether any truthy numeric flag is present without object downcasting."""
    numeric = pd.to_numeric(values, errors="coerce")
    return int((numeric.fillna(0) > 0).any())


def build_study_level_frame(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT
            p.program_id,
            p.drug_name,
            p.indication,
            p.modality,
            c.ticker,
            CAST(strftime('%Y', t0.t0_date) AS INTEGER) AS t0_year,
            o.clinical_success,
            o.met_primary_endpoint,
            o.technical_failure,
            s.study_id,
            s.species,
            s.disease_model,
            s.is_humanized_model,
            s.is_pdx,
            f.effect_size,
            f.p_value,
            f.dose_response,
            f.survival_benefit,
            f.randomization_reported,
            f.blinding_reported,
            f.sample_size_calculation,
            f.exclusions_described,
            f.peer_reviewed,
            f.independent_lab_replication,
            f.replicated_across_models,
            f.replicated_across_species,
            f.face_validity,
            f.construct_validity,
            f.predictive_validity,
            f.endpoint_clinical_similarity,
            f.mechanism_similarity,
            f.pkpd_relevance,
            f.biomarker_overlap,
            f.human_target_validated
        FROM programs p
        JOIN companies c ON p.company_id = c.company_id
        JOIN program_t0 t0 ON p.program_id = t0.program_id
        JOIN trial_outcomes o ON p.program_id = o.program_id AND o.outcome_level = 'PHASE2'
        JOIN animal_studies s ON p.program_id = s.program_id
        JOIN animal_study_features f ON s.study_id = f.study_id
        WHERE s.verification_status = 'verified'
        """,
        conn,
    )


def aggregate_program_features(studies: pd.DataFrame) -> pd.DataFrame:
    """Aggregate verified study-level rows to one row per program."""
    if studies.empty:
        return pd.DataFrame()

    rows = []
    for program_id, grp in studies.groupby("program_id"):
        meta = grp.iloc[0]
        effect = grp["effect_size"].dropna()
        rows.append(
            {
                "program_id": program_id,
                "drug_name": meta["drug_name"],
                "indication": meta["indication"],
                "modality": meta["modality"],
                "ticker": meta["ticker"],
                "t0_year": meta["t0_year"],
                "clinical_success": int(meta["clinical_success"]),
                "indication_group": "oncology",
                # efficacy aggregates
                "best_effect_size": effect.max() if len(effect) else np.nan,
                "median_effect_size": effect.median() if len(effect) else np.nan,
                "min_p_value": grp["p_value"].min(skipna=True),
                "any_dose_response": _binary_any(grp["dose_response"]),
                "survival_benefit_any": _binary_any(grp["survival_benefit"]),
                # quality aggregates
                "pct_studies_randomized": grp["randomization_reported"].mean(skipna=True),
                "pct_studies_blinded": grp["blinding_reported"].mean(skipna=True),
                "pct_sample_size_calc": grp["sample_size_calculation"].mean(skipna=True),
                "pct_exclusions_described": grp["exclusions_described"].mean(skipna=True),
                "pct_peer_reviewed": grp["peer_reviewed"].mean(skipna=True),
                # translation aggregates
                "mean_face_validity": _mean_or_nan(grp["face_validity"].tolist()),
                "mean_construct_validity": _mean_or_nan(grp["construct_validity"].tolist()),
                "mean_predictive_validity": _mean_or_nan(grp["predictive_validity"].tolist()),
                "mean_endpoint_clinical_similarity": _mean_or_nan(
                    grp["endpoint_clinical_similarity"].tolist()
                ),
                "mean_mechanism_similarity": _mean_or_nan(grp["mechanism_similarity"].tolist()),
                "mean_pkpd_relevance": _mean_or_nan(grp["pkpd_relevance"].tolist()),
                "any_humanized_or_pdx": int(
                    _binary_any(grp["is_humanized_model"]) or _binary_any(grp["is_pdx"])
                ),
                "human_target_validated_any": _binary_any(grp["human_target_validated"]),
                "biomarker_overlap_any": _binary_any(grp["biomarker_overlap"]),
                # replication
                "any_independent_replication": _binary_any(grp["independent_lab_replication"]),
                "replicated_across_models_any": _binary_any(grp["replicated_across_models"]),
                "replicated_across_species_any": _binary_any(grp["replicated_across_species"]),
                "n_animal_studies": len(grp),
                "n_species": grp["species"].nunique(),
                "n_models": grp["disease_model"].nunique(),
            }
        )
    return pd.DataFrame(rows)


def resolve_feature_columns(feature_set: str, config_path: Path | None = None) -> list[str]:
    cfg = load_yaml(config_path or project_root() / "configs" / "feature_sets.yaml")
    sets = cfg["feature_sets"]

    def expand(name: str) -> list[str]:
        spec = sets[name]
        if "extends" in spec:
            cols: list[str] = []
            for ext in spec["extends"]:
                cols.extend(expand(ext))
            return cols
        return list(spec["columns"])

    return list(dict.fromkeys(expand(feature_set)))


def build_feature_matrix(
    db_path: Path | None = None,
    feature_set: str = "all_preclinical",
) -> tuple[pd.DataFrame, list[str]]:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    try:
        studies = build_study_level_frame(conn)
        programs = aggregate_program_features(studies)
    finally:
        conn.close()

    feature_cols = resolve_feature_columns(feature_set)
    for col in feature_cols:
        if col not in programs.columns:
            programs[col] = np.nan

    return programs, feature_cols


def assign_temporal_split(df: pd.DataFrame, modeling_cfg: dict | None = None) -> pd.Series:
    cfg = modeling_cfg or load_yaml(project_root() / "configs" / "modeling.yaml")
    ts = cfg["temporal_splits"]

    def _split(year: int) -> str:
        if year <= ts["train_t0_year_max"]:
            return "train"
        if ts["validation_t0_year_min"] <= year <= ts["validation_t0_year_max"]:
            return "validation"
        if year >= ts["test_t0_year_min"]:
            return "test"
        return "train"

    return df["t0_year"].apply(_split)
