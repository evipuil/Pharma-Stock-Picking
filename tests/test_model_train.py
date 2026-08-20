"""Tests for feature matrix and model training."""

from pathlib import Path

import pytest

from src.feature_engineering.build_matrix import build_feature_matrix
from src.models.train import train_logistic_model


DB = Path("data/processed/research.db")


@pytest.mark.skipif(not DB.exists(), reason="database not built")
def test_feature_matrix_has_label():
    df, cols = build_feature_matrix(db_path=DB)
    assert not df.empty
    assert "clinical_success" in df.columns
    assert len(cols) > 0


@pytest.mark.skipif(not DB.exists(), reason="database not built")
def test_train_logistic_produces_probabilities():
    df, _ = build_feature_matrix(db_path=DB)
    if df["clinical_success"].nunique() < 2 or len(df) < 4:
        pytest.skip("need both classes and N>=4")
    bundle = train_logistic_model(programs_df=df, feature_set="all_preclinical", calibrate=False)
    assert "overall" in bundle.metrics
    assert 0 <= bundle.metrics["overall"]["brier_score"] <= 1
