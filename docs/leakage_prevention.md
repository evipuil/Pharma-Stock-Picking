# Leakage Prevention Rules

Look-ahead bias destroys prospective validity. This document defines enforceable rules and automated checks.

---

## Core definition

For each program:

```
t0 = earliest publicly documented Phase II start OR first-patient-dosed (FPI)
     among authoritative sources (see program_t0 table)
```

**Feature cutoff:** A record is **eligible** for model features only if:

```
effective_public_date(record) <= t0
```

where:

```
effective_public_date = MIN(
    publication_date,
    online_first_date,      -- if earlier than publication_date
    trial_registration_date -- for CT.gov features used as inputs
)
```

**Exception:** `company_announcement_date` used only when it precedes t0 and no scholarly date exists.

---

## Date field priority by source type

| Source | Primary date | Fallback |
|--------|--------------|----------|
| PubMed | `PubDate` / epub | Entrez date (**do not use** for features — epub only) |
| Crossref | `published-print`, `published-online` | issued |
| PMC | Same as PubMed | — |
| CT.gov trial | `StartDate`, `PrimaryStartDate` | `FirstPostDate` for registry only |
| SEC filing | Filing acceptance datetime → date | — |
| Press release | Announcement datetime → date | — |

**Rule:** Never use Entrez/Indexed date alone for literature eligibility — it reflects database indexing, not public disclosure.

---

## Forbidden leakage paths

| # | Violation | Mitigation |
|---|-----------|------------|
| L1 | Animal paper published after t0 in features | Filter on `effective_public_date` |
| L2 | CT.gov **results** or updated enrollment after t0 | Results fields → outcome tables only |
| L3 | Using Phase III outcome to label Phase II features in same row | Separate outcome_level rows |
| L4 | Stock returns before t0 used as features for trial success model | Returns only in event study targets |
| L5 | Including literature found via citation from post-t0 review | Search protocol frozen at t0 simulation |
| L6 | Training on 2019 programs to predict 2015 | Temporal split enforcement |
| L7 | Same program in train and test | GroupKFold by program_id |
| L8 | Imputing missing efficacy from later publications | Mark missing; no backfill |
| L9 | NLP model trained on post-t0 abstracts | NLP training corpus date-filtered |
| L10 | `pts_composite` fitted on full cohort including test | Fit PTS weights on train only |

---

## Literature search protocol (prospective simulation)

At data collection, document:

1. **Search date** (should ideally be simulated as t0, not today's date)
2. **Query terms** (drug synonyms, target, indication)
3. **Databases searched**
4. **Filters applied** (`effective_public_date <= t0`)

Store search log in `source_records` with `source_type = 'MANUAL'` and JSON in `raw_storage_path`.

---

## Automated leakage checks

Implemented in `src/validation/leakage.py`:

### Check 1: `publication_after_t0`

```python
FOR each animal_study linked to program:
    ASSERT publication.effective_public_date <= program.t0_date
```

### Check 2: `trial_results_before_features`

```python
ASSERT trial.results_first_posted_date is NOT used in feature engineering tables
```

### Check 3: `outcome_not_in_features`

```python
ASSERT no trial_outcomes columns joined to X except in y label table for supervised fit
```

### Check 4: `prediction_timestamp`

```python
FOR prospective predictions:
    ASSERT prediction_made_at <= t0_date
```

### Check 5: `market_data_event_alignment`

```python
FOR event study features (pre-event run-up as P_market v2):
    ASSERT feature_date < event_date
FOR trial success model:
    ASSERT no post-event returns in X
```

### Check 6: `temporal_split_integrity`

```python
ASSERT all train program t0_year <= max_train_year
ASSERT all test program t0_year >= min_test_year
```

### Check 7: `cross_program_deduplication`

```python
ASSERT no duplicate primary_nct_id across splits with different labels
```

All results logged to `leakage_audit_log`. Programs failing any hard check are excluded from `v_programs_prospective` until resolved.

---

## Soft warnings (review queue)

- Literature within **30 days before t0** (publication lag vs trial start)
- t0 source disagreement >14 days between CT.gov and press release
- Online-first date missing when print date is after t0
- Animal study in review article only (secondary source)

---

## Feature table materialization

Build `data/processed/features_prospective.parquet` via single pipeline:

```
raw → interim (all dates preserved) → leakage filter → processed
```

**Never** edit processed tables manually without audit trail.

---

## Event study separation

| Component | Timing |
|-----------|--------|
| P_model | Estimated using data ≤ t0 |
| Event date | Phase II readout announcement |
| CAR | Returns around event date |
| P_market (v2) | Estimated using prices ≤ event_date - 1 |

Scientific Edge = P_model − P_market must not use any information after t0 in P_model, or after pre-event window in P_market.

---

## Review cadence

- Run full leakage audit on every data refresh
- Re-audit when t0 or publication links change
- Version control `aggregation_rule_version` and `labeling_rule_version`
