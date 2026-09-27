"""End-to-end stock-picking pipeline orchestrator."""

from __future__ import annotations


def run_stock_picking_pipeline(
    skip_event_study: bool = False,
    skip_fundamentals: bool = False,
) -> dict:
    """
    Run the full catalyst → expected CAR → walk-forward pipeline.

    Preserves existing Wave 1 infrastructure; operates on catalyst-level data.
    """
    results: dict = {}

    from src.catalysts.apply_announcement_overrides import apply_announcement_overrides
    from src.catalysts.backfill_dates import backfill_announcement_dates
    from src.trial_design.features import compute_all_trial_features, export_trial_features_csv

    results["backfill_dates"] = backfill_announcement_dates()
    results["announcement_overrides"] = apply_announcement_overrides()
    results["trial_features"] = compute_all_trial_features()
    export_trial_features_csv()

    if not skip_event_study:
        from src.event_study.catalyst_study import run_catalyst_event_study

        es_df = run_catalyst_event_study()
        results["event_study_rows"] = len(es_df)

    from src.market_expectations.features import (
        compute_all_market_features,
        export_market_features_csv,
    )

    results["market_features"] = compute_all_market_features()
    export_market_features_csv()

    if not skip_fundamentals:
        from src.fundamentals.point_in_time import (
            compute_fundamentals_for_catalysts,
            export_fundamentals_csv,
        )

        results["fundamentals"] = compute_fundamentals_for_catalysts()
        export_fundamentals_csv()

    from src.fundamentals.exposure import compute_exposure_for_catalysts

    results["exposure"] = compute_exposure_for_catalysts()

    from src.validation.point_in_time import (
        generate_point_in_time_report,
        run_point_in_time_audit,
        summarize_point_in_time_audit,
    )

    point_in_time_audit = run_point_in_time_audit()
    results["point_in_time_audit"] = summarize_point_in_time_audit(point_in_time_audit)
    generate_point_in_time_report(point_in_time_audit)

    from src.config import project_root
    from src.return_models.dataset import load_catalyst_modeling_frame
    from src.return_models.expected_car import (
        export_predictions_csv,
        predict_expected_car,
        save_bundle,
        train_expected_car_models,
    )
    from src.return_models.walk_forward import run_walk_forward, summarize_walk_forward

    bundle = train_expected_car_models(feature_set="market_plus_trial")
    model_path = project_root() / "data" / "processed" / "models" / "expected_car_v1.pkl"
    save_bundle(bundle, model_path)
    preds = predict_expected_car(load_catalyst_modeling_frame(), bundle)
    export_predictions_csv(preds)
    results["train_metrics"] = bundle.metrics

    ledger = run_walk_forward(feature_set="market_plus_trial")
    results["walk_forward"] = summarize_walk_forward(ledger)

    from src.backtest.grid import generate_backtest_grid_report
    from src.backtest.ledger import (
        build_trade_ledger,
        export_trade_ledger,
        generate_backtest_report,
        summarize_backtest,
    )
    from src.catalysts.coverage_report import generate_coverage_report
    from src.market_data.price_coverage import generate_price_coverage_report
    from src.ranking.rank_catalysts import export_rankings, rank_catalysts
    from src.return_models.ablation import generate_ablation_report
    from src.return_models.report import generate_model_report
    from src.validation.holdout_eval import generate_holdout_report

    trades = build_trade_ledger()
    export_trade_ledger(trades)
    results["backtest"] = summarize_backtest(trades)
    generate_backtest_report(trades)
    generate_backtest_grid_report()
    generate_coverage_report()
    generate_price_coverage_report()
    generate_model_report()
    generate_ablation_report()
    generate_holdout_report()
    export_rankings(rank_catalysts())

    return results
