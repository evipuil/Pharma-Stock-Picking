# Wave 1 Pipeline Run Summary

**Date:** 2026-08-19  
**Command:** `python -m src.cli run-all`

## Programs loaded (5/5)

| ID | Drug | NCT | t0 | Pre-t0 pubs | clinical_success |
|----|------|-----|-----|-------------|------------------|
| C014 | epacadostat | NCT02178722 | 2014-07-17 | 2 | 1 |
| C009 | sacituzumab govitecan | NCT01631552 | 2012-12-17 | 19 | 1 |
| C011 | tivozanib | NCT01297244 | 2011-01-01 | 1 | 1 |
| C007 | neratinib | NCT01008150 | 2010-10-01 | 8 | 1 |
| C005 | rucaparib | NCT01891344 | 2013-10-30 | 2 | 1 |

## Leakage audit

**10/10 checks passed** (t0 defined + publication dates ≤ t0 for all animal-study links)

## Exploratory analysis

- **n_programs:** 5
- **success_rate:** 100% (all Wave 1 manually adjudicated as Phase II successes — add failure programs in Wave 2 for modeling)
- **Brier (marginal):** 0.0 (degenerate — no failures in cohort)
- **Brier (Wong baseline ~29%):** 0.513
- **Mean pre-t0 publications:** 4.6 per program
- **Logistic regression:** skipped (need outcome variation + more N)

## Event study

| Program | Ticker | Event date | CAR [-1,+1] |
|---------|--------|------------|-------------|
| C014 | INCY | 2016-06-01 | +3.4% |
| C007 | PBYI | 2014-12-10 | +1.9% |

**Delisted tickers (no yfinance history):** IMMU, AVEO, CLVS — requires CRSP/Polygon historical data for full event study.

## Raw data cached

- `data/raw/ctgov/NCT*.json` — 5 trial records
- `data/raw/pubmed/C*_pubmed.json` — literature search results
- `data/interim/wave1_bundles.json` — full program bundles
- `data/processed/research.db` — SQLite database
- `data/processed/exploratory_report.json`
- `data/processed/programs_analysis.csv`
- `data/processed/event_study_results.csv`

## Next steps

1. Add 10–15 **failure** programs (Wave 2) for balanced modeling
2. Manual feature extraction on 32 animal-study placeholder rows
3. Historical price data for delisted tickers
4. Transcribe Wong (2019) supplementary PoS tables (replace placeholders)
