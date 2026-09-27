"""Apply curated press-release dates and tickers to catalyst rows."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import yaml

from src.config import project_root
from src.event_study.windows import infer_trading_cutoff


def _load_overrides() -> dict:
    path = project_root() / "configs" / "catalyst_announcement_overrides.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("overrides", {})


def apply_announcement_overrides(
    db_path: Path | None = None,
    overrides: dict | None = None,
) -> dict:
    overrides = overrides if overrides is not None else _load_overrides()
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    stats = {"updated": 0, "tickers": 0, "missing": 0}

    for catalyst_id, spec in overrides.items():
        exists = conn.execute(
            "SELECT 1 FROM catalysts WHERE catalyst_id = ?", (catalyst_id,)
        ).fetchone()
        if not exists:
            stats["missing"] += 1
            continue

        ann = date.fromisoformat(str(spec["announcement_date"])[:10])
        timing = spec.get("announcement_timing", "UNKNOWN")
        cutoff, day_before, day_after, _conf = infer_trading_cutoff(ann, timing)

        conn.execute(
            """
            UPDATE catalysts SET
                announcement_date = ?,
                announcement_timing = ?,
                announcement_source = ?,
                announcement_source_url = ?,
                trading_cutoff_date = ?,
                trading_day_before = ?,
                first_trading_day_after = ?,
                updated_at = datetime('now')
            WHERE catalyst_id = ?
            """,
            (
                ann.isoformat(),
                timing,
                spec.get("announcement_source", "PRESS_RELEASE"),
                spec.get("source_url"),
                cutoff.isoformat(),
                day_before.isoformat(),
                day_after.isoformat(),
                catalyst_id,
            ),
        )
        conn.execute(
            """
            INSERT INTO catalyst_trading_cutoffs
                (catalyst_id, entry_cutoff_date, cutoff_rationale, execution_confidence)
            VALUES (?, ?, ?, 'HIGH')
            ON CONFLICT(catalyst_id) DO UPDATE SET
                entry_cutoff_date = excluded.entry_cutoff_date,
                cutoff_rationale = excluded.cutoff_rationale,
                execution_confidence = 'HIGH'
            """,
            (catalyst_id, cutoff.isoformat(), spec.get("notes", "PRESS_RELEASE")),
        )
        stats["updated"] += 1

        ticker = (spec.get("ticker") or "").upper()
        if ticker:
            conn.execute(
                """
                UPDATE catalyst_ticker_history
                SET ticker_at_event = ?, ticker_current = ?,
                    map_source = 'announcement_overrides',
                    notes = ?
                WHERE catalyst_id = ?
                """,
                (ticker, ticker, spec.get("notes"), catalyst_id),
            )
            stats["tickers"] += 1

    conn.commit()
    conn.close()
    return stats
