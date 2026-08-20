# Stock-Picking System Architecture

**Objective:** Predict **expected abnormal return** at the catalyst level:

```
Expected CAR = P(success|info≤t) × E(CAR|success) + (1−P(success)) × E(CAR|failure)
```

Scientific probability alone is insufficient — a high-P(success) drug can be a bad long if success is priced in.

---

## Reusable modules (preserve, do not rebuild)

| Existing module | Path | Reuse for |
|-----------------|------|-----------|
| SQLite + schema | `sql/schema.sql`, `src/db/` | Extend with catalyst tables |
| CT.gov client | `src/clinical_trials/` | Trial design, enrollment, outcomes |
| PubMed client | `src/literature/` | Preclinical (optional per catalyst) |
| Leakage audit | `src/validation/leakage.py` | Extend to catalyst cutoff |
| Program curation | `src/pipeline/batch_expand_cohort.py` | Seed catalyst calendar |
| Feature matrix | `src/feature_engineering/build_matrix.py` | Refactor to catalyst-level |
| Models / Wong PoS | `src/models/`, `data/external/wong2019_pos_rates.csv` | P(success) baselines |
| Event study CAR | `src/event_study/car.py` | Multi-window catalyst CAR |
| yfinance prices | `src/market_data/prices.py` | Active-ticker subset |
| CLI | `src/cli.py` | Add catalyst/backtest commands |

**Preserved:** 38-program cohort, 88 verified animal studies, leakage audits, tests, all existing CLI commands.

---

## Unit of analysis change

| Before | After |
|--------|-------|
| `program_id` (drug-level) | `catalyst_id` = drug × indication × trial × catalyst event |
| Same-drug programs share features | Indication-specific features; link to `program_id` optionally |
| `program_financial_events` (5 rows) | `catalysts` table with announcement timing |

Each catalyst row stores:
- Scientific context (drug, indication, NCT, phase, biomarker, line of therapy)
- Market context (ticker at event, trading cutoff)
- Outcome (success/failure/mixed)
- Event study results (multiple windows, SPY + XBI benchmarks)

---

## New module layout

```
src/
├── catalysts/           # Calendar, migration, curation, announcement timing
├── market_data/
│   ├── adapters/        # PriceAdapter interface (yfinance, Polygon stub, CRSP stub)
│   └── history.py       # Cache OHLCV to data/market_history/
├── event_study/
│   ├── car.py           # (existing) market model
│   └── catalyst_study.py # Multi-window CAR for all catalysts
├── market_expectations/ # Stage 5: pre-catalyst price features
├── fundamentals/        # Stage 5: point-in-time SEC fundamentals
├── return_models/       # Stage 7: E(CAR|success), E(CAR|failure)
├── backtest/            # Stage 9: walk-forward ledger
├── portfolio/           # Stage 9: sizing, constraints
└── ranking/             # Stage 12: rank-catalysts CLI
```

---

## Database extensions

Applied via `sql/schema_catalysts.sql` (additive, non-destructive):

| Table | Purpose |
|-------|---------|
| `catalysts` | Primary unit: catalyst_id, program link, announcement, outcome |
| `catalyst_ticker_history` | Point-in-time ticker mapping (changes, M&A) |
| `market_bars_daily` | OHLCV + adj_close (replaces sparse `market_data_daily`) |
| `catalyst_event_study` | CAR by window × benchmark |
| `catalyst_trading_cutoffs` | Executable entry/exit dates from announcement timing |
| `asset_exposure` | company_dependency score (Stage 5+) |
| `point_in_time_fundamentals` | Cash, debt, market cap at cutoff (Stage 5+) |

View: `v_catalysts_prospective` joins catalyst + outcome + latest leakage.

---

## Price data strategy

```
PriceAdapter (abstract)
├── YFinanceAdapter      # Active + recent delisted (limited); no survivorship fix
├── PolygonAdapter       # Implemented — requires POLYGON_API_KEY; auto-fallback from yfinance
├── EodhdAdapter         # Implemented — requires EODHD_API_KEY; delisted + active US equities
├── LocalCsvAdapter      # data/external/prices/{TICKER}.csv — Polygon/CRSP/EODHD exports
└── CRSPAdapter          # STUB — requires WRDS/CRSP license
```

**Benchmarks:** SPY (market), XBI (primary biotech), IBB (secondary).

Cache path: `data/market_history/{provider}/{ticker}.parquet`

**Known blockers documented in `reports/event_study.md`:**
- Delisted tickers (IMMU, AVEO, CLVS, LOXO, CELG) need CRSP/Polygon
- yfinance returns empty for many historical biotech symbols

