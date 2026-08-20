"""Tests for database initialization."""

from pathlib import Path

from src.db.init_db import init_database


def test_init_database_creates_tables(tmp_path: Path):
    db_path = tmp_path / "test.db"
    schema_path = Path("sql/schema.sql")
    init_database(db_path, schema_path)

    import sqlite3

    conn = sqlite3.connect(db_path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()
    table_names = {t[0] for t in tables}
    assert "programs" in table_names
    assert "animal_studies" in table_names
    assert "leakage_audit_log" in table_names
