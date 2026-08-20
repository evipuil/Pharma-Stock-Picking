# Statistical Analysis Plan (SAP)

**Version:** v1.0 (MVP)  
**Primary endpoint:** Calibrated prediction of `clinical_success` (Phase II)  
**Secondary endpoints:** Ablation comparisons, event-study CAR association with P_model

---

## 1. Objectives & hypotheses

### Primary (clinical)

**H1:** A model using pre-t0 preclinical features produces **better calibrated** probability estimates of Phase II success than a historical-rate baseline alone.

- Metric: **Brier score** (primary), PR-AUC (secondary)
- Null: Δ Brier ≤ 0 vs baseline

### Exploratory (feature groups)

| ID | Hypothesis | Test |
|----|------------|------|
| E1 | Raw animal effect size predicts success | Univariate logistic + OR |
| E2 | Study rigor (ARRIVE/Landis) predicts success | Group comparison |
| E3 | Translational validity (FIMD-inspired) predicts success | Univariate + multivariate |
| E4 | Independent replication predicts success | Fisher exact / logistic |
| E5 | PK/PD relevance predicts success | Ordinal logistic |
| E6 | Cross-model consistency predicts success | Binary flags |
| E7 | Combined preclinical beats baseline | Nested model LRT / Brier comparison |

### Financial (Version 1)

**H-F1:** Higher P_model among eventual successes associates with **lower** CAR if market fully efficient (exploratory sign test).

**H-F2:** P_model predicts **sign** or **magnitude** of CAR around readout after controlling for market cap and sector.

**H-F3 (Version 2):** Scientific Edge (P_model − P_market) predicts CAR.

---

## 2. Analysis populations

| Population | Definition | N (target) |
|------------|------------|------------|
| `PP_clinical` | Included programs passing leakage audit with label | 20–50 MVP |
| `PP_preclinical` | Subset with ≥1 pre-t0 animal study | Expected 60–80% |
| `PP_financial` | Subset with valid event_date + price history | Expected 70–90% |

Primary analyses on `PP_clinical`; sensitivity on `PP_preclinical` only.

---

## 3. Outcomes

| Outcome | Type | Role |
|---------|------|------|
| `clinical_success` | Binary | Primary ML target |
| `met_primary_endpoint` | Binary | Sensitivity |
| `advanced_to_phase3` | Binary | Sensitivity |
| `CAR[-1,+1]`, `CAR[0,+5]` | Continuous | Event study |

---

## 4. Predictors & feature sets (ablations)

Defined in `configs/feature_sets.yaml`:

| Set | Contents |
|-----|----------|
| `baseline_clinical` | phase, indication_group, modality, biomarker_strategy, sponsor_size |
| `animal_efficacy` | effect sizes, p-values, dose-response, survival benefit |
| `animal_quality` | randomization, blinding, sample size calc, exclusions |
| `translation` | FIMD-inspired validity scores, humanized/PDX, endpoint similarity |
| `replication` | independent lab, cross-model, cross-species |
| `pkpd` | pkpd_relevance, human target validation |
| `all_preclinical` | Union of animal blocks |
| `baseline_plus_preclinical` | baseline + all_preclinical |

**Rule:** Impute missing preclinical with indicator variables (`missing_preclinical=1`); do not mean-impute efficacy.

---

## 5. Baseline models

### B0: Naive

- P = 0.5 (sanity check only)

### B1: Marginal historical rate

- P = overall Phase II oncology success rate in cohort

### B2: Stratified Wong/BIO table

- Lookup PoS by (phase, indication_group, modality, biomarker_enriched)
- Fallback hierarchy if cell empty: modality → indication → phase → global

### B3: Logistic on baseline_clinical only

- Interpretable coefficients vs preclinical increment

---

## 6. Primary models (MVP)

Fit in order of complexity as N permits:

1. **Logistic regression** (unpenalized where identifiable)
2. **L2 logistic (C via CV on validation fold)**
3. **Random forest** (if N ≥ 40 and events ≥ 10)
4. **XGBoost** (Phase 2 scale; defer if N < 50)

