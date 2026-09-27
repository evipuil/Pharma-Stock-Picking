"""Validity tests for strict OOS selection and leakage-free tail risk."""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from src.backtest.ledger import build_trade_ledger
from src.short_edge.short_score import assign_short_trades, top_fraction_mask
from src.short_edge.tail_risk import fit_tail_risk, predict_tail_risk
from src.short_edge.walk_forward import _exclude_locked_holdout


def test_top_fraction_is_selected_within_each_test_year():
    frame = pd.DataFrame(
        {
            "test_year": [2020] * 5 + [2021] * 5,
            "score": [1, 2, 3, 4, 5, 101, 102, 103, 104, 105],
        }
    )

    mask = top_fraction_mask(frame, "score", 0.20)

    assert frame.loc[mask, "score"].tolist() == [5, 105]
    assert assign_short_trades(frame, "score", "short_top_20pct", 0.20).eq(-1).sum() == 2


def test_locked_holdout_rows_are_excluded_by_date():
    frame = pd.DataFrame(
        {
            "announcement_date": ["2021-12-31", "2022-01-01", "2023-06-01"],
            "value": [1, 2, 3],
        }
    )

    development = _exclude_locked_holdout(frame, "2022-01-01")

    assert development["value"].tolist() == [1]


def test_tail_risk_fallback_never_reads_test_returns():
    train = pd.DataFrame({"x": range(8), "realized_car": [-0.05] * 8})
    bundle = fit_tail_risk(train, ["x"], drop_threshold=-0.20)
    test_a = pd.DataFrame({"x": [1, 2], "realized_car": [-0.80, 0.10]})
    test_b = pd.DataFrame({"x": [1, 2], "realized_car": [0.10, 0.10]})

    pred_a = predict_tail_risk(test_a, bundle)
    pred_b = predict_tail_risk(test_b, bundle)

    assert bundle.classifier is None
    assert np.allclose(pred_a["expected_drop_magnitude"], -0.20)
    assert np.allclose(pred_a["tail_risk_score"], pred_b["tail_risk_score"])


def test_backtest_executes_only_explicit_signals_and_does_not_rescale_exposure():
    rows = pd.DataFrame(
        {
            "catalyst_id": ["NO", "YES"],
            "trade_signal": ["NO TRADE", "LONG"],
            "expected_car": [0.50, 0.10],
            "realized_car": [0.20, 0.05],
            "company_dependency": [0.20, 0.20],
            "test_year": [2020, 2020],
        }
    )
    mock_conn = MagicMock()
    with (
        patch("src.backtest.ledger.sqlite3.connect", return_value=mock_conn),
        patch("src.backtest.ledger.pd.read_sql_query", return_value=rows),
    ):
        trades = build_trade_ledger()

    assert trades["catalyst_id"].tolist() == ["YES"]
    assert trades["expected_car_adj"].iloc[0] == 0.10
