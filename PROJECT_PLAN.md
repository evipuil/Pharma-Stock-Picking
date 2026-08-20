# Preclinical-to-Clinical Translation & Biotech Mispricing Research Pipeline

## Executive summary

This project investigates whether **characteristics of preclinical animal evidence**—not merely raw efficacy—can **prospectively** predict human clinical-trial success beyond conventional development-stage baselines, and whether discrepancies between model-implied and market-implied success probabilities identify **mispricing** in publicly traded biotech/pharma sponsors.

**Unit of observation:** `drug × indication × development stage` (program), not drug alone.

**Primary scientific framing (avoid naive correlation):**

> Can the rigor, biological validity, replication, PK/PD relevance, and quantitative outcomes of preclinical animal evidence prospectively improve calibrated prediction of human clinical-trial success beyond phase/indication/modality baselines, and does that information reveal evidence that financial markets under- or overprice?

A strong negative result (e.g., effect size alone is uninformative but translational-quality variables add value) is scientifically valuable.

---

## Research questions

| # | Question | MVP scope | Full scale |
|---|----------|-----------|------------|
| RQ1 | Can pre-t0 animal evidence predict clinical success? | Phase II oncology, logistic baseline | Multi-indication, multi-model |
| RQ2 | Which animal-study characteristics are most predictive? | Univariate + ablation | SHAP, hierarchical models |
| RQ3 | Does a preclinical model beat historical PoS baselines? | Wong/Siah/Lo + BIO benchmarks | Calibrated ensembles |
| RQ4 | Does P_model predict abnormal returns at readouts? | Event study [-1,+1], [0,+5] | Options-implied P_market |
| RQ5 | Does P_model − P_market identify mispricing? | Version 1 only (P_model → CAR) | Version 2 (explicit P_market) |

---

## Repository map

```
StockPicking/
├── PROJECT_PLAN.md              ← this file
├── README.md
├── requirements.txt
├── pyproject.toml
├── configs/
│   ├── cohort_mvp.yaml          ← MVP inclusion filters & program IDs
│   ├── data_sources.yaml        ← API endpoints, rate limits
│   ├── feature_sets.yaml        ← ablation feature groups
│   └── modeling.yaml            ← train/val/test splits, model hyperparams
├── data/
│   ├── raw/                     ← immutable downloads (gitignored)
│   ├── interim/                 ← parsed but unvalidated
│   ├── processed/               ← leakage-checked, analysis-ready
│   └── external/                ← benchmark PoS tables, sector indices
├── docs/
│   ├── schema.md                ← relational DB / table definitions
│   ├── inclusion_exclusion_criteria.md
│   ├── outcome_labeling_rules.md
│   ├── leakage_prevention.md
│   ├── data_sources.md
│   ├── mvp_cohort.md            ← 20–50 program selection & status
│   ├── statistical_analysis_plan.md
│   ├── automation_vs_manual.md
│   └── data_dictionary.md
├── src/
│   ├── literature/              ← PubMed, Crossref, Europe PMC
│   ├── clinical_trials/         ← ClinicalTrials.gov API
│   ├── preclinical/             ← animal-study tables, PTS components
│   ├── market_data/             ← prices, event dates, confounders
│   ├── feature_engineering/     ← aggregation, t0 cutoff enforcement
│   ├── models/                  ← baselines, ML, calibration
│   ├── event_study/             ← CAR, market model
│   └── validation/              ← leakage checks, temporal splits
├── notebooks/                   ← exploratory only; production logic in src/
├── tests/
└── sql/
    └── schema.sql               ← DDL for SQLite/PostgreSQL
```

---

## Phase plan

### Phase 0 — Foundation (current milestone)

- [x] Project plan, schema, labeling rules, leakage policy
- [x] Repository skeleton, configs, data dictionary template
- [ ] Manual MVP cohort curation (20–50 programs)
- [ ] SQLite database initialized from schema

### Phase 1 — MVP data collection (20–50 programs)

For each program:

1. Identify primary Phase II trial → NCT ID
2. Define `t0` (first-patient-dosed or trial start, documented)
3. Label clinical outcome(s) per `docs/outcome_labeling_rules.md`
4. Collect all pre-t0 animal literature (PubMed/PMC/manual)
5. Extract features (semi-manual); store provenance
6. Build relational tables; run leakage audit
7. Exploratory stats + historical-rate baseline + logistic regression
8. Document missing-data patterns and feasibility

