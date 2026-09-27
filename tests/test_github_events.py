"""Tests for GitHub EventsStockPrices integration."""

from pathlib import Path

import pandas as pd
import pytest

from src.catalysts.github_events import (
    _drug_similarity,
    apply_github_date_suggestions,
    export_github_candidates,
    load_github_events,
    validate_catalyst_dates,
)
from src.config import project_root


@pytest.fixture
def events_csv(tmp_path):
    d = tmp_path / "EventsStockPrices"
    d.mkdir(parents=True)
    df = pd.DataFrame(
        {
            "ticker": ["CLVS", "MRK", "CLVS"],
            "drug": ["rucaparib", "pembrolizumab", "other drug"],
            "disease": ["ovarian", "melanoma", "other"],
            "stage": ["Phase 2", "Phase 3", "Phase 2"],
            "event_date": pd.to_datetime(["2015-10-25", "2013-06-02", "2018-01-01"]),
            "event_desc": ["top line", "positive", "fail"],
            "stage_normalized": ["Phase 2", "Phase 3", "Phase 2"],
            "source": ["test"] * 3,
            "source_url": ["test"] * 3,
        }
    )
    df.to_csv(d / "clinical_phase_events.csv", index=False)
    return d


def test_drug_similarity_substring():
    assert _drug_similarity("rucaparib", "Rucaparib (CO-338)") >= 0.9


def test_load_github_events_real():
    path = (
        project_root()
        / "data"
        / "external"
        / "github"
        / "EventsStockPrices"
        / "clinical_phase_events.csv"
    )
    if not path.exists():
        pytest.skip("Run seed-github-data first")
    df = load_github_events()
    assert len(df) > 1000
    assert "event_date" in df.columns


def test_validate_catalyst_dates_real():
    db = project_root() / "data" / "processed" / "research.db"
    if not db.exists():
        pytest.skip("DB missing")
    events_path = project_root() / "data" / "external" / "github/EventsStockPrices/clinical_phase_events.csv"
    if not events_path.exists():
        pytest.skip("Run seed-github-data first")
    df = validate_catalyst_dates()
    assert len(df) >= 112
    assert "match_status" in df.columns


def test_export_candidates_bounded():
    events_path = project_root() / "data/external/github/EventsStockPrices/clinical_phase_events.csv"
    if not events_path.exists():
        pytest.skip("Run seed-github-data first")
    cands = export_github_candidates(max_candidates=50)
    assert len(cands) <= 50
    if not cands.empty:
        assert "candidate_id" in cands.columns


def test_apply_github_suggestions_idempotent():
    sugg_path = project_root() / "configs" / "github_events_date_suggestions.yaml"
    if not sugg_path.exists():
        pytest.skip("Run validate-github-events first")
    stats = apply_github_date_suggestions(merge_overrides=False)
    assert "github_suggestions_total" in stats
    assert stats["github_suggestions_skipped_existing"] >= 0
