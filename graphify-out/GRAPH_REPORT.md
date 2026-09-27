# Graph Report - src  (2026-08-20)

## Corpus Check
- 104 files · ~34,362 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 800 nodes · 1493 edges · 55 communities (50 shown, 5 thin omitted)
- Extraction: 75% EXTRACTED · 25% INFERRED · 0% AMBIGUOUS · INFERRED: 380 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Market Data Operations
- Short Walk Forward
- Clinical Trial Cohorts
- Catalyst Event Studies
- Price Adapter Interfaces
- Feature Matrix Prediction
- Trial Design Analysis
- Short Scoring Baselines
- Market Data Validation
- Ticker Resolution Seeding
- Preclinical Leakage Repair
- GitHub Catalyst Events
- PubMed Literature Backfill
- Market Model Returns
- Robustness Testing
- Point-in-Time Fundamentals
- Delisted Price Recovery
- Backtest Parameter Grid
- Pipeline Trade Ledger
- Company Exposure Controls
- Prediction Uncertainty Intervals
- Return Model Ablation
- Expected CAR Models
- Market Expectations Features
- Return Walk Forward
- Holdout Evaluation
- Local Price Adapter
- Catalyst Ranking Export
- Short Modeling Dataset
- Trading Signal Assignment
- GitHub Candidate Import
- Pipeline Compliance Audit
- Return Modeling Dataset
- Feature Engineering Package
- Research Pipeline Package
- Short Edge Package
- Feature Matrix Module
- Ranking Module