**Do not scale** until schema, labeling, and leakage checks are validated.

### Phase 2 — Modeling & baselines

- Historical PoS baselines (Wong et al., BIO/Informa)
- Ablation feature sets (see `configs/feature_sets.yaml`)
- Temporal train/validation split
- Calibration-first evaluation (Brier, calibration slope)

### Phase 3 — Financial event study

- Reproduce Singh et al.–style baseline event study
- Test P_model → CAR association
- Control for market cap, portfolio concentration, sector

### Phase 4 — P_market & scientific edge

- Version 2 market-implied probability (analyst, run-up, options where available)
- Direct test: `Scientific Edge = P_model − P_market`

### Phase 5 — NLP extraction (optional scale)

- Deterministic parsing → LLM-assisted extraction with verification queue
- Never silently accept LLM values

---

## Information cutoff (`t0`) — summary

For every program, define:

```
t0 = Phase II trial start date OR first-patient-dosed date
     (whichever is earlier and publicly documented)
```

**Hard rule:** No feature, publication, trial registration, or price signal used in modeling may have a public timestamp **after t0**, unless explicitly designated as a **post-t0 outcome** or **financial target**.

Full rules: `docs/leakage_prevention.md`

---

## Key literature integration

| Reference | Use in pipeline |
|-----------|-----------------|
| Ferreira et al. 2019 (FIMD) | Translational validity variables |
| Percie du Sert et al. 2020 (ARRIVE 2.0) | Reporting/rigor checklist fields |
| Landis et al. 2012 | Randomization, blinding, sample size, exclusions |
| van der Worp et al. 2010 | Background / construct validity framing |
| Van Norman 2019 | Safety translation limitations |
| Mak et al. 2014 | Oncology-specific translation context |
| Berg et al. 2024 | Empirical translation factor priors |
| Wong, Siah & Lo 2019 | Phase/indication/modality PoS baselines |
| BIO/Informa/QLS 2011–2020 | Industry benchmark rates |
| Singh et al. 2022 | Event-study design benchmark |
| Hwang et al. 2013 | Event-study replication |
| Budennyy et al. 2023 | ML + asymmetric market response |

---

## Deliverables by milestone

| Milestone | Deliverable | Success criterion |
|-----------|-------------|-------------------|
| M0 | Schema + docs + repo | Reviewable, reproducible structure |
| M1 | 20–50 program DB populated | ≥80% core fields; leakage audit pass |
| M2 | Baseline + logistic model | Beats naive 50% on PR-AUC; calibration documented |
| M3 | Ablation results | Preclinical blocks vs baseline quantified |
| M4 | Event study baseline | CAR sign/magnitude consistent with literature direction |
| M5 | P_model → CAR test | Pre-specified hypothesis test with CIs |

---

## Risk register

| Risk | Mitigation |
|------|------------|
| Look-ahead bias | Automated leakage checks; dual date fields; audit log |
| Survivorship bias | Include terminated/failed programs explicitly |
| Label ambiguity | Multi-label outcomes; adjudication log; `unknown` category |
| Sparse animal data | Document coverage; don't impute efficacy silently |
| MVP too small for ML | Start logistic; bootstrap CIs; hold complex models for N>100 |
| Historical options/analyst data gaps | Version 1 P_market proxy; mark paid-only sources |
| LLM extraction errors | Verification queue; source sentences stored |
| Same-program train/test leakage | Group splits by `program_id` |

---

## Governance

- **Data provenance:** Every derived field links to `source_records` row(s)
- **Versioning:** Git for code; DVC or manifest hashes for raw data (optional Phase 1)
- **Reproducibility:** `configs/` pin cohort and splits; random seeds in `modeling.yaml`
- **Manual review:** Fields in `automation_vs_manual.md` flagged `requires_validation`

---

## Next actions (immediate)

1. Review `docs/schema.md` and `sql/schema.sql`
2. Curate MVP list in `docs/mvp_cohort.md` / `configs/cohort_mvp.yaml`
3. Run ClinicalTrials.gov fetch for candidate NCT IDs → `data/raw/`
4. Initialize SQLite: `python -m src.cli init-db` (after implementation)
5. Begin manual feature extraction template for first 5 programs

See linked docs for detail on each design decision.
