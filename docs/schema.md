# Relational Database Schema

## Design principles

1. **Program-centric:** `programs` is the anchor for drug × indication × stage
2. **Provenance-first:** every fact links to `source_records`
3. **Two-level preclinical data:** `animal_studies` (study-level) → `program_preclinical_features` (aggregated)
4. **Temporal integrity:** all ingested records store multiple date fields; `leakage_audit` validates t0 compliance
5. **Multi-outcome labels:** avoid collapsing heterogeneous failures into one binary without documentation

## Entity-relationship overview

```
companies ──< programs ──< clinical_trials
                │              │
                │              └──< trial_outcomes
                │
                ├──< program_t0
                ├──< program_preclinical_features
                ├──< program_financial_events
                └──< model_predictions

animal_studies ──< animal_study_features
       │
       └──> source_records (via study_source_links)

publications ──> source_records
benchmark_pos_rates (reference tables)
leakage_audit_log
extraction_review_queue
```

## Table definitions

### `companies`

Publicly traded sponsors.

| Column | Type | Description |
|--------|------|-------------|
| company_id | TEXT PK | Internal UUID |
| ticker | TEXT | Primary US ticker (e.g., `MRNA`) |
| cik | TEXT | SEC CIK if available |
| company_name | TEXT | Legal or common name |
| exchange | TEXT | NYSE, NASDAQ, etc. |
| is_biotech_sponsor | BOOLEAN | Diversified pharma vs biotech flag |
| market_cap_usd_at_t0 | REAL | **Nullable** — requires historical market data |
| cash_usd_at_t0 | REAL | **Nullable** — SEC 10-Q/10-K |
| portfolio_drug_count_at_t0 | INTEGER | **Manual/semi-auto** |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### `programs`

**Primary analytical unit:** drug × indication × development stage at t0.

| Column | Type | Description |
|--------|------|-------------|
| program_id | TEXT PK | Internal UUID |
| company_id | TEXT FK → companies | |
| drug_name | TEXT | INN or research code at t0 |
| drug_synonyms | TEXT | JSON array |
| indication | TEXT | Normalized indication (e.g., `NSCLC`) |
| indication_mesh | TEXT | MeSH term if mapped |
| modality | TEXT | mAb, small molecule, ADC, cell therapy, etc. |
| target | TEXT | e.g., `PD-1`, `KRAS G12C` |
| biomarker_strategy | TEXT | all-comers, PD-L1+, MSI-H, etc. |
| development_stage_at_t0 | TEXT | `PHASE2` (MVP) |
| primary_nct_id | TEXT FK | Lead Phase II trial |
| cohort_inclusion_date | DATE | When program entered MVP cohort |
| mvp_wave | TEXT | `wave_1`, `validation` |
| notes | TEXT | |

**Unique constraint:** `(drug_name, indication, development_stage_at_t0, primary_nct_id)`

### `program_t0`

Information cutoff definition (one row per program; versioned if revised).

| Column | Type | Description |
|--------|------|-------------|
| program_id | TEXT PK/FK | |
| t0_date | DATE | **Authoritative cutoff** |
| t0_definition | TEXT | `FIRST_PATIENT_DOSED` \| `TRIAL_START` \| `OTHER` |
| t0_source_type | TEXT | CT.gov, press release, SEC filing |
| t0_source_record_id | TEXT FK → source_records | |
| t0_rationale | TEXT | Human-readable justification |
| defined_by | TEXT | analyst ID |
| defined_at | TIMESTAMP | |

### `clinical_trials`

Trial metadata from ClinicalTrials.gov (+ manual supplements).

| Column | Type | Description |
|--------|------|-------------|
| nct_id | TEXT PK | e.g., `NCT01234567` |
| program_id | TEXT FK | |
| brief_title | TEXT | |
| phase | TEXT | `PHASE2`, `PHASE2/PHASE3`, etc. |
| study_type | TEXT | Interventional |
| condition | TEXT | Raw condition string |
| intervention | TEXT | |
| sponsor | TEXT | |
| collaborator | TEXT | |
| start_date | DATE | |
| primary_completion_date | DATE | |
| study_completion_date | DATE | |
| first_posted_date | DATE | Registry posting |
| results_first_posted_date | DATE | **Post-t0 outcome signal** |
| enrollment | INTEGER | |
| allocation | TEXT | Randomized, etc. |
| masking | TEXT | |
| primary_purpose | TEXT | Treatment |
| api_fetched_at | TIMESTAMP | |
| raw_json_path | TEXT | Path to raw API response |

### `trial_outcomes`

Multi-dimensional outcome labels (see `outcome_labeling_rules.md`).

