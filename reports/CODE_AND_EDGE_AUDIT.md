# Code and Market-Edge Audit

Date: 2026-08-21

## Bottom line

The repository is a thoughtful biotech catalyst research system, but it does not yet
demonstrate a robust market-beating strategy. After strict source-timestamp filtering and
event-session correction, the general long/short result remains economically weak, while the
development-only short model is promising but has only 15 selected trades.

## System understood

1. Catalyst, trial, publication, ticker, price, and SEC data are normalized into SQLite.
2. Point-in-time market, preclinical, and company-exposure features are assembled. Historical
   trial-design fields are excluded when no contemporaneous CT.gov snapshot exists.
3. Expanding-window models estimate failure probability and conditional event-window CAR.
4. Expected CAR is converted into exposure-adjusted long/short rankings and trading costs.
5. Event studies, walk-forward ledgers, baselines, ablations, holdouts, and robustness reports
   evaluate the research hypothesis.

The strongest architectural idea is separating scientific success probability from the market
reaction conditional on success or failure. The main weakness is evidence quality: the catalyst
sample is small, historical failures are harder to price, and several company/trial fields are
heuristic or not fully snapshot-versioned.

## Corrected empirical results

### General long/short backtest

- Declared OOS signals: 37
- Mean abnormal return per trade after 25 bps slippage per leg: +0.47%
- 95% bootstrap interval: approximately -4.61% to +6.22%
- Long mean: -2.87%
- Short mean: +6.64%

The prior positive result included eight rows labeled `NO TRADE` that were converted into
positions by a fallback threshold. That fallback is now disabled by default.

### Development-only short strategy

- Development OOS rows: 59
- Year-local top-quintile shorts: 15
- Mean abnormal short return after modeled costs: +17.66%
- Ordinary bootstrap 95% interval: +4.01% to +33.63%
- Year-block bootstrap 95% interval: +0.14% to +38.47%
- Permutation p-value: 0.0185
- High-dependency heuristic mean: +11.83% on 25 trades
- Verdict: **PROMISING BUT UNVALIDATED EDGE** (7/8 criteria; sample-size criterion fails)

The 2022+ period appeared in earlier repository artifacts, so it is not a pristine final
holdout. It is quarantined from the regenerated development report; a new prospective holdout
is required.

## Improvements implemented

- Select top-percentile trades independently inside each OOS test year.
- Exclude the configured legacy holdout from routine short-model validation by default.
- Freeze tail-risk fallback magnitude and class probability from training data only.
- Freeze general conditional-CAR fallbacks and Wong-baseline calibration from training rows only.
- Execute only explicit walk-forward signals; legacy threshold fallback is opt-in.
- Stop applying company-dependency exposure twice in the backtest.
- Annualize event-trade Sharpe by observed trade frequency instead of `sqrt(252)`.
- Include year-block bootstrap uncertainty in the success criteria and report.
- Make live rankings prospective by default and fail closed when the model or strict training
  provenance is missing.
- Remove realized outcomes from the ranking output.
- Record the actual final market date used instead of labeling features with the requested cutoff.
- Null market, exposure, and trial feature families that cannot be verified at the trading cutoff.
- Add a point-in-time audit covering market, exposure, SEC filing, CT.gov posting, and snapshot dates.
- Preserve immutable timestamped CT.gov snapshots for all future fetches.
- Anchor event day zero to the first trading session on/after the announcement.
- Reclassify the existing 2019–2021 and 2022+ evaluations as legacy, non-pristine periods.
- Keep all-missing features stable through scikit-learn imputers.
- Add regression tests for holdout isolation, fold-local selection, tail-risk leakage, signal
  execution, exposure scaling, and ranking safety.

## Highest-priority next research

1. Freeze the current methodology and designate a genuinely new prospective holdout.
2. Expand catalysts independently of outcomes until there are at least 100–200 OOS short
   trades, with deliberate recovery of delisted failures.
3. Replace ticker-list company-dependency heuristics with point-in-time market cap, enterprise
   value, cash runway, revenue, and lead-asset concentration.
4. Recover dated historical AACT/ClinicalTrials.gov snapshots. New fetches are now versioned, but
   current records cannot reconstruct what the registry showed at old event dates.
5. Add point-in-time borrow availability, borrow fee, ADV, spread, and overlap-aware portfolio
   capacity before treating event CAR as executable P&L.
6. Test whether the model adds residual value beyond the high-dependency heuristic, with all
   variants declared before the new holdout begins.
7. Track every attempted model/strategy and apply multiple-testing-aware statistics such as a
   deflated Sharpe ratio or probability-of-backtest-overfitting analysis.

## Verification

- Test suite: 61 passed
- Lint on all changed source and test files: passed
- Graph audit: 800 nodes, 1,493 edges, 55 communities
- Graph health: passed with no dangling, missing, self-loop, duplicate, or collapsed edges
- Graph query benchmark: approximately 12.8x fewer tokens than reading the full corpus

No return is guaranteed, and the current sample is not sufficient for live capital allocation.
