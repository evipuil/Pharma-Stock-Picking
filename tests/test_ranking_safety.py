"""Safety tests for live catalyst ranking."""

from datetime import datetime, timezone
from unittest.mock import patch

import pandas as pd
import pytest

from src.ranking.rank_catalysts import rank_catalysts
from src.return_models.expected_car import ExpectedCarBundle, save_bundle


def test_ranking_refuses_realized_outcome_fallback(tmp_path):
    inference = pd.DataFrame(
        {
            "catalyst_id": ["CAT-FUTURE"],
            "announcement_date": ["2030-01-01"],
            "clinical_success": [1],
            "realized_car": [0.99],
        }
    )
    missing_model = tmp_path / "missing.pkl"

    with (
        patch(
            "src.ranking.rank_catalysts.load_catalyst_modeling_frame",
            return_value=inference,
        ),
        pytest.raises(FileNotFoundError, match="refusing to rank with realized outcomes"),
    ):
        rank_catalysts(model_path=missing_model)


def test_ranking_defaults_to_prospective_candidates():
    captured: dict = {}

    def _load_frame(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame()

    with patch(
        "src.ranking.rank_catalysts.load_catalyst_modeling_frame",
        side_effect=_load_frame,
    ):
        ranked = rank_catalysts()

    assert ranked.empty
    assert captured["labeled_only"] is False
    assert captured["as_of"] == datetime.now(timezone.utc).date()


def test_historical_ranking_requires_explicit_opt_in():
    captured: dict = {}

    def _load_frame(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame()

    with patch(
        "src.ranking.rank_catalysts.load_catalyst_modeling_frame",
        side_effect=_load_frame,
    ):
        rank_catalysts(include_historical=True)

    assert captured["as_of"] is None


def test_ranking_rejects_model_without_training_provenance(tmp_path):
    model_path = tmp_path / "legacy.pkl"
    save_bundle(ExpectedCarBundle(), model_path)
    inference = pd.DataFrame({"catalyst_id": ["CAT-FUTURE"]})

    with (
        patch(
            "src.ranking.rank_catalysts.load_catalyst_modeling_frame",
            return_value=inference,
        ),
        pytest.raises(ValueError, match="lacks strict point-in-time training provenance"),
    ):
        rank_catalysts(model_path=model_path)
