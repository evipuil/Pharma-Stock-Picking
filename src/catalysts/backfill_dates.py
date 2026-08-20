"""Backfill catalyst announcement dates from trial outcomes / t0 (inferred, low confidence)."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from src.config import project_root
from src.event_study.windows import infer_trading_cutoff


def backfill_announcement_dates(db_path: Path | None = None) -> dict:
    """
    For catalysts missing announcement_date, infer from:
    1. CT.gov results_first_posted_date (preferred for completed trials)
    2. trial_outcomes.outcome_date
    3. program_t0.t0_date + 540 days (~18mo typical Phase II readout proxy)

    Marks announcement_source as INFERRED_* and timing UNKNOWN.
    """
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    stats = {"from_ctgov_results": 0, "from_outcome": 0, "from_t0_proxy": 0, "upgraded": 0, "cutoffs_updated": 0}

    # Pass 1: fill missing dates
    rows = conn.execute(
        """
        SELECT c.catalyst_id, c.program_id, c.announcement_date,
               o.outcome_date, t0.t0_date, ct.results_first_posted_date
        FROM catalysts c
        LEFT JOIN trial_outcomes o
            ON c.program_id = o.program_id AND o.outcome_level = 'PHASE2'
        LEFT JOIN program_t0 t0 ON c.program_id = t0.program_id
        LEFT JOIN clinical_trials ct ON c.nct_id = ct.nct_id
        WHERE c.announcement_date IS NULL
        """
    ).fetchall()

    for catalyst_id, _program_id, _ann, outcome_date, t0_date, results_posted in rows:
        inferred, source = _infer_date(outcome_date, t0_date, results_posted)
        if not inferred:
            continue
        if source == "INFERRED_CTGOV_RESULTS":
            stats["from_ctgov_results"] += 1
        elif source == "INFERRED_OUTCOME_DATE":
            stats["from_outcome"] += 1
        else:
            stats["from_t0_proxy"] += 1
        _apply_date(conn, catalyst_id, inferred, source, stats)

    # Pass 2: upgrade weak t0-proxy dates when CT.gov results date available
    upgrade_rows = conn.execute(
        """
        SELECT c.catalyst_id, ct.results_first_posted_date
        FROM catalysts c
        JOIN clinical_trials ct ON c.nct_id = ct.nct_id
        WHERE c.announcement_source = 'INFERRED_T0_PLUS_18MO'
          AND ct.results_first_posted_date IS NOT NULL
        """
    ).fetchall()
    for catalyst_id, results_posted in upgrade_rows:
        inferred = date.fromisoformat(str(results_posted)[:10])
        _apply_date(conn, catalyst_id, inferred, "INFERRED_CTGOV_RESULTS", stats)
        stats["upgraded"] += 1

    # Pass 3: tag catalysts with dates but missing source (legacy rows)
    conn.execute(
        """
        UPDATE catalysts
        SET announcement_source = 'LEGACY_UNTAGGED'
        WHERE announcement_date IS NOT NULL AND announcement_source IS NULL
        """
    )
    stats["legacy_tagged"] = conn.execute(
        "SELECT changes()"
    ).fetchone()[0]

    conn.commit()
    conn.close()
    return stats


def _infer_date(
    outcome_date,
    t0_date,
    results_posted,
) -> tuple[date | None, str | None]:
    if results_posted:
        return date.fromisoformat(str(results_posted)[:10]), "INFERRED_CTGOV_RESULTS"
    if outcome_date:
        return date.fromisoformat(str(outcome_date)[:10]), "INFERRED_OUTCOME_DATE"
    if t0_date:
        from datetime import timedelta

        t0d = date.fromisoformat(str(t0_date)[:10])
        return t0d + timedelta(days=540), "INFERRED_T0_PLUS_18MO"
    return None, None


def _apply_date(conn, catalyst_id: str, inferred: date, source: str, stats: dict) -> None:
    cutoff, day_before, day_after, _conf = infer_trading_cutoff(inferred, "UNKNOWN")
    conn.execute(
        """
        UPDATE catalysts SET
            announcement_date = ?,
            announcement_timing = 'UNKNOWN',
            announcement_source = ?,
            trading_cutoff_date = ?,
            trading_day_before = ?,
            first_trading_day_after = ?,
            updated_at = datetime('now')
        WHERE catalyst_id = ?
        """,
        (
            str(inferred)[:10],
            source,
            str(cutoff)[:10],
            str(day_before)[:10],
            str(day_after)[:10],
            catalyst_id,
        ),
    )
    conn.execute(
        """
        INSERT INTO catalyst_trading_cutoffs (catalyst_id, entry_cutoff_date, cutoff_rationale, execution_confidence)
        VALUES (?, ?, ?, 'LOW')
        ON CONFLICT(catalyst_id) DO UPDATE SET
            entry_cutoff_date = excluded.entry_cutoff_date,
            cutoff_rationale = excluded.cutoff_rationale,
            execution_confidence = 'LOW'
        """,
        (catalyst_id, str(cutoff)[:10], source),
    )
    stats["cutoffs_updated"] += 1
