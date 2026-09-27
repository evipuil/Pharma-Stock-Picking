"""CLI entry points for pipeline operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.db.init_db import init_database


def main() -> None:
    parser = argparse.ArgumentParser(description="StockPicking research pipeline CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init-db", help="Initialize SQLite database from schema")
    init_parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("data/processed/research.db"),
        help="Path to SQLite database file",
    )
    init_parser.add_argument(
        "--schema",
        type=Path,
        default=Path("sql/schema.sql"),
        help="Path to SQL schema file",
    )

    sub.add_parser("curate-wave1", help="Fetch Wave 1 data, load DB, run leakage audit")
    sub.add_parser("analyze", help="Run exploratory baseline analysis")
    sub.add_parser("event-study", help="Run event study on Wave 1 readouts")
    sub.add_parser("apply-extractions", help="Apply manual preclinical feature extractions")
    sub.add_parser("add-failures", help="Load Wave 2 failure programs")
    sub.add_parser("train-model", help="Train animal→clinical prediction models")
    sub.add_parser("predict", help="Score programs with trained models")
    sub.add_parser("expand-cohort", help="Batch-add programs from batch_candidates.yaml")
    sub.add_parser(
        "backfill-literature", help="PubMed backfill for programs with sparse animal data"
    )
    sub.add_parser("fix-leakage", help="Repair missing pub dates on verified studies")
    sub.add_parser(
        "migrate-catalysts", help="Apply catalyst schema + migrate programs to catalysts"
    )
    sub.add_parser("expand-catalysts", help="Expand catalyst calendar toward Phase A (N≥100)")
    sub.add_parser("catalyst-event-study", help="Multi-window event study for all catalysts")
    sub.add_parser("catalyst-coverage", help="Generate catalyst coverage + event study reports")
    sub.add_parser("sync-prices", help="Cache benchmark price history (SPY, XBI, IBB)")
    sub.add_parser("backfill-catalyst-dates", help="Infer announcement dates from outcomes/t0")
    sub.add_parser(
        "apply-announcement-overrides",
        help="Apply curated press-release dates/tickers from YAML",
    )
    sub.add_parser("compute-market-features", help="Pre-catalyst market expectation features")
    sub.add_parser("train-expected-car", help="Train P(success) + conditional CAR models")
    sub.add_parser("walk-forward", help="Walk-forward OOS expected CAR evaluation")
    sub.add_parser("model-report", help="Generate expected CAR performance report")
    rank_parser = sub.add_parser(
        "rank-catalysts", help="Rank catalysts by exposure-adjusted expected CAR"
    )
    rank_parser.add_argument(
        "--as-of", type=str, default=None, help="Filter catalysts on/after date YYYY-MM-DD"
    )
    rank_parser.add_argument(
        "--include-history",
        action="store_true",
        help="Research-only: include already announced catalysts",
    )
    sub.add_parser("audit-point-in-time", help="Audit feature source dates against trading cutoffs")
    sub.add_parser("compute-exposure", help="Compute company_dependency scores for catalysts")
    sub.add_parser("compute-fundamentals", help="SEC EDGAR point-in-time fundamentals")
    sub.add_parser("sync-catalyst-prices", help="Prefetch price history for all catalyst tickers")
    sub.add_parser("price-coverage", help="Audit price data coverage for catalysts")
    export_parser = sub.add_parser(
        "export-delisted-prices",
        help="Export delisted tickers to data/external/prices/ via Polygon",
    )
    export_parser.add_argument("--force", action="store_true", help="Overwrite existing CSVs")
    seed_parser = sub.add_parser(
        "seed-delisted-prices",
        help="Seed delisted prices from pystock GitHub archives (2009-2017)",
    )
    seed_parser.add_argument("--force", action="store_true", help="Merge/overwrite existing CSVs")
    github_parser = sub.add_parser(
        "seed-github-data",
        help="Download all GitHub public datasets (pystock, EventsStockPrices, delisted sample)",
    )
    github_parser.add_argument(
        "--force", action="store_true", help="Re-download all GitHub sources"
    )
    sub.add_parser(
        "validate-github-events",
        help="Validate catalyst dates vs GitHub EventsStockPrices; export candidates",
    )
    sub.add_parser(
        "apply-github-date-suggestions",
        help="Apply GitHub event date corrections to catalyst registry",
    )
    sub.add_parser(
        "import-github-pilot",
        help="Import filtered pilot batch of GitHub event candidates (~20)",
    )
    sub.add_parser(
        "short-edge-ablation",
        help="Feature ablation for short-edge OOS strategies",
    )
    sub.add_parser(
        "extend-prices-stooq",
        help="Extend delisted local CSVs via Stooq (requires STOOQ_API_KEY)",
    )
    sub.add_parser("audit-pipeline", help="Verify deliverables against objective requirements")
    sub.add_parser(
        "compute-trial-features", help="Compute catalyst trial design features from CT.gov"
    )
    sub.add_parser("backtest", help="Build OOS trade ledger and backtest report")
    sub.add_parser("backtest-grid", help="Slippage grid + strategy variant backtests")
    sub.add_parser("holdout-eval", help="Legacy 2019-2021 evaluation (not pristine)")
    sub.add_parser("ablation", help="Compare model variants for expected CAR")
    sub.add_parser("freeze-baseline", help="Freeze baseline artifacts before short-edge research")
    sub.add_parser(
        "validate-short-edge", help="Run short-edge validation without re-freezing baseline"
    )
    sub.add_parser("run-short-edge", help="Freeze baseline + run full short-edge validation")
    sub.add_parser("run-stock-picking", help="End-to-end stock-picking pipeline")
    sub.add_parser("run-all", help="Full Wave 1 pipeline: curate → analyze → event study")

    args = parser.parse_args()
    if args.command == "init-db":
        path = init_database(args.db_path, args.schema)
        print(f"Database initialized at {path}")
    elif args.command == "curate-wave1":
        from src.pipeline.wave1_curation import main as curate_main

        curate_main()
    elif args.command == "analyze":
        from src.pipeline.exploratory_analysis import main as analyze_main

        analyze_main()
    elif args.command == "event-study":
        from src.pipeline.event_study_run import main as es_main

        es_main()
    elif args.command == "apply-extractions":
        from src.preclinical.apply_extractions import main as extract_main

        extract_main()
    elif args.command == "add-failures":
        from src.pipeline.add_wave2_failures import load_failures

        load_failures()
    elif args.command == "train-model":
        from src.models.train import main as train_main

        train_main()
    elif args.command == "expand-cohort":
        from src.pipeline.batch_expand_cohort import main as expand_main

        expand_main()
    elif args.command == "backfill-literature":
        from src.pipeline.backfill_literature import backfill

        stats = backfill()
        print(f"Backfill complete: {stats}")
    elif args.command == "fix-leakage":
        from src.pipeline.fix_leakage_dates import fix_missing_dates

        print(fix_missing_dates())
    elif args.command == "migrate-catalysts":
        from src.catalysts.migrate_from_programs import (
            export_catalysts_csv,
            migrate_programs_to_catalysts,
        )

        stats = migrate_programs_to_catalysts()
        csv_path = export_catalysts_csv()
        print(f"Migrated: {stats}")
        print(f"Exported: {csv_path}")
    elif args.command == "expand-catalysts":
        from src.catalysts.expand_cohort import expand_catalyst_cohort

        stats = expand_catalyst_cohort()
        print(stats)
    elif args.command == "catalyst-event-study":
        from src.event_study.catalyst_study import run_catalyst_event_study, summarize_by_outcome

        df = run_catalyst_event_study()
        print(summarize_by_outcome(df).to_string(index=False) if not df.empty else "No results")
    elif args.command == "catalyst-coverage":
        from src.catalysts.coverage_report import generate_coverage_report

        print(f"Report: {generate_coverage_report()}")
    elif args.command == "sync-prices":
        from src.config import load_yaml, project_root
        from src.market_data.history import fetch_or_load

        cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
        start = cfg["market_data"]["history_start"]
        for t in cfg["market_data"]["benchmark_tickers"]:
            df = fetch_or_load(t, start=start, force_refresh=False)
            print(f"{t}: {len(df)} bars")
    elif args.command == "backfill-catalyst-dates":
        from src.catalysts.backfill_dates import backfill_announcement_dates

        print(backfill_announcement_dates())
    elif args.command == "apply-announcement-overrides":
        from src.catalysts.apply_announcement_overrides import apply_announcement_overrides

        print(apply_announcement_overrides())
    elif args.command == "compute-market-features":
        from src.market_expectations.features import (
            compute_all_market_features,
            export_market_features_csv,
        )

        stats = compute_all_market_features()
        path = export_market_features_csv()
        print(f"Market features: {stats}")
        print(f"Exported: {path}")
    elif args.command == "compute-trial-features":
        from src.trial_design.features import compute_all_trial_features, export_trial_features_csv

        stats = compute_all_trial_features()
        path = export_trial_features_csv()
        print(f"Trial features: {stats}")
        print(f"Exported: {path}")
    elif args.command == "train-expected-car":
        from src.config import project_root
        from src.return_models.dataset import load_catalyst_modeling_frame
        from src.return_models.expected_car import (
            export_predictions_csv,
            predict_expected_car,
            save_bundle,
            train_expected_car_models,
        )

        bundle = train_expected_car_models()
        df = load_catalyst_modeling_frame()
        preds = predict_expected_car(df, bundle)
        model_path = project_root() / "data" / "processed" / "models" / "expected_car_v1.pkl"
        save_bundle(bundle, model_path)
        csv_path = export_predictions_csv(preds)
        print(f"Metrics: {bundle.metrics}")
        print(f"Model: {model_path}")
        print(f"Predictions: {csv_path}")
    elif args.command == "walk-forward":
        from src.return_models.walk_forward import run_walk_forward, summarize_walk_forward

        ledger = run_walk_forward()
        print(summarize_walk_forward(ledger))
        print(f"Ledger rows: {len(ledger)}")
    elif args.command == "model-report":
        from src.return_models.report import generate_model_report

        print(f"Report: {generate_model_report(rerun_walk_forward=False)}")
    elif args.command == "compute-exposure":
        from src.fundamentals.exposure import compute_exposure_for_catalysts

        print(compute_exposure_for_catalysts())
    elif args.command == "compute-fundamentals":
        from src.fundamentals.point_in_time import (
            compute_fundamentals_for_catalysts,
            export_fundamentals_csv,
        )

        stats = compute_fundamentals_for_catalysts()
        path = export_fundamentals_csv()
        print(f"Fundamentals: {stats}")
        print(f"Exported: {path}")
    elif args.command == "sync-catalyst-prices":
        from src.market_data.price_coverage import sync_catalyst_prices
        from src.market_data.ticker_metadata import sync_delist_metadata

        print(sync_delist_metadata())
        print(sync_catalyst_prices(force_refresh=False))
    elif args.command == "price-coverage":
        from src.market_data.price_coverage import generate_price_coverage_report

        print(f"Report: {generate_price_coverage_report()}")
    elif args.command == "export-delisted-prices":
        from src.market_data.export_delisted import export_delisted_prices

        print(export_delisted_prices(force=args.force))
    elif args.command == "seed-delisted-prices":
        from src.market_data.seed_pystock import seed_pystock_prices

        print(seed_pystock_prices(force=args.force))
    elif args.command == "seed-github-data":
        from src.market_data.seed_github import seed_all_github_sources

        stats = seed_all_github_sources(force=args.force)
        print(json.dumps(stats, indent=2, default=str))
    elif args.command == "validate-github-events":
        from src.catalysts.github_events import generate_github_validation_report

        report = generate_github_validation_report()
        print(f"Report: {report}")
    elif args.command == "apply-github-date-suggestions":
        from src.catalysts.github_events import apply_github_date_suggestions

        stats = apply_github_date_suggestions()
        print(json.dumps(stats, indent=2))
    elif args.command == "import-github-pilot":
        from src.catalysts.import_github_candidates import import_github_pilot

        stats = import_github_pilot(max_candidates=20)
        print(json.dumps(stats, indent=2, default=str))
    elif args.command == "short-edge-ablation":
        from src.short_edge.ablation import generate_ablation_report

        print(f"Report: {generate_ablation_report()}")
    elif args.command == "extend-prices-stooq":
        from src.short_edge.price_recovery import try_extend_prices_via_stooq

        print(json.dumps(try_extend_prices_via_stooq(), indent=2))
    elif args.command == "audit-pipeline":
        from src.validation.pipeline_audit import generate_audit_report, summarize_audit

        summary = summarize_audit()
        print(f"Pass: {summary['pass']}, Partial: {summary['partial']}, Fail: {summary['fail']}")
        report = generate_audit_report()
        print(f"Report: {report}")
    elif args.command == "rank-catalysts":
        from datetime import date as date_cls

        from src.ranking.rank_catalysts import export_rankings, format_decomposition, rank_catalysts

        as_of = date_cls.fromisoformat(args.as_of) if args.as_of else None
        ranked = rank_catalysts(as_of=as_of, include_historical=args.include_history)
        path = export_rankings(ranked)
        print(ranked.head(15).to_string(index=False))
        print(f"\nSaved: {path}")
        if not ranked.empty:
            print("\n--- Top recommendation decomposition ---")
            print(format_decomposition(ranked.iloc[0]))
    elif args.command == "audit-point-in-time":
        from src.validation.point_in_time import (
            generate_point_in_time_report,
            run_point_in_time_audit,
            summarize_point_in_time_audit,
        )

        audit = run_point_in_time_audit()
        print(summarize_point_in_time_audit(audit))
        print(f"Report: {generate_point_in_time_report(audit)}")
    elif args.command == "backtest":
        from src.backtest.ledger import (
            build_trade_ledger,
            export_trade_ledger,
            generate_backtest_report,
            summarize_backtest,
        )

        trades = build_trade_ledger()
        path = export_trade_ledger(trades)
        report = generate_backtest_report(trades)
        print(summarize_backtest(trades))
        print(f"Trade ledger: {path}")
        print(f"Report: {report}")
    elif args.command == "backtest-grid":
        from src.backtest.grid import (
            generate_backtest_grid_report,
            run_slippage_grid,
            run_strategy_grid,
        )

        slip = run_slippage_grid()
        strat = run_strategy_grid()
        print("Slippage grid:")
        print(slip.to_string(index=False) if not slip.empty else "No trades")
        print("\nStrategy grid:")
        print(strat.to_string(index=False) if not strat.empty else "No trades")
        report = generate_backtest_grid_report()
        print(f"\nReport: {report}")
    elif args.command == "holdout-eval":
        from src.validation.holdout_eval import (
            generate_holdout_report,
            run_holdout_baselines,
            summarize_holdout,
        )

        baselines = run_holdout_baselines()
        for name, preds in baselines.items():
            print(f"\n{name}: {summarize_holdout(preds)}")
        report = generate_holdout_report()
        print(f"\nReport: {report}")
    elif args.command == "ablation":
        from src.return_models.ablation import generate_ablation_report, run_ablation

        df = run_ablation()
        print(df.to_string(index=False))
        print(f"\nReport: {generate_ablation_report()}")
    elif args.command == "freeze-baseline":
        from src.short_edge.baseline_freeze import freeze_baseline

        path = freeze_baseline()
        print(f"Baseline frozen: {path}")
    elif args.command == "validate-short-edge":
        from src.short_edge.run import run_short_edge_validation

        result = run_short_edge_validation(freeze=False)
        print(f"Verdict: {result['verdict']}")
    elif args.command == "run-short-edge":
        from src.short_edge.run import run_short_edge_validation

        result = run_short_edge_validation(freeze=True)
        print(f"Verdict: {result['verdict']}")
    elif args.command == "predict":
        from src.models.predict import main as predict_main

        predict_main()
    elif args.command == "run-stock-picking":
        from src.pipeline.stock_picking_run import run_stock_picking_pipeline

        results = run_stock_picking_pipeline()
        for k, v in results.items():
            print(f"{k}: {v}")
    elif args.command == "run-all":
        from src.pipeline.event_study_run import main as es_main
        from src.pipeline.exploratory_analysis import main as analyze_main
        from src.pipeline.wave1_curation import main as curate_main

        curate_main()
        print("\n--- Exploratory analysis ---")
        analyze_main()
        print("\n--- Event study ---")
        es_main()


if __name__ == "__main__":
    main()
