"""Orchestrate short-edge validation pipeline."""

from __future__ import annotations

from pathlib import Path

from src.config import project_root
from src.short_edge.baseline_freeze import freeze_baseline
from src.short_edge.dataset import load_short_edge_frame
from src.short_edge.dependency import compute_enhanced_dependency, persist_enhanced_dependency
from src.short_edge.price_recovery import export_missing_price_requirements, try_recover_missing_cars
from src.short_edge.reports import generate_short_edge_reports
from src.short_edge.walk_forward import (
    export_short_predictions,
    persist_short_predictions,
    run_short_walk_forward,
)


def regenerate_stale_reports() -> None:
    """Regenerate model_performance, backtest_grid, event_study from current DB without re-running walk-forward."""
    from src.return_models.report import generate_model_report
    from src.backtest.grid import generate_backtest_grid_report
    from src.catalysts.coverage_report import generate_coverage_report

    generate_model_report(rerun_walk_forward=False)
    generate_backtest_grid_report()
    generate_coverage_report()  # includes event_study.md


def run_short_edge_validation(freeze: bool = True) -> dict:
    root = project_root()

    if freeze:
        baseline_path = freeze_baseline()
        print(f"Baseline frozen at {baseline_path}")

    # Price recovery attempt
    recovery = try_recover_missing_cars()
    print(f"Price recovery: {recovery}")

    # Enhanced dependency
    frame = load_short_edge_frame()
    dep_frame = compute_enhanced_dependency(frame)
    persist_enhanced_dependency(dep_frame)

    # Walk-forward short models
    preds = run_short_walk_forward(feature_set="everything_no_preclinical")
    # Enrich with stratification columns
    frame = load_short_edge_frame()
    enrich_cols = [c for c in frame.columns if c not in preds.columns and c != "catalyst_id"]
    if enrich_cols:
        preds = preds.merge(frame[["catalyst_id"] + enrich_cols], on="catalyst_id", how="left")
    export_short_predictions(preds)
    persist_short_predictions(preds)

    # Reports
    result = generate_short_edge_reports(preds)
    print(f"Verdict: {result['verdict']}")
    return result
