# Clinical Outcome Labeling Rules

**Version:** v1.0  
**Primary label (MVP):** `clinical_success` at **Phase II** level

---

## Primary outcome definition

```
clinical_success = 1  IF the Phase II program met its prespecified primary efficacy endpoint
                      AND development continued toward Phase III or registration
                      on the basis of that efficacy readout (not solely commercial partnership)

clinical_success = 0  OTHERWISE
```

**Important:** `clinical_success = 0` includes safety failures, efficacy failures, inconclusive results, and programs that met endpoint but were abandoned for commercial reasons — with those subtypes recorded separately.

---

## Outcome dimensions (store all; don't collapse silently)

| Field | Type | Definition |
|-------|------|------------|
| `met_primary_endpoint` | 0/1/NULL | Statistical/clinical endpoint met per sponsor or FDA-aligned readout |
| `advanced_to_phase3` | 0/1/NULL | Sponsor initiated Phase III or registrational study for same indication |
| `regulatory_approval` | 0/1/NULL | FDA/EMA approval for same indication (long-run label) |
| `technical_failure` | 0/1 | Failed efficacy, futility, or statistically negative primary |
| `safety_failure` | 0/1 | Terminated primarily for toxicity/DLT/unacceptable AE profile |
| `commercial_discontinuation` | 0/1 | Stopped despite possible signal: business, competitive, pipeline reprioritization |
| `outcome_unknown` | 0/1 | Insufficient public disclosure to adjudicate |

**Constraint:** At most one of `technical_failure`, `safety_failure`, `commercial_discontinuation` should be 1 for a given outcome_level; if multiple apply, document hierarchy in notes.

---

## Adjudication hierarchy (when narratives conflict)

1. **Regulatory label / FDA correspondence** (if applicable)
2. **Peer-reviewed publication** of trial results
3. **CT.gov results posting** (primary outcome field)
4. **Company press release / 8-K / earnings call transcript**
5. **Analyst reports** (lowest weight; never sole source)

---

## Phase II success — operational rules

### Count as success (`clinical_success = 1`)

- Primary endpoint met (p < alpha or predefined clinical benefit) **and** sponsor publicly confirms advancement
- Phase II registrational trial leading directly to NDA (single-trial approval path) with positive readout
- Conditional approval path initiated on basis of Phase II data (document explicitly)

### Count as failure (`clinical_success = 0`, `technical_failure = 1`)

- Primary endpoint not met
- Study stopped at interim for futility
- Sponsor states trial "did not meet primary endpoint"
- Numerically positive trend but sponsor declares failure to advance

### Safety failure (`clinical_success = 0`, `safety_failure = 1`)

- Early termination citing DLTs, excess mortality, or unacceptable safety
- FDA clinical hold leading to permanent discontinuation of that indication

### Commercial discontinuation (`clinical_success = 0`, `commercial_discontinuation = 1`)

- Endpoint met or trend positive, but sponsor exits for portfolio/competitive reasons
- Program out-licensed with no advancement by original sponsor (case-by-case)
- **Do not** label as biological failure in primary analysis; include sensitivity analysis excluding these

### Unknown (`outcome_unknown = 1`)

- Trial terminated with no reason and no results posted >3 years after completion
- Conflicting sources without resolution
- **Exclude from primary modeling** or include with imputation sensitivity (document choice)

---

## Phase III & regulatory labels (secondary outcomes)

Stored in separate `trial_outcomes` rows with `outcome_level = 'PHASE3'` or `'REGULATORY'`.

| Label | Definition |
|-------|------------|
| Phase III success | Primary endpoint met in confirmatory trial |
| Regulatory approval | First approval for indication (FDA or EMA) |
| CRL / rejection | Complete response letter or negative opinion |

---

## Outcome date

`outcome_date` = first public date when primary result direction became knowable:

- Press release timestamp (date only if intraday unavailable)
- CT.gov results_first_posted_date
- Publication epub date

**Not** conference presentation date unless that was first public disclosure (document if used).

---

## Examples (illustrative patterns — verify per program)

| Pattern | clinical_success | Other flags |
|---------|------------------|-------------|
| Positive PFS, Phase III started | 1 | advanced_to_phase3=1 |
| ORR met but OS immature, continued | 1 | notes on maturity |
| Missed primary, program killed | 0 | technical_failure=1 |
| Excess deaths in arm | 0 | safety_failure=1 |
| Positive but partner returns rights, shelved | 0 | commercial_discontinuation=1 |
| Terminated "strategic reasons", no data | 0 | outcome_unknown=1 |

---

## Labeling workflow

1. Auto-ingest CT.gov `resultsSection` and status fields
2. Manual adjudication spreadsheet → `trial_outcomes` row
3. Second reviewer for first 10 programs; then 20% audit sample
4. Store `labeling_rule_version` on every row

---

## Sensitivity analyses (pre-specified)

1. **Strict:** Exclude `commercial_discontinuation` and `outcome_unknown`
2. **Endpoint-only:** `met_primary_endpoint` as label (ignore advancement)
3. **Advancement-only:** `advanced_to_phase3` as label
4. **Long-run:** `regulatory_approval` as label (survival / competing risks later)

---

## What we do NOT do

- Label all `TERMINATED` CT.gov statuses as failure
- Infer success from stock price reaction alone
- Use post-hoc subgroup claims as primary success
- Backfill labels from Wikipedia without primary source
