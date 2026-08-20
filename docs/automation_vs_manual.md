# Automation vs Manual Validation

Field-level strategy for MVP → scale.  
Legend: **A** = automated, **S** = semi-automated, **M** = manual required, **P** = paid source, **U** = uncertain/historically incomplete

---

## Clinical & program metadata

| Field | Method | Notes |
|-------|--------|-------|
| nct_id | **A** | CT.gov API |
| phase, condition, intervention | **A** | CT.gov; normalize indication **S** |
| trial start date | **A** | Compare FPI **M** if disclosed in press only |
| enrollment, masking, allocation | **A** | CT.gov |
| sponsor → ticker mapping | **S** | EDGAR + manual lookup |
| modality, target | **S** | CT.gov + manual from mechanism |
| biomarker_strategy | **M** | Protocol review |
| t0_date | **S** | Rule-based + adjudication |
| clinical_success labels | **S** | CT.gov results + **M** adjudication |
| failure subtype flags | **M** | Requires reading disclosures |
| event_date (readout) | **S** | Press release scrape + **M** verify |
| market_cap, cash at t0 | **S** | SEC 10-Q **U** for exact t0 alignment |
| portfolio concentration | **M** | Subjective |

---

## Literature discovery

| Task | Method | Notes |
|------|--------|-------|
| PubMed query generation | **S** | Drug synonyms from CT.gov + manual |
| Search execution | **A** | E-utilities |
| Date filter ≤ t0 | **A** | Leakage module |
| Relevance filtering (animal vs clinical) | **S** | Keyword + **M** review |
| DOI/date reconciliation | **A** | Crossref |
| Full-text retrieval | **S** | PMC OA **U** for paywall |
| Link paper → program | **M** | MVP; ML later |

---

## Animal study features

### Basic metadata

| Field | Method | Notes |
|-------|--------|-------|
| species, strain, sex, age | **S** | Regex + LLM assist → **M** verify |
| disease_model | **S** | NLP **M** verify |
| sample_size per group | **S** | Table extraction fragile |
| control_type | **S** | |
| drug dose | **S** | Units normalization **M** |

### Efficacy

| Field | Method | Notes |
|-------|--------|-------|
| primary_endpoint | **S** | |
| effect_size, CI, p-value | **S** | **M** verify all MVP rows |
| percent improvement | **S** | Define computation rule |
| dose-response | **M** | Needs figure interpretation |
| survival benefit | **S** | Kaplan-Meier text patterns |
| therapeutic vs prophylactic | **M** | |

### Translational validity (FIMD-inspired)

| Field | Method | Notes |
|-------|--------|-------|
| face/construct/predictive validity | **M** | Rubric scoring; 2 reviewers MVP |
| endpoint_clinical_similarity | **M** | Compare to CT.gov primary endpoint |
| mechanism_similarity | **M** | |
| pkpd_relevance | **M** | Often absent in papers |
| biomarker_overlap | **S** | |
| humanized_model, PDX flags | **S** | Keyword + **M** |
| human_target_validated | **S** | Literature prior to t0 |

### Quality / bias (ARRIVE 2.0 / Landis)

| Field | Method | Notes |
|-------|--------|-------|
| randomization_reported | **S** | Methods section patterns |
| blinding_reported | **S** | |
| allocation_concealment | **S** | Often unreported → NULL |
| sample_size_calculation | **S** | |
| exclusions_described | **S** | |
| preregistration | **A/S** | ClinicalTrials.gov preclinical rare |
| COI/funding | **A** | PubMed metadata partial |
| peer_reviewed | **A** | |
| independent_lab_replication | **M** | Cross-ref search |
| replicated_across_models/species | **M** | Program-level synthesis |

---

## Aggregation (program level)

| Field | Method | Notes |
|-------|--------|-------|
| n_animal_studies, n_species | **A** | After studies verified |
| best/median effect_size | **A** | Rule: document max vs median |
| pct_studies_randomized | **A** | |
| pts_composite | **A** | Only after train-fit weights |

---

## Financial / event study

| Field | Method | Notes |
|-------|--------|-------|
| adj_close daily prices | **A** | yfinance **U** delisted |
| SPY, XBI benchmark | **A** | |
| beta estimation window | **A** | |
| CAR computation | **A** | |
| concurrent_event_flag | **M** | 8-K scan |
| P_market (v2) | **S/P** | Options **P**; run-up **S** |
| analyst estimates | **P/U** | Not MVP |

---

## NLP / LLM extraction pipeline (Phase 5)

```
paper PDF/XML
  → deterministic regex (methods, n=)
  → LLM structured JSON (confidence per field)
  → extraction_review_queue (status=pending)
  → human approve/reject
  → animal_study_features (verification_status=verified)
```

**Never** write LLM output directly to `processed/` without review flag.

Store per field:

- `source_sentence`
- `feature_page_ref`
- `extraction_confidence`
- `verification_status`

---

## MVP manual effort estimate

| Task | Per program | × 25 programs |
|------|-------------|---------------|
| CT.gov + t0 + outcome | 1–2 hr | ~30 hr |
| Literature search | 1–2 hr | ~30 hr |
| Animal feature extraction | 2–4 hr (if papers exist) | ~50 hr |
| Financial event | 0.5 hr | ~12 hr |
| **Total** | | **~120 hr** |

Programs with zero pre-t0 animal papers: ~30 min (document null).

---

## Quality gates

| Gate | Requirement |
|------|-------------|
| G1 | All **M** fields for efficacy reviewed for Wave 1 (n=5) |
| G2 | 100% leakage audit pass before modeling |
| G3 | Inter-rater κ ≥ 0.6 on validity rubric (subset) before scaling rubric |
| G4 | LLM extraction <80% auto-accept without review |

---

## Fields likely permanently sparse

- `allocation_concealment` (historical papers)
- `preregistration` (animal studies)
- `pkpd_relevance` quantitative data
- `options_implied_p_market` (historical)
- Exact `first_patient_dosed` dates

Document sparsity in every model report; do not fake imputation.
