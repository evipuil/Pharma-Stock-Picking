# Catalyst Dataset Coverage Report

**Generated from:** `C:\Users\eshan\Desktop\StockPicking\data\processed\research.db`

## Cohort size

| Metric | Count | Target |
|--------|------:|-------:|
| Catalysts | 122 | ≥100 (Phase A) |
| Underlying programs | 121 | — |
| With announcement date | 122 | — |
| With event study CAR | 115 | — |
| With market features | 107 | — |
| With trial design features | 112 | — |
| Preclinical evidence found | 65 | — |
| No preclinical evidence | 57 | — |

## Outcome mix

outcome_category  n
EFFICACY_FAILURE 31
  SAFETY_FAILURE  3
         SUCCESS 66
         UNKNOWN 22

## Event study: CAR [-1,+1] market model by outcome

 clinical_success  n  mean_car  median_car      std
              0.0 28 -0.120216   -0.009098 0.269563
              1.0 83 -0.002202    0.004347 0.050713

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