| Column | Type | Description |
|--------|------|-------------|
| outcome_id | TEXT PK | |
| program_id | TEXT FK | |
| nct_id | TEXT FK | |
| outcome_level | TEXT | `PHASE2`, `PHASE3`, `REGULATORY` |
| clinical_success | INTEGER | 0/1 primary label for MVP |
| met_primary_endpoint | INTEGER | 0/1/NULL |
| advanced_to_phase3 | INTEGER | 0/1/NULL |
| regulatory_approval | INTEGER | 0/1/NULL |
| technical_failure | INTEGER | 0/1 |
| safety_failure | INTEGER | 0/1 |
| commercial_discontinuation | INTEGER | 0/1 |
| outcome_unknown | INTEGER | 0/1 |
| failure_reason_detail | TEXT | |
| outcome_date | DATE | When outcome became public |
| outcome_source_record_id | TEXT FK | |
| labeling_rule_version | TEXT | e.g., `v1.0` |
| adjudicated_by | TEXT | |
| adjudicated_at | TIMESTAMP | |
| notes | TEXT | |

### `source_records`

Universal provenance table.

| Column | Type | Description |
|--------|------|-------------|
| source_record_id | TEXT PK | |
| source_type | TEXT | `PUBMED`, `PMC`, `CROSSREF`, `CTGOV`, `SEC`, `PRESS`, `MANUAL` |
| source_identifier | TEXT | PMID, DOI, NCT, accession |
| url | TEXT | |
| title | TEXT | |
| publication_date | DATE | Print/epub date |
| online_first_date | DATE | **Nullable** |
| trial_registration_date | DATE | **Nullable** |
| company_announcement_date | DATE | **Nullable** |
| data_extraction_timestamp | TIMESTAMP | When we extracted |
| is_peer_reviewed | BOOLEAN | |
| full_text_available | BOOLEAN | |
| raw_storage_path | TEXT | |

### `publications`

Literature linked to programs (many-to-many via `publication_program_links`).

| Column | Type | Description |
|--------|------|-------------|
| publication_id | TEXT PK | |
| source_record_id | TEXT FK | |
| pmid | TEXT | |
| pmcid | TEXT | |
| doi | TEXT | |
| abstract | TEXT | |
| study_type_inferred | TEXT | `ANIMAL_EFFICACY`, `PKPD`, `REVIEW`, etc. |

### `publication_program_links`

| Column | Type | Description |
|--------|------|-------------|
| link_id | TEXT PK | |
| publication_id | TEXT FK | |
| program_id | TEXT FK | |
| relevance | TEXT | `PRIMARY_EFFICACY`, `SAFETY`, `MODEL`, etc. |
| linked_by | TEXT | auto \| manual |

### `animal_studies`

One row per preclinical animal experiment (or distinct cohort within a paper).

| Column | Type | Description |
|--------|------|-------------|
| study_id | TEXT PK | |
| program_id | TEXT FK | |
| publication_id | TEXT FK | |
| drug_name | TEXT | As reported |
| indication_model | TEXT | e.g., `LLC syngeneic lung` |
| species | TEXT | mouse, rat, etc. |
| strain | TEXT | C57BL/6, etc. |
| sex | TEXT | M, F, mixed, NR |
| age | TEXT | e.g., `6-8 weeks` |
| disease_model | TEXT | xenograft, GEMM, carcinogen |
| model_induction_method | TEXT | |
| sample_size_treatment | INTEGER | |
| sample_size_control | INTEGER | |
| control_type | TEXT | vehicle, isotype, sham |
| is_humanized_model | BOOLEAN | |
| is_pdx | BOOLEAN | |
| therapeutic_vs_prophylactic | TEXT | |
| extracted_by | TEXT | manual \| nlp \| hybrid |
| extraction_confidence | REAL | 0–1 |
| verification_status | TEXT | `pending`, `verified`, `rejected` |

### `animal_study_features`

Long-format or wide feature store for study-level variables.

**Recommended:** wide table with nullable columns grouped by domain.

| Column group | Examples |
|--------------|----------|
| Efficacy | primary_endpoint, effect_size, pct_improvement, p_value, ci_lower, ci_upper, dose_mg_kg, dose_response |
| Translational (FIMD-inspired) | face_validity_score, endpoint_clinical_similarity, mechanism_similarity, pkpd_relevance, biomarker_overlap |
| Quality (ARRIVE/Landis) | randomization_reported, blinding_reported, allocation_concealment, sample_size_calc, exclusions_described, preregistration |
| Replication | independent_lab_replication, replicated_across_models, replicated_across_species |
| Meta | feature_source_sentence, feature_page_ref, extraction_method |

See `data_dictionary.md` for full column list.

### `program_preclinical_features`

Aggregated features across all pre-t0 animal studies for a program.

