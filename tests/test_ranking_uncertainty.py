"""Tests for ranking uncertainty intervals."""

import numpy as np
import pandas as pd

from src.ranking.uncertainty import (
    add_uncertainty_columns,
    classify_confidence_signal,
    conformal_interval,
)


def test_conformal_interval_symmetric():
    residuals = np.array([-0.05, 0.03, -0.02, 0.04, -0.01])
    lo, hi = conformal_interval(0.10, residuals, alpha=0.10)
    assert lo < 0.10 < hi
    assert hi - lo > 0


def test_classify_confidence_signal():
    row = pd.Series({"expected_car_exposure_adj_lo": 0.02, "expected_car_exposure_adj_hi": 0.08})
    assert classify_confidence_signal(row) == "CONFIDENT LONG"
    row2 = pd.Series({"expected_car_exposure_adj_lo": -0.08, "expected_car_exposure_adj_hi": -0.01})
    assert classify_confidence_signal(row2) == "CONFIDENT SHORT"


def test_add_uncertainty_columns():
    preds = pd.DataFrame(
        {
            "expected_car": [0.05, -0.03],
            "company_dependency": [0.9, 0.9],
        }
    )
    out = add_uncertainty_columns(preds)
    assert "expected_car_lo" in out.columns
    assert "expected_car_exposure_adj_hi" in out.columns
    assert out["expected_car_ci_width"].iloc[0] > 0
