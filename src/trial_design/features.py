"""Catalyst-level trial design features for indication-level P(success)."""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path

import pandas as pd

from src.clinical_trials.parse_study import parse_study
from src.config import project_root
from src.models.baselines import load_benchmark_rates, lookup_pos_rate
from src.trial_design.endpoint_classifier import classify_endpoint


PHASE_NUMERIC = {
    "PHASE1": 1.0,
    "PHASE2": 2.0,
    "PHASE3": 3.0,
    "PHASE4": 4.0,
    "PHASE1/PHASE2": 1.5,
    "PHASE2/PHASE3": 2.5,
    "EARLY_PHASE1": 0.5,
}


def _apply_schema(conn: sqlite3.Connection) -> None:
    schema = project_root() / "sql" / "schema_trial_features.sql"
    conn.executescript(schema.read_text(encoding="utf-8"))


def _phase_numeric(phase: str | None) -> float:
    if not phase:
        return 2.0
    return PHASE_NUMERIC.get(phase.upper(), 2.0)


def _load_primary_outcomes(nct_id: str, raw_json_path: str | None) -> list[str]:
    paths: list[Path] = []
    if raw_json_path:
        paths.append(Path(raw_json_path))
    paths.append(project_root() / "data" / "raw" / "ctgov" / f"{nct_id}.json")

    for path in paths:
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            parsed = parse_study(raw)
            return parsed.get("primary_outcomes") or []
    return []


def _is_combination(intervention_json: str | None) -> int:
    if not intervention_json:
        return 0
    try:
        interventions = json.loads(intervention_json)
    except json.JSONDecodeError:
        return 0
    if isinstance(interventions, list) and len(interventions) > 1:
        return 1
    text = " ".join(str(i) for i in interventions).lower()
    combo_markers = (" plus ", " + ", " in combination", "combined with", " and ")
    return int(any(m in text for m in combo_markers))


def _prior_same_drug_stats(
    conn: sqlite3.Connection,
    drug_name: str,
    announcement_date: str | None,
) -> tuple[int, float | None]:
    if not announcement_date:
        return 0, None
    rows = conn.execute(
        """
        SELECT clinical_success
        FROM catalysts
        WHERE drug_name = ?
          AND announcement_date < ?
          AND clinical_success IS NOT NULL
        ORDER BY announcement_date
        """,
        (drug_name, announcement_date),
    ).fetchall()
    if not rows:
        return 0, None
    successes = [r[0] for r in rows]
    return len(rows), float(sum(successes) / len(successes))


def compute_trial_features_for_catalyst(
    conn: sqlite3.Connection,
    catalyst_id: str,
    nct_id: str,
    drug_name: str,
    modality: str | None,
    announcement_date: str | None,
) -> dict | None:
    trial = conn.execute(
        """
        SELECT ct.phase, ct.enrollment, ct.allocation, ct.masking, ct.intervention,
               ct.start_date, ct.first_posted_date, ct.raw_json_path
        FROM clinical_trials ct
        WHERE ct.nct_id = ?
        """,
        (nct_id,),
    ).fetchone()
    if not trial:
        return None

    phase, enrollment, allocation, masking, intervention, start_date, first_posted, raw_path = trial
    outcomes = _load_primary_outcomes(nct_id, raw_path)
    endpoint_flags = classify_endpoint(outcomes)

    rates = load_benchmark_rates(project_root() / "data" / "external" / "wong2019_pos_rates.csv")
    phase_for_wong = (phase or "PHASE2").replace("PHASE1/PHASE2", "PHASE2")
    wong_rate = lookup_pos_rate(rates, phase_for_wong, "oncology", modality)

    n_prior, prior_rate = _prior_same_drug_stats(conn, drug_name, announcement_date)
    enroll_val = int(enrollment) if enrollment else None
    log_enroll = math.log1p(enroll_val) if enroll_val and enroll_val > 0 else None

    alloc = (allocation or "").upper()
    mask = (masking or "").upper()

    return {
        "catalyst_id": catalyst_id,
        "nct_id": nct_id,
        "phase": phase,
        "phase_numeric": _phase_numeric(phase),
        "enrollment": enroll_val,
        "log_enrollment": log_enroll,
        "is_randomized": int(alloc == "RANDOMIZED"),
        "is_blinded": int(mask not in ("", "NONE", "NA", "OPEN LABEL")),
        "is_combination": _is_combination(intervention),
        "wong_pos_rate": wong_rate,
        "n_prior_same_drug": n_prior,
        "prior_success_rate_same_drug": prior_rate,
        "trial_start_date": start_date,
        "first_posted_date": first_posted,
        **endpoint_flags,
    }


