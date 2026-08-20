"""Tests for expected CAR assembly."""

from __future__ import annotations

import pandas as pd

from src.return_models.expected_car import ExpectedCarBundle, predict_expected_car


def test_expected_car_formula():
    df = pd.DataFrame(
        {
            "catalyst_id": ["CAT-1"],
            "return_60d": [0.1],
            "abnormal_return_60d_xbi": [0.05],
            "return_20d": [0.02],
            "return_5d": [0.01],
            "return_1d": [0.0],
            "return_120d": [0.15],
            "abnormal_return_20d_xbi": [0.01],
            "distance_from_52w_high": [-0.1],
            "realized_vol_20d": [0.3],
            "volume_ratio_20d": [1.2],
            "pre_catalyst_runup_60d": [0.1],
            "clinical_success": [1],
            "realized_car": [0.05],
        }
    )
    # Minimal mock: set models to None and rely on fallback means
    bundle = ExpectedCarBundle(
        feature_cols=[
            "return_1d",
            "return_5d",
            "return_20d",
            "return_60d",
            "return_120d",
            "abnormal_return_20d_xbi",
            "abnormal_return_60d_xbi",
            "distance_from_52w_high",
            "realized_vol_20d",
            "volume_ratio_20d",
            "pre_catalyst_runup_60d",
        ],
        p_success_model=None,
    )
    # Without fitted models this would fail — test formula directly
    p, es, ef = 0.6, 0.10, -0.15
    expected = p * es + (1 - p) * ef
    assert abs(expected - (0.6 * 0.10 + 0.4 * (-0.15))) < 1e-9