**Ensemble:** Simple average of calibrated B3 + best preclinical model (Phase 2).

---

## 7. Validation strategy

### Temporal split (primary)

| Fold | t0 year | Use |
|------|---------|-----|
| Train | 2010–2016 | Fit coefficients |
| Validation | 2017–2018 | Tune regularization, calibration |
| Test | 2019–2020 | Report final metrics once |

**No random K-fold** as primary analysis.

### Bootstrap

- 1000 bootstrap resamples of train for coefficient CIs
- Cluster bootstrap at `company_id` level for financial analyses

### Group constraints

- One row per `program_id`
- Never split related NCT IDs of same program

---

## 8. Evaluation metrics

| Metric | Priority | Notes |
|--------|----------|-------|
| Brier score | **Primary** | Lower is better |
| Log loss | Primary secondary | |
| Calibration slope/intercept | **Primary** | On test fold |
| Calibration plot (reliability) | Required | Deciles |
| PR-AUC | Secondary | Imbalanced outcomes |
| ROC-AUC | Secondary | |
| Sensitivity @ fixed specificity | Exploratory | |

**Calibration method:** Platt scaling or isotonic regression fit on **validation fold only**, apply to test.

---

## 9. Model comparison tests

- **Brier:** Bootstrap Δ Brier with 95% CI
- **Nested models:** Likelihood ratio test (logistic nested cases)
- **Discrimination:** DeLong test for AUC (if applicable)

Pre-register in analysis code comments; avoid test-set peeking.

---

## 10. Missing data

| Pattern | Approach |
|---------|----------|
| No animal studies | Keep in analysis with `n_animal_studies=0` |
| Partial feature missing | Missing indicators + sensitivity complete-case |
| Unknown outcome | Exclude from supervised; report count |
| Missing event date | Exclude from event study only |

---

## 11. Preclinical Translation Score (PTS)

**MVP:** Do **not** use composite in primary analysis.

**Phase 2 (if justified):**

1. Univariate screen → retain p < 0.10 features
2. Fit L2 logistic on train → coefficients as weights
3. PTS = linear predictor transformed to [0,1]
4. Validate increment to Brier vs baseline on test

Document if weights unstable (small N).

---

## 12. Event study methodology

Following Singh et al. (2022) and Hwang et al. (2013):

### Event date

First public Phase II readout (press release date).

### Windows

- `[-1,+1]`, `[0,+1]`, `[0,+5]` trading days

### Expected return models

1. **Market model:** SPY beta estimated over [-252,-30] days
2. **Sector model:** XBI or IBB beta
3. **FF3** (robustness)

```
AR_it = R_it - (alpha_i + beta_i * R_mt)
CAR_i = sum(AR_it) over window
```

### Cross-sectional regression

```
CAR_i = gamma_0 + gamma_1 * P_model_i + gamma_2 * log(mktcap_i) + gamma_3 * single_asset_i + epsilon_i
```

- Heteroskedasticity-robust SEs
- Winsorize CAR at 1%/99% (sensitivity)

### Version 2

Add P_market from pre-event run-up or analyst consensus where available.

---

## 13. Multiplicity

- Primary: Brier comparison baseline vs `baseline_plus_preclinical`
- Exploratory E1–E6: report unadjusted p-values with FDR annotation; interpret cautiously at N=30

---

## 14. Power considerations (honest)

At N=30, ~12 events (assuming 40% success rate):

- Detecting AUC improvement of 0.15 → low power
- Focus on **effect direction**, calibration, and feasibility
- Hold strict claims for N>100 expansion

---

## 15. Software & reproducibility

- Python 3.10+
- `scikit-learn`, `statsmodels`
- Fixed seeds in `configs/modeling.yaml`
- Analysis scripts: `src/models/evaluate.py`, `src/event_study/analysis.py`

---

## 16. Reporting checklist

- [ ] CONSORT-style cohort flow (included/excluded counts)
- [ ] Leakage audit summary
- [ ] Missing data table
- [ ] Calibration plot (test)
- [ ] Ablation table (all feature sets)
- [ ] Event study CAR distribution vs P_model
- [ ] Negative results documented explicitly
