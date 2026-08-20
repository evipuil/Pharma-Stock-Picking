"""Database initialization utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def init_database(db_path: Path, schema_path: Path, catalyst_schema: Path | None = None) -> Path:
    """Create SQLite database and apply DDL from schema.sql (+ optional catalyst extension)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = schema_path.read_text(encoding="utf-8")

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        if catalyst_schema is None:
            catalyst_schema = schema_path.parent / "schema_catalysts.sql"
        if catalyst_schema.exists():
            conn.executescript(catalyst_schema.read_text(encoding="utf-8"))
        market_schema = schema_path.parent / "schema_market_features.sql"
        if market_schema.exists():
            conn.executescript(market_schema.read_text(encoding="utf-8"))
        pred_schema = schema_path.parent / "schema_predictions.sql"
        if pred_schema.exists():
            conn.executescript(pred_schema.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()

    return db_path.resolve()