---

## Announcement timing & executable backtest

Critical fields on `catalysts`:
- `announcement_timestamp` (UTC or US/Eastern)
- `announcement_timing`: `BMO` | `AMC` | `DURING` | `UNKNOWN`
- `trading_day_before` / `first_trading_day_after`

**Trading cutoff rule (default):**
- BMO: last close before announcement day
- AMC: close on announcement day
- DURING: prior close (conservative)
- UNKNOWN: prior close + flag low confidence

No same-day close entry after a BMO announcement.

---

## Cohort expansion phases

| Phase | Target N | Status |
|-------|----------|--------|
| Existing programs | 38 | ✅ in DB |
| Phase A | ≥100 catalysts | In progress — `configs/catalyst_candidates.yaml` |
| Phase B | ≥250 | Planned |
| Long-term | 500+ | Planned |

Inclusion does **not** require preclinical publications. Missingness features:
- `preclinical_evidence_found`
- `n_preclinical_publications`
- `publication_coverage_confidence`

---

## Event study specification (Stage 4)

**Estimation window:** trading days [-250, -30] relative to catalyst.

**Event windows:** `[-5,+5]`, `[-1,+1]`, `[0,+1]`, `[0,+5]`, `[0,+20]`

**Benchmarks per window:**
- Raw return
- Market-adjusted (SPY beta model)
- XBI-adjusted (sector beta model)
- Abnormal return (market model residual)

Stored in `catalyst_event_study` with provenance (`price_source`, `beta_estimation_start/end`).

---

## Walk-forward & holdout (Stage 9–11)

`configs/stock_picking.yaml`:
```yaml
holdout:
  final_locked:
    start_year: 2019
    end_year: 2021
walk_forward:
  initial_train_end_year: 2014
  step_years: 1
```

**Rule:** Final holdout never inspected until pipeline frozen.

**CLI:**
- `python -m src.cli audit-pipeline` — verify deliverables against objective
- `python -m src.cli run-stock-picking` — end-to-end pipeline orchestrator
- `python -m src.cli compute-fundamentals` — SEC EDGAR point-in-time fundamentals
- `python -m src.cli price-coverage` — delisted ticker audit
- `python -m src.cli walk-forward` — expanding-window OOS ledger
- `python -m src.cli holdout-eval` — locked 2019–2021 evaluation with bootstrap CIs
- `python -m src.cli ablation` — market vs preclinical vs Wong prior
- `python -m src.cli backtest` — trade P&L with slippage + bootstrap CIs
- `python -m src.cli backtest-grid` — slippage sensitivity + strategy variants
- `python -m src.cli rank-catalysts --as-of YYYY-MM-DD` — includes conformal CIs

---

## Deliverables map

| Deliverable | Path | Stage |
|-------------|------|-------|
| Catalyst registry | `data/catalysts.csv` | 2–3 |
| Price history | `data/market_history/` | 3 |
| Event study report | `reports/event_study.md` | 4 |
| OOS predictions | `data/out_of_sample_predictions.csv` | 9 |
| Trade ledger | `data/trade_ledger.csv` | 9 |
| Coverage report | `reports/catalyst_coverage.md` | 4 |
| Holdout evaluation | `reports/holdout_evaluation.md` | 11 |
| Ablation study | `reports/ablation_study.md` | 11 |
| Backtest report | `reports/backtest.md` | 9 |
| Backtest grid | `reports/backtest_grid.md` | 9 |
| Pipeline audit | `reports/pipeline_audit.md` | all |

---

## Execution stages

| Stage | Status |
|-------|--------|
| 1–4 Catalyst schema, N≥100, price adapter, event study | ✅ Complete |
| 5 Market features + exposure heuristics | ✅ Prototype |
| 6 Trial design features (CT.gov) | ✅ Implemented |
| 6–7 Expected CAR models + walk-forward | ✅ Prototype (split P/CAR features) |
| 9 Backtester + OOS ledger | ✅ Prototype |
| 11 Locked holdout + ablation | ✅ Implemented |
| 12 rank-catalysts CLI | ✅ Prototype |

**Remaining:** 5 post-2017 delisted names (CLVS, MRTX, SGEN, OMED) still need Polygon/CRSP; SEC fundamentals remain partial.

---

## Leakage invariants (tests required)

- No post-cutoff publications in features
- No post-cutoff trial results in P(success) features
- No post-cutoff fundamentals
- No post-cutoff prices as features (only for realized P&L)
- Announcement-time-aware execution dates
- Temporal train/test separation in walk-forward
