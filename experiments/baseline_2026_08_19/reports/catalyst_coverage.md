# Catalyst Dataset Coverage Report

**Generated from:** `C:\Users\eshan\Desktop\StockPicking\data\processed\research.db`

## Cohort size

| Metric | Count | Target |
|--------|------:|-------:|
| Catalysts | 112 | ≥100 (Phase A) |
| Underlying programs | 112 | — |
| With announcement date | 112 | — |
| With event study CAR | 107 | — |
| With market features | 107 | — |
| With trial design features | 112 | — |
| Preclinical evidence found | 65 | — |
| No preclinical evidence | 47 | — |

## Outcome mix

outcome_category  n
EFFICACY_FAILURE 24
  SAFETY_FAILURE  3
         SUCCESS 63
         UNKNOWN 22

## Event study: CAR [-1,+1] market model by outcome

 clinical_success  n  mean_car  median_car      std
                0 27 -0.104766   -0.008537 0.245388
                1 80 -0.002656    0.004521 0.051205

## Known blockers

### Price data
- **yfinance**: Active tickers only; many delisted biotech symbols return empty history
- **Delisted examples**: IMMU, AVEO, CLVS, LOXO, CELG, SNTA, CYTR — require Polygon or CRSP
- **Adapter stubs**: `PolygonAdapter` (needs `POLYGON_API_KEY`), `CRSPAdapter` (needs WRDS)

### Announcement timing
- Most catalysts use `announcement_timing=UNKNOWN` until SEC/press release parsing is built
- Executable backtest uses conservative prior-close cutoff when timing unknown

### Fundamentals
- `point_in_time_fundamentals` schema ready; SEC EDGAR ingestion not yet implemented

## Next stages

1. Stage 5: Point-in-time market + fundamentals features
2. Stage 6–7: Indication-level P(success) and E(CAR|success/failure) models
3. Stage 9: Walk-forward backtester with OOS ledger
