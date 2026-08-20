"""Automated look-ahead bias / leakage checks."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


@dataclass
class LeakageCheckResult:
    program_id: str
    check_type: str
    passed: bool
    violation_detail: str | None = None


def effective_public_date(
    publication_date: date | None,
    online_first_date: date | None,
) -> date | None:
    """Return earliest public disclosure date for a source record."""
    candidates = [d for d in (publication_date, online_first_date) if d is not None]
    return min(candidates) if candidates else None


def check_publication_after_t0(
    conn: sqlite3.Connection,
    program_id: str,
) -> LeakageCheckResult:
    """Ensure all linked animal-study publications have effective_public_date <= t0."""
    rows = conn.execute(
        """
        SELECT s.study_id, sr.publication_date, sr.online_first_date, t0.t0_date
        FROM animal_studies s
        JOIN publications p ON s.publication_id = p.publication_id
        JOIN source_records sr ON p.source_record_id = sr.source_record_id
        JOIN program_t0 t0 ON s.program_id = t0.program_id
        WHERE s.program_id = ? AND s.verification_status = 'verified'
        """,
        (program_id,),
    ).fetchall()

    for study_id, pub_date, online_date, t0_date in rows:
        eff = effective_public_date(
            _parse_date(pub_date),
            _parse_date(online_date),
        )
        t0 = _parse_date(t0_date)
        if eff is None:
            return LeakageCheckResult(
                program_id=program_id,
                check_type="publication_after_t0",
                passed=False,
                violation_detail=f"study {study_id}: missing publication date",
            )
        if t0 and eff > t0:
            return LeakageCheckResult(
                program_id=program_id,
                check_type="publication_after_t0",
                passed=False,
                violation_detail=f"study {study_id}: effective date {eff} > t0 {t0}",
            )

    return LeakageCheckResult(
        program_id=program_id,
        check_type="publication_after_t0",
        passed=True,
    )


def check_t0_defined(conn: sqlite3.Connection, program_id: str) -> LeakageCheckResult:
    row = conn.execute(
        "SELECT t0_date FROM program_t0 WHERE program_id = ?",
        (program_id,),
    ).fetchone()
    if not row or row[0] is None:
        return LeakageCheckResult(
            program_id=program_id,
            check_type="t0_defined",
            passed=False,
            violation_detail="t0_date not set",
        )
    return LeakageCheckResult(program_id=program_id, check_type="t0_defined", passed=True)


def check_temporal_split(
    conn: sqlite3.Connection,
    program_id: str,
    split: str,
    train_max_year: int,
    test_min_year: int,
) -> LeakageCheckResult:
    row = conn.execute(
        """
        SELECT CAST(strftime('%Y', t0_date) AS INTEGER)
        FROM program_t0 WHERE program_id = ?
        """,
        (program_id,),
    ).fetchone()
    if not row or row[0] is None:
        return LeakageCheckResult(
            program_id=program_id,
            check_type="temporal_split_integrity",
            passed=False,
            violation_detail="missing t0 year",
        )
    year = row[0]
    if split == "train" and year > train_max_year:
        return LeakageCheckResult(
            program_id=program_id,
            check_type="temporal_split_integrity",
            passed=False,
            violation_detail=f"train split but t0 year {year} > {train_max_year}",
        )
    if split == "test" and year < test_min_year:
        return LeakageCheckResult(
            program_id=program_id,
            check_type="temporal_split_integrity",
            passed=False,
            violation_detail=f"test split but t0 year {year} < {test_min_year}",
        )
    return LeakageCheckResult(
        program_id=program_id,
        check_type="temporal_split_integrity",
        passed=True,
    )


ALL_CHECKS = [
    check_t0_defined,
    check_publication_after_t0,
]


def run_leakage_audit(
    db_path: Path,
    program_ids: Iterable[str] | None = None,
) -> list[LeakageCheckResult]:
    conn = sqlite3.connect(db_path)
    try:
        if program_ids is None:
            rows = conn.execute("SELECT program_id FROM programs").fetchall()
            program_ids = [r[0] for r in rows]

        results: list[LeakageCheckResult] = []
        for program_id in program_ids:
            for check_fn in ALL_CHECKS:
                result = check_fn(conn, program_id)
                results.append(result)
                _log_audit(conn, result)
        conn.commit()
        return results
    finally:
        conn.close()


def _log_audit(conn: sqlite3.Connection, result: LeakageCheckResult) -> None:
    conn.execute(
        """
        INSERT INTO leakage_audit_log (audit_id, program_id, check_type, passed, violation_detail)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            result.program_id,
            result.check_type,
            1 if result.passed else 0,
            result.violation_detail,
        ),
    )


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value[:10])
