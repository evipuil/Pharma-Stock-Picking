"""Improved company dependency proxy and failure CAR relationship test."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from src.config import project_root
from src.fundamentals.exposure import classify_ticker


def compute_enhanced_dependency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transparent proxy for asset exposure:
      base = heuristic ticker tier
      + lead asset boost
      + pipeline concentration (single asset flag)
      - approved product / large cap discount
    """
    out = df.copy()
    scores = []
    for _, row in out.iterrows():
        _, base = classify_ticker(row.get("ticker", ""))
        score = base
        if row.get("is_lead_asset") == 1:
            score = min(1.0, score + 0.05)
        if row.get("is_single_asset_company") == 1:
            score = min(1.0, score + 0.05)
        if row.get("phase_numeric", 0) >= 3:
            score = min(1.0, score + 0.03)
        if row.get("is_large_cap") == 1:
            score = max(0.10, score - 0.10)
        scores.append(score)
    out["enhanced_dependency"] = scores
    return out


def test_failure_car_vs_dependency(df: pd.DataFrame) -> dict:
    failures = df[df["clinical_failure"] == 1].dropna(subset=["realized_car", "enhanced_dependency"])
    if len(failures) < 5:
        return {"n_failures": len(failures), "correlation": None}
    r, p = stats.pearsonr(failures["enhanced_dependency"], failures["realized_car"])
    # More negative CAR with higher dependency?
    return {
        "n_failures": len(failures),
        "correlation": float(r),
        "p_value": float(p),
        "interpretation": "Higher dependency associated with more negative failure CAR" if r < 0 and p < 0.05 else "No significant linear relationship",
    }


def persist_enhanced_dependency(df: pd.DataFrame, db_path: Path | None = None) -> int:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "ALTER TABLE asset_exposure ADD COLUMN enhanced_dependency REAL"
    ) if False else None  # column may exist
    try:
        conn.execute("ALTER TABLE asset_exposure ADD COLUMN enhanced_dependency REAL")
    except sqlite3.OperationalError:
        pass
    n = 0
    for _, row in df.iterrows():
        conn.execute(
            "UPDATE asset_exposure SET enhanced_dependency = ? WHERE catalyst_id = ?",
            (row["enhanced_dependency"], row["catalyst_id"]),
        )
        n += conn.total_changes
    conn.commit()
    conn.close()
    return n
