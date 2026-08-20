"""Tests for locked holdout evaluation."""

from src.validation.holdout_eval import run_locked_holdout, summarize_holdout


def test_locked_holdout_runs():
    preds = run_locked_holdout()
    assert not preds.empty
    assert preds["split"].eq("locked_holdout").all()
    assert (preds["catalyst_year"] >= 2019).all()
    assert (preds["catalyst_year"] <= 2021).all()


def test_holdout_summary_has_correlation():
    preds = run_locked_holdout()
    summary = summarize_holdout(preds)
    assert summary["n"] > 0
    assert "correlation_expected_realized" in summary
    assert "mean_realized_car_ci_95" in summary
