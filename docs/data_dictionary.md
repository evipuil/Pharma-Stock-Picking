# Data Dictionary (MVP core fields)

Full schema: `docs/schema.md`. This dictionary defines semantics and allowed values for analysis-critical variables.

---

## Identifiers

| Variable | Table | Type | Description |
|----------|-------|------|-------------|
| program_id | programs | TEXT | UUID primary key for drug×indication×stage |
| nct_id | clinical_trials | TEXT | ClinicalTrials.gov identifier |
| study_id | animal_studies | TEXT | UUID per animal experiment cohort |
| ticker | companies | TEXT | US exchange symbol at reference date |

---

## Temporal

| Variable | Type | Description | Allowed / notes |
|----------|------|-------------|-----------------|
| t0_date | DATE | Information cutoff for features | Required |
| t0_definition | TEXT | How t0 was chosen | FIRST_PATIENT_DOSED, TRIAL_START, OTHER |
| effective_public_date | DATE | min(pub, online-first) | Computed in pipeline |
| outcome_date | DATE | First public outcome disclosure | Post-t0 |
| event_date | DATE | Clinical readout for CAR | Post-t0 |

---

## Clinical outcomes

| Variable | Type | Values | Description |
|----------|------|--------|-------------|
| clinical_success | INT | 0, 1 | Primary Phase II success label |
| met_primary_endpoint | INT | 0, 1, NULL | Endpoint met independent of advancement |
| advanced_to_phase3 | INT | 0, 1, NULL | Phase III initiated |
| regulatory_approval | INT | 0, 1, NULL | FDA/EMA approval same indication |
| technical_failure | INT | 0, 1 | Efficacy/futility failure |
| safety_failure | INT | 0, 1 | Safety-driven stop |
| commercial_discontinuation | INT | 0, 1 | Business decision not biological failure |
| outcome_unknown | INT | 0, 1 | Cannot adjudicate |

---

## Program classification

| Variable | Type | Values |
|----------|------|--------|
| indication | TEXT | NSCLC, melanoma, ... |
| indication_group | TEXT | Rolled-up for PoS lookup |
| modality | TEXT | small_molecule, mAb, ADC, CAR_T, ... |
| target | TEXT | Free text normalized |
| biomarker_strategy | TEXT | all_comers, biomarker_selected, ... |
| development_stage_at_t0 | TEXT | PHASE2 (MVP) |
| sponsor_size | TEXT | large_pharma, mid_cap, small_biotech |

---

## Animal study — basic

| Variable | Type | Unit / values |
|----------|------|---------------|
| species | TEXT | mouse, rat, dog, NHP, ... |
| strain | TEXT | e.g. BALB/c nude |
| sex | TEXT | M, F, mixed, not_reported |
| age | TEXT | As reported |
| disease_model | TEXT | syngeneic, CDX, PDX, GEMM, carcinogen |
| sample_size_treatment | INT | Count |
| sample_size_control | INT | Count |
| control_type | TEXT | vehicle, isotype, untreated |
| is_humanized_model | BOOL | |
| is_pdx | BOOL | |
| therapeutic_vs_prophylactic | TEXT | therapeutic, prophylactic, both, NR |

---

## Animal study — efficacy

| Variable | Type | Notes |
|----------|------|-------|
| primary_endpoint | TEXT | e.g. tumor volume, OS |
| effect_size | REAL | Standardized where possible |
| effect_size_type | TEXT | HR, OR, mean_diff, pct_inhibition |
| pct_improvement | REAL | Percent |
| p_value | REAL | Two-sided unless stated |
| ci_lower, ci_upper | REAL | 95% default |
| dose_mg_kg | REAL | Normalize to mg/kg if possible |
| dose_response | BOOL | Monotonic response shown |
| survival_benefit | BOOL | Median OS benefit stated |

---

## Animal study — translational validity

Ordinal **0 = poor/absent, 1 = partial, 2 = strong** unless binary noted.

| Variable | Description | Framework |
|----------|-------------|-----------|
| face_validity | Phenotype resembles human disease | FIMD |
| construct_validity | Same biological pathway | FIMD / van der Worp |
| predictive_validity | Endpoint predicts human endpoint | FIMD |
| endpoint_clinical_similarity | Animal endpoint maps to Phase II primary | Custom |
| mechanism_similarity | Target/pathway alignment | FIMD |
| pkpd_relevance | Exposure at efficacious dose plausibly reachable in humans | Berg et al. |
| biomarker_overlap | Same biomarker used in animal and planned clinical | Custom |
| human_target_validated | BOOL; target evidence in humans pre-t0 | Literature |

---

## Animal study — quality (ARRIVE 2.0 / Landis)

Binary **0/1/NULL** (NULL = not reported, not assumed negative).

| Variable | ARRIVE item |
|----------|-------------|
| randomization_reported | Randomisation |
| blinding_reported | Blinding |
| allocation_concealment | Concealment |
| sample_size_calculation | Sample size |
| exclusions_described | Exclusions |
| preregistration | Protocol registration |
| conflict_of_interest_reported | Funding/COI |
| peer_reviewed | Publication type |
| independent_lab_replication | External replication |
| replicated_across_models | Multiple models same lab/program |
| replicated_across_species | >1 species |

---

## Program-level aggregates

| Variable | Aggregation rule |
|----------|------------------|
| n_animal_studies | COUNT studies with verification_status=verified |
| n_species | DISTINCT species |
| n_models | DISTINCT disease_model |
| best_effect_size | MAX(effect_size) among comparable endpoints — document heterogeneity |
| median_effect_size | MEDIAN |
| pct_studies_randomized | MEAN(randomization_reported) |
| pct_studies_blinded | MEAN(blinding_reported) |
| any_independent_replication | MAX(independent_lab_replication) |
| any_humanized_or_pdx | MAX(is_humanized OR is_pdx) |
| pts_composite | Train-fit linear combination; NULL until derived |

---

## Model outputs

| Variable | Range | Description |
|----------|-------|-------------|
| p_model | [0,1] | Predicted P(clinical_success) |
| p_market | [0,1] | Market-implied (v2) |
| scientific_edge | [-1,1] | p_model - p_market |
| car | ℝ | Cumulative abnormal return |
| benchmark_model | TEXT | MARKET, XBI, FF3 |

---

## Provenance (required on all extracted fields)

| Variable | Description |
|----------|-------------|
| source_record_id | FK to source_records |
| data_extraction_timestamp | When extracted |
| feature_source_sentence | Quote supporting value |
| extraction_confidence | 0–1 |
| verification_status | pending, verified, rejected |

---

## Data quality flags

| Flag | Meaning |
|------|---------|
| missing_preclinical | No pre-t0 animal studies found |
| t0_disputed | Sources disagree >14 days |
| paywalled_fulltext | Features from abstract only |
| delisted_ticker | Price history may be incomplete |
| labeling_disputed | Awaiting second reviewer |

Store flags in `programs.notes` JSON or dedicated QA table in Phase 2.
