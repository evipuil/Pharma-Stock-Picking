"""Tests for catalyst-level schema and migration."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.catalysts.migrate_from_programs import migrate_programs_to_catalysts
from src.db.init_db import init_database


@pytest.fixture
def catalyst_db(tmp_path: Path):
    db = tmp_path / "test.db"
    init_database(db, Path("sql/schema.sql"), Path("sql/schema_catalysts.sql"))
    return db


def test_catalyst_tables_exist(catalyst_db: Path):
    conn = sqlite3.connect(catalyst_db)
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()
    assert "catalysts" in tables
    assert "catalyst_event_study" in tables
    assert "market_bars_daily" in tables


def test_migrate_idempotent_on_empty_db(catalyst_db: Path):
    stats = migrate_programs_to_catalysts(catalyst_db)
    assert stats["created"] == 0
    assert stats["skipped"] == 0
