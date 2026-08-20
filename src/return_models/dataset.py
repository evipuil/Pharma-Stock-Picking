"""Build catalyst-level modeling dataset from DB."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import project_root

CAR_WINDOW = "[-1,+1]"
CAR_BENCHMARK = "MARKET_MODEL"


def load_catalyst_modeling_frame(db_path: Path | None = None) -> pd.DataFrame:
    """One row per catalyst with realized CAR, market features, and labels."""
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        f"""
        SELECT
            c.catalyst_id,
            c.program_id,
            c.drug_name,
            c.indication,
            p.modality,
            c.clinical_success,
            c.outcome_category,
            c.announcement_date,
            CAST(strftime('%Y', c.announcement_date) AS INTEGER) AS catalyst_year,
            ct.ticker_at_event AS ticker,
            es.car AS realized_car,
            mf.return_1d,
            mf.return_5d,
            mf.return_20d,
            mf.return_60d,
            mf.return_120d,
            mf.abnormal_return_20d_xbi,
            mf.abnormal_return_60d_xbi,
            mf.distance_from_52w_high,
            mf.realized_vol_20d,
            mf.volume_ratio_20d,
            mf.pre_catalyst_runup_60d,
            tf.phase_numeric,
            tf.log_enrollment,
            tf.is_randomized,
            tf.is_blinded,
            tf.is_combination,
            tf.endpoint_os,
            tf.endpoint_pfs,
            tf.endpoint_orr,
            tf.wong_pos_rate,
            tf.n_prior_same_drug,
            tf.prior_success_rate_same_drug,
            c.preclinical_evidence_found,
            c.n_preclinical_publications,
            pf.n_animal_studies,
            pf.median_effect_size
        FROM catalysts c
        JOIN programs p ON c.program_id = p.program_id
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        JOIN catalyst_event_study es ON c.catalyst_id = es.catalyst_id
            AND es.window_label = '{CAR_WINDOW}' AND es.benchmark = '{CAR_BENCHMARK}'
        LEFT JOIN catalyst_market_features mf ON c.catalyst_id = mf.catalyst_id
        LEFT JOIN catalyst_trial_features tf ON c.catalyst_id = tf.catalyst_id
        LEFT JOIN program_preclinical_features pf ON c.program_id = pf.program_id
        WHERE c.clinical_success IS NOT NULL
          AND es.car IS NOT NULL
        """,
        conn,
    )
    conn.close()
    df["announcement_date"] = pd.to_datetime(df["announcement_date"], errors="coerce")
    return df


MARKET_FEATURE_COLS = [
    "return_1d",
    "return_5d",
    "return_20d",
    "return_60d",
    "return_120d",
    "abnormal_return_20d_xbi",
    "abnormal_return_60d_xbi",
    "distance_from_52w_high",
    "realized_vol_20d",
    "volume_ratio_20d",
    "pre_catalyst_runup_60d",
]

PRECLINICAL_COLS = [
    "preclinical_evidence_found",
    "n_preclinical_publications",
    "n_animal_studies",
    "median_effect_size",
]

TRIAL_DESIGN_COLS = [
    "phase_numeric",
    "log_enrollment",
    "is_randomized",
    "is_blinded",
    "is_combination",
    "endpoint_os",
    "endpoint_pfs",
    "endpoint_orr",
    "wong_pos_rate",
    "n_prior_same_drug",
    "prior_success_rate_same_drug",
]


def resolve_feature_cols(feature_set: str) -> list[str]:
    """Map feature set name to column list for expected CAR models."""
    if feature_set == "market_only":
        return MARKET_FEATURE_COLS.copy()
    if feature_set == "market_plus_trial":
        return MARKET_FEATURE_COLS + TRIAL_DESIGN_COLS
    if feature_set == "market_plus_preclinical":
        return MARKET_FEATURE_COLS + PRECLINICAL_COLS
    if feature_set == "market_plus_trial_plus_preclinical":
        return MARKET_FEATURE_COLS + TRIAL_DESIGN_COLS + PRECLINICAL_COLS
    if feature_set == "trial_only":
        return TRIAL_DESIGN_COLS.copy()
    return MARKET_FEATURE_COLS.copy()


def resolve_split_feature_cols(feature_set: str) -> tuple[list[str], list[str]]:
    """
    Return (p_success_features, car_features).

    Trial design informs P(success); market momentum informs conditional CAR.
    """
    car_cols = MARKET_FEATURE_COLS.copy()
    if feature_set == "market_only":
        cols = MARKET_FEATURE_COLS.copy()
        return cols, cols
    if feature_set == "trial_only":
        return TRIAL_DESIGN_COLS.copy(), car_cols
    if feature_set in ("market_plus_trial", "split_trial_market"):
        return MARKET_FEATURE_COLS + TRIAL_DESIGN_COLS, car_cols
    if feature_set == "market_plus_preclinical":
        return MARKET_FEATURE_COLS + PRECLINICAL_COLS, car_cols
    if feature_set == "market_plus_trial_plus_preclinical":
        return MARKET_FEATURE_COLS + TRIAL_DESIGN_COLS + PRECLINICAL_COLS, car_cols
    cols = resolve_feature_cols(feature_set)
    return cols, car_cols
