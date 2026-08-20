"""Migrate existing programs → catalyst-level observations."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import date
from pathlib import Path

from src.config import project_root
from src.event_study.windows import infer_trading_cutoff


def apply_catalyst_schema(db_path: Path | None = None) -> None:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    schema = project_root() / "sql" / "schema_catalysts.sql"
    conn = sqlite3.connect(db_path)
    conn.executescript(schema.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()


def _outcome_category(row: tuple) -> str:
    success, tech, safety, unknown = row
    if unknown:
        return "UNKNOWN"
    if success:
        return "SUCCESS"
    if safety:
        return "SAFETY_FAILURE"
    if tech:
        return "EFFICACY_FAILURE"
    return "MIXED"


def migrate_programs_to_catalysts(db_path: Path | None = None) -> dict:
    """Create one catalyst per program from existing DB rows."""
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    apply_catalyst_schema(db_path)
    conn = sqlite3.connect(db_path)
    stats = {"created": 0, "skipped": 0, "linked_events": 0}

    programs = conn.execute(
        """
        SELECT p.program_id, p.company_id, p.drug_name, p.indication, p.primary_nct_id,
               p.modality, c.ticker, t0.t0_date,
               o.clinical_success, o.met_primary_endpoint, o.technical_failure,
               o.safety_failure, o.outcome_unknown, o.outcome_date, o.notes,
               ct.phase, ct.enrollment, ct.brief_title,
               COALESCE(pf.n_animal_studies, 0) AS n_preclin
        FROM programs p
        JOIN companies c ON p.company_id = c.company_id
        JOIN program_t0 t0 ON p.program_id = t0.program_id
        JOIN trial_outcomes o ON p.program_id = o.program_id AND o.outcome_level = 'PHASE2'
        LEFT JOIN clinical_trials ct ON p.primary_nct_id = ct.nct_id
        LEFT JOIN program_preclinical_features pf ON p.program_id = pf.program_id
        """
    ).fetchall()

    for row in programs:
        (
            program_id, company_id, drug, indication, nct_id, _modality, ticker, t0_date,
            clinical_success, met_pe, tech_fail, safety_fail, outcome_unknown,
            outcome_date, outcome_notes, phase, enrollment, _title, n_preclin,
        ) = row

        existing = conn.execute(
            "SELECT catalyst_id FROM catalysts WHERE program_id = ?", (program_id,)
        ).fetchone()
        if existing:
            stats["skipped"] += 1
            continue

        catalyst_id = f"CAT-{program_id}"
        fin = conn.execute(
            """
            SELECT event_type, event_date, outcome_direction
            FROM program_financial_events WHERE program_id = ?
            ORDER BY event_date LIMIT 1
            """,
            (program_id,),
        ).fetchone()

        if fin:
            event_type, event_date, _direction = fin
            ann_date = event_date
            stats["linked_events"] += 1
        else:
            event_type = "PHASE2_READOUT"
            ann_date = outcome_date or t0_date

        ann = date.fromisoformat(str(ann_date)[:10]) if ann_date else None
        cutoff, day_before, day_after, conf = (
            infer_trading_cutoff(ann, "UNKNOWN") if ann else (None, None, None, "LOW")
        )

        cat = _outcome_category((clinical_success, tech_fail, safety_fail, outcome_unknown))
        preclin_found = 1 if n_preclin and n_preclin > 0 else 0

        conn.execute(
            """
            INSERT INTO catalysts (
                catalyst_id, program_id, company_id, drug_name, indication, nct_id,
                trial_phase, catalyst_type, enrollment, announcement_date,
                trading_cutoff_date, trading_day_before, first_trading_day_after,
                clinical_success, outcome_category, met_primary_endpoint,
                preclinical_evidence_found, n_preclinical_publications,
                publication_coverage_confidence, outcome_notes, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                catalyst_id,
                program_id,
                company_id,
                drug,
                indication,
                nct_id,
                phase,
                event_type or "PHASE2_READOUT",
                enrollment,
                str(ann)[:10] if ann else None,
                str(cutoff)[:10] if cutoff else None,
                str(day_before)[:10] if day_before else None,
                str(day_after)[:10] if day_after else None,
                clinical_success,
                cat,
                met_pe,
                preclin_found,
                n_preclin or 0,
                1.0 if preclin_found else 0.0,
                outcome_notes,
                "migrate_programs_v1",
            ),
        )
        conn.execute(
            """
            INSERT INTO catalyst_ticker_history (
                map_id, catalyst_id, ticker_at_event, ticker_current, map_source
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), catalyst_id, ticker, ticker, "companies_table"),
        )
        if cutoff:
            conn.execute(
                """
                INSERT INTO catalyst_trading_cutoffs (
                    catalyst_id, entry_cutoff_date, cutoff_rationale, execution_confidence
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    catalyst_id,
                    str(cutoff)[:10],
                    "migrated_from_program; announcement_timing UNKNOWN",
                    conf,
                ),
            )
        stats["created"] += 1

    conn.commit()
    conn.close()
    return stats


def export_catalysts_csv(out_path: Path | None = None) -> Path:
    import pandas as pd

    db_path = project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        """
        SELECT c.*, ct.ticker_at_event, tc.entry_cutoff_date
        FROM catalysts c
        LEFT JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        LEFT JOIN catalyst_trading_cutoffs tc ON c.catalyst_id = tc.catalyst_id
        ORDER BY c.announcement_date
        """,
        conn,
    )
    conn.close()
    out_path = out_path or project_root() / "data" / "catalysts.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path