| Column | Type | Description |
|--------|------|-------------|
| program_id | TEXT PK/FK | |
| n_animal_studies | INTEGER | Count pre-t0 |
| n_species | INTEGER | |
| n_models | INTEGER | |
| best_effect_size | REAL | Max across studies (document rule) |
| median_effect_size | REAL | |
| any_dose_response | BOOLEAN | |
| pct_studies_randomized | REAL | |
| pct_studies_blinded | REAL | |
| any_independent_replication | BOOLEAN | |
| any_humanized_or_pdx | BOOLEAN | |
| pts_composite | REAL | **Nullable until statistically derived** |
| pts_version | TEXT | |
| aggregation_rule_version | TEXT | |
| computed_at | TIMESTAMP | |

### `benchmark_pos_rates`

Historical success rates for baseline models (Wong, BIO/Informa).

| Column | Type | Description |
|--------|------|-------------|
| rate_id | TEXT PK | |
| source | TEXT | `WONG2019`, `BIO_INFORMA_2020` |
| phase | TEXT | |
| indication_group | TEXT | |
| modality | TEXT | |
| biomarker_enriched | BOOLEAN | |
| success_rate | REAL | |
| n_programs | INTEGER | Source sample size |
| effective_year_range | TEXT | |

### `program_financial_events`

Clinical readout / announcement events for event study.

| Column | Type | Description |
|--------|------|-------------|
| event_id | TEXT PK | |
| program_id | TEXT FK | |
| event_type | TEXT | `PHASE2_READOUT`, `PHASE3_READOUT`, `FDA_DECISION` |
| event_date | DATE | **Precise announcement date** |
| event_date_source | TEXT | Press release, SEC 8-K |
| event_date_precision | TEXT | `DAY`, `WEEK`, `MONTH` |
| outcome_direction | TEXT | positive, negative, mixed |
| concurrent_event_flag | BOOLEAN | Financing, M&A same window |

### `market_data_daily`

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | |
| ticker | TEXT | |
| date | DATE | |
| adj_close | REAL | |
| volume | REAL | |
| source | TEXT | yfinance, etc. |

### `event_study_results`

| Column | Type | Description |
|--------|------|-------------|
| result_id | TEXT PK | |
| event_id | TEXT FK | |
| window | TEXT | `[-1,+1]`, `[0,+5]` |
| benchmark_model | TEXT | `MARKET`, `XBI`, `FF3` |
| car | REAL | Cumulative abnormal return |
| ar_series_json | TEXT | Daily ARs |
| estimated_at | TIMESTAMP | |

### `model_predictions`

| Column | Type | Description |
|--------|------|-------------|
| prediction_id | TEXT PK | |
| program_id | TEXT FK | |
| model_name | TEXT | |
| model_version | TEXT | |
| p_model | REAL | P(clinical success) |
| prediction_made_at | DATE | Must be ≤ t0 for prospective; or train-fold date |
| feature_set | TEXT | ablation group name |
| train_cohort | TEXT | temporal split ID |

### `market_implied_probability`

Version 2 — optional at MVP.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | |
| program_id | TEXT FK | |
| p_market | REAL | |
| estimation_method | TEXT | run_up, analyst, options |
| as_of_date | DATE | Must be pre-readout |
| confidence | TEXT | |

### `leakage_audit_log`

| Column | Type | Description |
|--------|------|-------------|
| audit_id | TEXT PK | |
| program_id | TEXT FK | |
| check_type | TEXT | See leakage_prevention.md |
| passed | BOOLEAN | |
| violation_detail | TEXT | |
| checked_at | TIMESTAMP | |

### `extraction_review_queue`

For NLP/manual verification workflow.

| Column | Type | Description |
|--------|------|-------------|
| queue_id | TEXT PK | |
| study_id | TEXT FK | |
| field_name | TEXT | |
| extracted_value | TEXT | |
| source_sentence | TEXT | |
| confidence | REAL | |
| reviewer | TEXT | |
| status | TEXT | pending, approved, corrected |
| corrected_value | TEXT | |

## Indexes

```sql
CREATE INDEX idx_programs_company ON programs(company_id);
CREATE INDEX idx_trials_program ON clinical_trials(program_id);
CREATE INDEX idx_animal_studies_program ON animal_studies(program_id);
CREATE INDEX idx_source_records_dates ON source_records(publication_date, online_first_date);
CREATE INDEX idx_financial_events_date ON program_financial_events(event_date);
```

## Views (analysis-ready)

### `v_programs_prospective`

Programs passing leakage audit with pre-t0 features only.

### `v_program_outcomes_primary`

One row per program with primary `clinical_success` label and t0.

### `v_preclinical_wide`

Join `programs` + `program_preclinical_features` + `trial_outcomes`.

## SQLite vs PostgreSQL

- **MVP:** SQLite (`data/processed/research.db`) — single-file, portable
- **Scale:** PostgreSQL — concurrent writers, full-text search on abstracts

DDL: `sql/schema.sql`
