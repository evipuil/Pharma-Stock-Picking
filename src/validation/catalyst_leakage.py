"""Leakage checks for catalyst-level market features."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.config import project_root


@dataclass
class CatalystLeakageResult:
    catalyst_id: str
    check_type: str
    passed: bool
    detail: str | None = None


def check_market_features_before_cutoff(conn: sqlite3.Connection, catalyst_id: str) -> CatalystLeakageResult:
    row = conn.execute(
        """
        SELECT mf.as_of_date, tc.entry_cutoff_date, c.announcement_date
        FROM catalyst_market_features mf
        JOIN catalysts c ON mf.catalyst_id = c.catalyst_id
        LEFT JOIN catalyst_trading_cutoffs tc ON c.catalyst_id = tc.catalyst_id
        WHERE mf.catalyst_id = ?
        """,
        (catalyst_id,),
    ).fetchone()
    if not row:
        return CatalystLeakageResult(catalyst_id, "market_features_exist", False, "no features")

    as_of, entry_cutoff, ann = row
    cutoff = entry_cutoff or ann
    if not cutoff:
        return CatalystLeakageResult(catalyst_id, "cutoff_defined", False, "no cutoff")

    as_of_d = date.fromisoformat(str(as_of)[:10])
    cutoff_d = date.fromisoformat(str(cutoff)[:10])
    if as_of_d > cutoff_d:
        return CatalystLeakageResult(
            catalyst_id,
            "market_features_before_cutoff",
            False,
            f"as_of {as_of_d} > cutoff {cutoff_d}",
        )
    return CatalystLeakageResult(catalyst_id, "market_features_before_cutoff", True)


def run_catalyst_leakage_audit(db_path: Path | None = None) -> list[CatalystLeakageResult]:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    ids = [r[0] for r in conn.execute("SELECT catalyst_id FROM catalyst_market_features").fetchall()]
    results = [check_market_features_before_cutoff(conn, cid) for cid in ids]
    conn.close()
    return results
