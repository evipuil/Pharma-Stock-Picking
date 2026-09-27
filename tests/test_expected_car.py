"""Tests for expected CAR assembly."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.return_models.expected_car import (
    ExpectedCarBundle,
    predict_expected_car,
    predict_with_wong_prior,
)


class _FixedProbabilityModel:
    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        return np.tile([0.4, 0.6], (len(frame), 1))


def test_expected_car_formula():
    p, es, ef = 0.6, 0.10, -0.15
    expected = p * es + (1 - p) * ef
    assert abs(expected - (0.6 * 0.10 + 0.4 * (-0.15))) < 1e-9


def test_conditional_fallbacks_never_read_prediction_outcomes():
    bundle = ExpectedCarBundle(
        p_success_model=_FixedProbabilityModel(),
        feature_cols=["x"],
        p_feature_cols=["x"],
        car_feature_cols=["x"],
        car_success_fallback=0.08,
        car_failure_fallback=-0.22,
    )
    first = pd.DataFrame({"x": [1.0, 2.0], "clinical_success": [1, 0], "realized_car": [0.9, -0.9]})
    second = first.assign(realized_car=[-0.4, 0.4])

    pred_first = predict_expected_car(first, bundle)
    pred_second = predict_expected_car(second, bundle)

    assert pred_first["expected_car"].equals(pred_second["expected_car"])
    assert pred_first["e_car_given_success"].eq(0.08).all()
    assert pred_first["e_car_given_failure"].eq(-0.22).all()


def test_wong_conditional_returns_are_calibrated_on_training_rows():
    calibration = pd.DataFrame(
        {
            "modality": ["SMALL_MOLECULE", "SMALL_MOLECULE"],
            "clinical_success": [1, 0],
            "realized_car": [0.06, -0.18],
        }
    )
    test = pd.DataFrame(
        {
            "modality": ["SMALL_MOLECULE"],
            "clinical_success": [1],
            "realized_car": [0.95],
        }
    )

    pred = predict_with_wong_prior(test, calibration_df=calibration)

    assert pred["e_car_given_success"].eq(0.06).all()
    assert pred["e_car_given_failure"].eq(-0.18).all()
