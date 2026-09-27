"""Enriched catalyst dataset for short-edge validation."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import project_root
from src.validation.point_in_time import sanitize_feature_family

CAR_WINDOW = "[-1,+1]"
CAR_BENCHMARK = "MARKET_MODEL"

EFFICACY_SAFETY_FAILURE = {"EFFICACY_FAILURE", "SAFETY_FAILURE"}


def load_short_edge_frame(
    db_path: Path | None = None,
    *,
    point_in_time_only: bool = True,
) -> pd.DataFrame:
    """One row per priced catalyst with exposure, market, trial, and outcome fields."""
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
            COALESCE(cut.entry_cutoff_date, c.trading_cutoff_date,
                     c.announcement_date) AS feature_cutoff_date,
            CAST(strftime('%Y', c.announcement_date) AS INTEGER) AS catalyst_year,
            ct.ticker_at_event AS ticker,
            es.car AS realized_car,
            ae.as_of_date AS exposure_as_of,
            ae.company_dependency,
            ae.is_lead_asset,
            ae.is_single_asset_company,
            ae.market_cap_usd,
            ae.data_source AS exposure_source,
            mf.as_of_date AS market_feature_as_of,
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
            mf.price_at_cutoff,
            mf.volume_ratio_20d AS volume_ratio_20d_mf,
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
            trial.api_fetched_at AS trial_source_observed_at,
            c.preclinical_evidence_found,
            c.n_preclinical_publications,
            pf.n_animal_studies,
            pf.median_effect_size
        FROM catalysts c
        JOIN programs p ON c.program_id = p.program_id
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        LEFT JOIN catalyst_trading_cutoffs cut ON c.catalyst_id = cut.catalyst_id
        LEFT JOIN clinical_trials trial ON c.nct_id = trial.nct_id
        JOIN catalyst_event_study es ON c.catalyst_id = es.catalyst_id
            AND es.window_label = '{CAR_WINDOW}' AND es.benchmark = '{CAR_BENCHMARK}'
        LEFT JOIN asset_exposure ae ON c.catalyst_id = ae.catalyst_id
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
    if point_in_time_only:
        df = sanitize_feature_family(
            df,
            MARKET_COLS,
            "market_feature_as_of",
            flag_col="market_features_point_in_time",
        )
        df = sanitize_feature_family(
            df,
            COMPANY_COLS,
            "exposure_as_of",
            flag_col="company_features_point_in_time",
        )
        df = sanitize_feature_family(
            df,
            CLINICAL_COLS,
            "trial_source_observed_at",
            flag_col="clinical_features_point_in_time",
        )
        safe_dates = pd.DataFrame(
            {
                "market": pd.to_datetime(df["market_feature_as_of"], errors="coerce").where(
                    df["market_features_point_in_time"]
                ),
                "company": pd.to_datetime(df["exposure_as_of"], errors="coerce").where(
                    df["company_features_point_in_time"]
                ),
                "clinical": pd.to_datetime(df["trial_source_observed_at"], errors="coerce").where(
                    df["clinical_features_point_in_time"]
                ),
            }
        )
        df["feature_as_of_date"] = safe_dates.max(axis=1)
        df["structured_features_point_in_time"] = (
            df["market_features_point_in_time"]
            & df["company_features_point_in_time"]
            & df["clinical_features_point_in_time"]
        )
    df["clinical_failure"] = (df["clinical_success"] == 0).astype(int)
    df["efficacy_safety_failure"] = df["outcome_category"].isin(EFFICACY_SAFETY_FAILURE).astype(int)
    df["major_negative_event"] = (df["realized_car"] <= -0.20).astype(int)
    df["catastrophic_drop"] = (df["realized_car"] <= -0.40).astype(int)
    df["company_dependency"] = df["company_dependency"].fillna(0.9)

    # Proxy size bucket from dependency heuristic
    df["is_small_cap"] = (df["company_dependency"] >= 0.85).astype(int)
    df["is_large_cap"] = (df["company_dependency"] <= 0.25).astype(int)
    df["high_momentum"] = (df["pre_catalyst_runup_60d"].fillna(0) > 0.15).astype(int)
    df["high_volatility"] = (
        df["realized_vol_20d"].fillna(0) > df["realized_vol_20d"].median()
    ).astype(int)
    df["high_dependency"] = (df["company_dependency"] >= 0.80).astype(int)
    df["phase_3"] = (df["phase_numeric"].fillna(0) >= 3).astype(int)
    df["phase_2"] = (
        (df["phase_numeric"].fillna(0) >= 2) & (df["phase_numeric"].fillna(0) < 3)
    ).astype(int)

    return df


MARKET_COLS = [
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

COMPANY_COLS = [
    "company_dependency",
    "is_lead_asset",
    "is_single_asset_company",
]

CLINICAL_COLS = [
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

PRECLINICAL_COLS = [
    "preclinical_evidence_found",
    "n_preclinical_publications",
    "n_animal_studies",
    "median_effect_size",
]

HUMAN_EVIDENCE_COLS = [
    "wong_pos_rate",
    "n_prior_same_drug",
    "prior_success_rate_same_drug",
    "log_enrollment",
]

FEATURE_SETS: dict[str, list[str]] = {
    "company_only": COMPANY_COLS,
    "market_only": MARKET_COLS,
    "clinical_only": CLINICAL_COLS,
    "preclinical_only": PRECLINICAL_COLS,
    "human_evidence_only": HUMAN_EVIDENCE_COLS,
    "market_plus_company": MARKET_COLS + COMPANY_COLS,
    "clinical_plus_market": CLINICAL_COLS + MARKET_COLS,
    "clinical_plus_human": CLINICAL_COLS + HUMAN_EVIDENCE_COLS,
    "everything": MARKET_COLS + COMPANY_COLS + CLINICAL_COLS + PRECLINICAL_COLS,
    "everything_no_preclinical": MARKET_COLS + COMPANY_COLS + CLINICAL_COLS,
}


def resolve_features(name: str) -> list[str]:
    return FEATURE_SETS.get(name, MARKET_COLS + COMPANY_COLS + CLINICAL_COLS).copy()


def shrinkage_mean(values: pd.Series, global_mean: float, k: float = 5.0) -> float:
    """James-Stein style shrinkage toward global mean for small samples."""
    n = values.notna().sum()
    if n == 0:
        return global_mean
    sample_mean = float(values.mean())
    weight = n / (n + k)
    return weight * sample_mean + (1 - weight) * global_mean