## God Nodes (most connected - your core abstractions)
1. `project_root()` - 80 edges
2. `main()` - 60 edges
3. `run_stock_picking_pipeline()` - 32 edges
4. `load_yaml()` - 25 edges
5. `run_walk_forward()` - 18 edges
6. `run_catalyst_event_study()` - 18 edges
7. `run_short_walk_forward()` - 18 edges
8. `expand_catalyst_cohort()` - 17 edges
9. `PubMedClient` - 16 edges
10. `load_catalyst_modeling_frame()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `expand_catalyst_cohort()` --uses--> `PubMedClient`  [INFERRED]
  catalysts/expand_cohort.py → literature/pubmed_client.py
- `load_failures()` --uses--> `PubMedClient`  [INFERRED]
  pipeline/add_wave2_failures.py → literature/pubmed_client.py
- `expand_cohort()` --uses--> `PubMedClient`  [INFERRED]
  pipeline/batch_expand_cohort.py → literature/pubmed_client.py
- `fix_missing_dates()` --uses--> `PubMedClient`  [INFERRED]
  pipeline/fix_leakage_dates.py → literature/pubmed_client.py
- `curate_wave1()` --uses--> `PubMedClient`  [INFERRED]
  pipeline/wave1_curation.py → literature/pubmed_client.py

## Import Cycles
- None detected.

## Communities (55 total, 5 thin omitted)

### Community 0 - "Market Data Operations"
Cohesion: 0.06
Nodes (50): generate_coverage_report(), Path, Generate catalyst dataset coverage report., apply_catalyst_schema(), export_catalysts_csv(), migrate_programs_to_catalysts(), _outcome_category(), Path (+42 more)

### Community 1 - "Short Walk Forward"
Cohesion: 0.06
Nodes (53): ConditionalCarBundle, fit_conditional_car(), _make_ridge(), predict_car_failure(), predict_car_success(), DataFrame, ndarray, Pipeline (+45 more)

### Community 2 - "Clinical Trial Cohorts"
Cohesion: 0.06
Nodes (47): expand_catalyst_cohort(), Path, ClinicalTrialsGovClient, Any, Path, ClinicalTrials.gov API client (Phase 1)., Search CT.gov v2 API; returns list of study JSON dicts., _get() (+39 more)

### Community 3 - "Catalyst Event Studies"
Cohesion: 0.05
Nodes (47): apply_announcement_overrides(), _load_overrides(), Path, Apply curated press-release dates and tickers to catalyst rows., _apply_date(), backfill_announcement_dates(), _infer_date(), date (+39 more)

### Community 4 - "Price Adapter Interfaces"
Cohesion: 0.05
Nodes (30): ABC, MissingCredentialsError, PriceAdapter, PriceBar, DataFrame, Path, Price data adapter interface., Abstract daily OHLCV provider. (+22 more)

### Community 5 - "Feature Matrix Prediction"
Cohesion: 0.10
Nodes (37): ColumnTransformer, Connection, aggregate_program_features(), assign_temporal_split(), _binary_any(), build_feature_matrix(), build_study_level_frame(), _mean_or_nan() (+29 more)

### Community 6 - "Trial Design Analysis"
Cohesion: 0.10
Nodes (26): load_benchmark_rates(), lookup_pos_rate(), DataFrame, Path, Baseline PoS lookup from Wong/BIO tables., Hierarchical fallback lookup for baseline probability., load_program_table(), main() (+18 more)

### Community 7 - "Short Scoring Baselines"
Cohesion: 0.10
Nodes (27): generate_ablation_report(), DataFrame, Path, Feature ablation for short strategy OOS performance., Run feature ablations and write markdown report., run_feature_ablations(), assign_baseline_side(), evaluate_baseline() (+19 more)

### Community 8 - "Market Data Validation"
Cohesion: 0.13
Nodes (25): download_apify_delisted_sample(), download_events_stock_prices(), download_pystock_readme(), _ensure_dir(), Path, Download and normalize public datasets from GitHub (and linked free archives)., Cache HoleyHan/pystock-data README for provenance., Download all available GitHub-linked public datasets. (+17 more)

### Community 9 - "Ticker Resolution Seeding"
Cohesion: 0.14
Nodes (24): _cache_dir(), _daily_archive_urls(), _download(), _extract_prices(), _last_pystock_date(), _normalize(), _output_dir(), DataFrame (+16 more)

### Community 10 - "Preclinical Leakage Repair"
Cohesion: 0.12
Nodes (21): fix_missing_dates(), Fix missing publication dates on verified animal studies (leakage repair)., compute_program_aggregates(), export_extraction_summary(), Connection, Program-level preclinical feature aggregation., Return human-readable extraction summary for reporting., Aggregate verified animal_study_features to program_preclinical_features. (+13 more)

### Community 11 - "GitHub Catalyst Events"
Cohesion: 0.19
Nodes (22): apply_github_date_suggestions(), _best_event_match(), _drug_similarity(), export_github_candidates(), generate_github_validation_report(), load_catalyst_registry(), load_github_date_suggestions(), load_github_events() (+14 more)

### Community 12 - "PubMed Literature Backfill"
Cohesion: 0.17
Nodes (9): Element, PubMedClient, Any, Path, PubMed E-utilities client (Phase 1)., Return PMIDs matching query, optionally filtered by max publication date…, Search pre-t0 animal studies for a drug., backfill() (+1 more)

### Community 13 - "Market Model Returns"
Cohesion: 0.13
Nodes (16): cumulative_abnormal_return(), estimate_market_model_beta(), DatetimeIndex, Series, Event study CAR computation (Phase 3)., OLS estimate of alpha and beta for market model., cache_ticker(), download_adj_close() (+8 more)

### Community 14 - "Robustness Testing"
Cohesion: 0.19
Nodes (17): _bootstrap_interval(), ndarray, block_bootstrap_by_year(), bootstrap_short_strategy(), era_split_analysis(), leave_one_out_analysis(), DataFrame, ndarray (+9 more)

### Community 15 - "Point-in-Time Fundamentals"
Cohesion: 0.18
Nodes (16): fetch_company_facts(), _get(), load_ticker_cik_map(), lookup_cik(), SEC EDGAR API client for company facts and CIK lookup., Return upper-case ticker → CIK integer., _user_agent(), compute_fundamentals_for_catalysts() (+8 more)

### Community 16 - "Delisted Price Recovery"
Cohesion: 0.16
Nodes (13): _empty_frame(), DataFrame, Stooq daily OHLCV adapter (free tier requires STOOQ_API_KEY)., Stooq historical daily CSV download. Register at https://stooq.com/db/i/ for a…, StooqAdapter, _count_cars(), export_missing_price_requirements(), Path (+5 more)

### Community 17 - "Backtest Parameter Grid"
Cohesion: 0.29
Nodes (16): apply_slippage(), _assign_sides_threshold(), _assign_sides_top_k(), _assign_sides_walkforward(), bootstrap_significance(), generate_backtest_grid_report(), _load_oos_ledger(), DataFrame (+8 more)

### Community 18 - "Pipeline Trade Ledger"
Cohesion: 0.22
Nodes (14): build_trade_ledger(), export_trade_ledger(), generate_backtest_report(), DataFrame, Path, Simple backtester: walk-forward ledger → trade P&L with slippage., Build P&L for explicit walk-forward signals. The optional threshold fallback…, summarize_backtest() (+6 more)

### Community 19 - "Company Exposure Controls"
Cohesion: 0.17
Nodes (14): classify_ticker(), compute_exposure_for_catalysts(), _load_exposure_config(), load_exposure_frame(), DataFrame, Path, Company / asset exposure scoring for catalyst impact scaling., compute_enhanced_dependency() (+6 more)

### Community 20 - "Prediction Uncertainty Intervals"
Cohesion: 0.17
Nodes (15): add_uncertainty_columns(), bootstrap_expected_car_intervals(), classify_confidence_signal(), conformal_interval(), _load_oos_residuals(), DataFrame, ndarray, Path (+7 more)

### Community 21 - "Return Model Ablation"
Cohesion: 0.16
Nodes (14): generate_ablation_report(), DataFrame, Path, Ablation: compare feature sets for investment-return prediction., In-sample correlation by model variant (monitoring only)., run_ablation(), load_catalyst_modeling_frame(), DataFrame (+6 more)

### Community 22 - "Expected CAR Models"
Cohesion: 0.26
Nodes (14): ExpectedCarBundle, _fit_conditional_car(), load_bundle(), _make_logistic(), _make_ridge(), persist_predictions(), predict_expected_car(), DataFrame (+6 more)

### Community 23 - "Market Expectations Features"
Cohesion: 0.22
Nodes (13): _apply_schema(), compute_all_market_features(), compute_features_for_catalyst(), _cum_return(), export_market_features_csv(), Connection, DataFrame, Path (+5 more)

### Community 24 - "Return Walk Forward"
Cohesion: 0.21
Nodes (12): export_predictions_csv(), generate_model_report(), Path, Generate model performance report for expected CAR., _persist_ledger(), DataFrame, Walk-forward OOS evaluation for expected CAR models., Deprecated alias — use assign_percentile_signals. (+4 more)

### Community 25 - "Holdout Evaluation"
Cohesion: 0.29
Nodes (13): _apply_exposure(), _bootstrap_corr_interval(), _fit_bundle(), generate_holdout_report(), DataFrame, ndarray, Path, Locked holdout evaluation (2019–2021) — run once after pipeline freeze. (+5 more)

### Community 26 - "Local Price Adapter"
Cohesion: 0.27
Nodes (6): _empty_frame(), LocalCsvAdapter, DataFrame, Path, Local CSV price adapter for delisted tickers (Polygon/CRSP exports)., Read daily OHLCV from data/external/prices/{TICKER}.csv. Expected columns…

### Community 27 - "Catalyst Ranking Export"
Cohesion: 0.24
Nodes (9): date, export_rankings(), format_decomposition(), DataFrame, Path, Series, rank_catalysts(), Rank catalysts by exposure-adjusted expected CAR. (+1 more)

### Community 28 - "Short Modeling Dataset"
Cohesion: 0.20
Nodes (8): load_short_edge_frame(), DataFrame, Path, Series, Enriched catalyst dataset for short-edge validation., James-Stein style shrinkage toward global mean for small samples., One row per priced catalyst with exposure, market, trial, and outcome fields., shrinkage_mean()

### Community 29 - "Trading Signal Assignment"
Cohesion: 0.29
Nodes (7): assign_fixed_signals(), assign_percentile_signals(), classify_signal_from_percentile(), DataFrame, Shared trade signal classification for walk-forward and ranking., Assign cross-sectional percentile signals within each test_year group., Fixed absolute thresholds (legacy).

### Community 30 - "GitHub Candidate Import"
Cohesion: 0.43
Nodes (6): filter_github_candidates(), import_github_pilot(), DataFrame, Path, Import a filtered pilot batch of GitHub EventsStockPrices candidates., write_pilot_import_yaml()

### Community 31 - "Pipeline Compliance Audit"
Cohesion: 0.52
Nodes (6): AuditCheck, generate_audit_report(), Path, Verify stock-picking pipeline deliverables against objective requirements., run_pipeline_audit(), summarize_audit()

### Community 32 - "Return Modeling Dataset"
Cohesion: 0.40
Nodes (5): Build catalyst-level modeling dataset from DB., Map feature set name to column list for expected CAR models., Return (p_success_features, car_features). Trial design informs P(success);…, resolve_feature_cols(), resolve_split_feature_cols()

## Knowledge Gaps
- **1 isolated node(s):** `PriceBar`
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `project_root()` connect `Market Data Operations` to `Short Walk Forward`, `Clinical Trial Cohorts`, `Catalyst Event Studies`, `Feature Matrix Prediction`, `Trial Design Analysis`, `Short Scoring Baselines`, `Market Data Validation`, `Ticker Resolution Seeding`, `Preclinical Leakage Repair`, `GitHub Catalyst Events`, `Market Model Returns`, `Point-in-Time Fundamentals`, `Delisted Price Recovery`, `Pipeline Trade Ledger`, `Company Exposure Controls`, `Return Model Ablation`, `Market Expectations Features`, `Return Walk Forward`, `Holdout Evaluation`, `Local Price Adapter`, `Short Modeling Dataset`, `GitHub Candidate Import`, `Pipeline Compliance Audit`?**
  _High betweenness centrality (0.428) - this node is a cross-community bridge._
- **Why does `main()` connect `Pipeline Trade Ledger` to `Market Data Operations`, `Short Walk Forward`, `Clinical Trial Cohorts`, `Catalyst Event Studies`, `Trial Design Analysis`, `Market Data Validation`, `Ticker Resolution Seeding`, `Preclinical Leakage Repair`, `GitHub Catalyst Events`, `PubMed Literature Backfill`, `Point-in-Time Fundamentals`, `Delisted Price Recovery`, `Backtest Parameter Grid`, `Company Exposure Controls`, `Return Model Ablation`, `Expected CAR Models`, `Market Expectations Features`, `Return Walk Forward`, `Holdout Evaluation`, `Catalyst Ranking Export`, `GitHub Candidate Import`, `Pipeline Compliance Audit`?**
  _High betweenness centrality (0.319) - this node is a cross-community bridge._
- **Why does `run_short_edge_validation()` connect `Short Walk Forward` to `Market Data Operations`, `Delisted Price Recovery`, `Pipeline Trade Ledger`, `Company Exposure Controls`, `Short Modeling Dataset`?**
  _High betweenness centrality (0.173) - this node is a cross-community bridge._
- **Are the 78 inferred relationships involving `project_root()` (e.g. with `apply_announcement_overrides()` and `_load_overrides()`) actually correct?**
  _`project_root()` has 78 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `main()` (e.g. with `generate_backtest_grid_report()` and `run_slippage_grid()`) actually correct?**
  _`main()` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `run_stock_picking_pipeline()` (e.g. with `main()` and `generate_backtest_grid_report()`) actually correct?**
  _`run_stock_picking_pipeline()` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `load_yaml()` (e.g. with `generate_coverage_report()` and `main()`) actually correct?**
  _`load_yaml()` has 22 INFERRED edges - model-reasoned connections that need verification._