def compute_all_trial_features(db_path: Path | None = None) -> dict:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    _apply_schema(conn)

    rows = conn.execute(
        """
        SELECT c.catalyst_id, c.nct_id, c.drug_name, c.announcement_date, p.modality
        FROM catalysts c
        JOIN programs p ON c.program_id = p.program_id
        WHERE c.nct_id IS NOT NULL
        """
    ).fetchall()

    stats = {"computed": 0, "skipped": 0}
    for catalyst_id, nct_id, drug_name, ann_date, modality in rows:
        features = compute_trial_features_for_catalyst(
            conn, catalyst_id, nct_id, drug_name, modality, ann_date
        )
        if not features:
            stats["skipped"] += 1
            continue

        conn.execute(
            """
            INSERT INTO catalyst_trial_features (
                catalyst_id, nct_id, phase, phase_numeric, enrollment, log_enrollment,
                is_randomized, is_blinded, is_combination,
                endpoint_os, endpoint_pfs, endpoint_orr, endpoint_safety,
                wong_pos_rate, n_prior_same_drug, prior_success_rate_same_drug,
                trial_start_date, first_posted_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(catalyst_id) DO UPDATE SET
                nct_id = excluded.nct_id,
                phase = excluded.phase,
                phase_numeric = excluded.phase_numeric,
                enrollment = excluded.enrollment,
                log_enrollment = excluded.log_enrollment,
                is_randomized = excluded.is_randomized,
                is_blinded = excluded.is_blinded,
                is_combination = excluded.is_combination,
                endpoint_os = excluded.endpoint_os,
                endpoint_pfs = excluded.endpoint_pfs,
                endpoint_orr = excluded.endpoint_orr,
                endpoint_safety = excluded.endpoint_safety,
                wong_pos_rate = excluded.wong_pos_rate,
                n_prior_same_drug = excluded.n_prior_same_drug,
                prior_success_rate_same_drug = excluded.prior_success_rate_same_drug,
                trial_start_date = excluded.trial_start_date,
                first_posted_date = excluded.first_posted_date
            """,
            (
                features["catalyst_id"],
                features["nct_id"],
                features["phase"],
                features["phase_numeric"],
                features["enrollment"],
                features["log_enrollment"],
                features["is_randomized"],
                features["is_blinded"],
                features["is_combination"],
                features["endpoint_os"],
                features["endpoint_pfs"],
                features["endpoint_orr"],
                features["endpoint_safety"],
                features["wong_pos_rate"],
                features["n_prior_same_drug"],
                features["prior_success_rate_same_drug"],
                features["trial_start_date"],
                features["first_posted_date"],
            ),
        )

        # Backfill sparse catalyst columns from CT.gov
        conn.execute(
            """
            UPDATE catalysts
            SET trial_phase = COALESCE(trial_phase, ?),
                enrollment = COALESCE(enrollment, ?)
            WHERE catalyst_id = ?
            """,
            (features["phase"], features["enrollment"], catalyst_id),
        )
        stats["computed"] += 1

    conn.commit()
    conn.close()
    return stats


def export_trial_features_csv(db_path: Path | None = None) -> Path:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM catalyst_trial_features", conn)
    conn.close()
    path = project_root() / "data" / "processed" / "catalyst_trial_features.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
