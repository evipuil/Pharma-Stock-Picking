"""Sync delisted ticker metadata into catalyst_ticker_history."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import yaml

from src.config import project_root


def sync_delist_metadata(db_path: Path | None = None) -> dict:
    path = project_root() / "configs" / "ticker_delist_map.yaml"
    if not path.exists():
        return {"updated": 0}
    tickers = yaml.safe_load(path.read_text(encoding="utf-8")).get("tickers", {})
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)

    updated = 0
    for catalyst_id, ticker in conn.execute(
        """
        SELECT c.catalyst_id, ct.ticker_at_event
        FROM catalysts c
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        """
    ).fetchall():
        meta = tickers.get((ticker or "").upper())
        if not meta:
            continue
        conn.execute(
            """
            UPDATE catalyst_ticker_history
            SET delisted = ?,
                delist_date = ?,
                successor_ticker = ?,
                notes = ?,
                map_source = 'ticker_delist_map.yaml'
            WHERE catalyst_id = ?
            """,
            (
                1 if meta.get("delisted") else 0,
                meta.get("delist_date"),
                meta.get("successor_ticker"),
                meta.get("notes"),
                catalyst_id,
            ),
        )
        updated += 1

    conn.commit()
    conn.close()
    return {"updated": updated}
