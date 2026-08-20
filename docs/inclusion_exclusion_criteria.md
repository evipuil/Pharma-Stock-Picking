# Inclusion & Exclusion Criteria

## Population definition

**Target population:** Drug development **programs** (drug × indication × stage) sponsored by **publicly traded U.S. biotech/pharma companies**, entering **Phase II** for **oncology** indications during a defined calendar window, with **observable subsequent Phase II/III outcomes**.

## Inclusion criteria (MVP)

All must be satisfied:

| # | Criterion | Rationale |
|---|-----------|-----------|
| I1 | **Sponsor** is a U.S.-listed company (NYSE/NASDAQ) at or before t0 | Event study requires tradable equity |
| I2 | **Indication** is oncology (solid or hematologic malignancy) | Focused MVP; expandable later |
| I3 | **Lead interventional Phase II trial** started (or FPI) between **2010-01-01** and **2020-12-31** | Sufficient follow-up for outcomes; pre-2020 t0 for literature |
| I4 | **Primary trial** registered on ClinicalTrials.gov with retrievable metadata | Reproducible trial provenance |
| I5 | **Outcome known** for primary Phase II endpoint or clear program disposition (advance, terminate, approve) | Supervised learning requires labels |
| I6 | **t0 documentable** from CT.gov start date, FPI, or contemporaneous sponsor disclosure | Leakage prevention anchor |
| I7 | Program is **not exclusively pediatric/rare** orphan with no animal literature expectation (case-by-case) | Avoid empty preclinical stratum without justification |

### Inclusion — expanded cohort (post-MVP)

- Phase I/III extensions, non-oncology indications
- EU-listed sponsors with ADR tickers (secondary analysis)
- Private sponsors if paired with public licensee (complex; deferred)

## Exclusion criteria

| # | Criterion | Rationale |
|---|-----------|-----------|
| E1 | Phase II trial **not interventional** (observational only) | Outcome definition breaks down |
| E2 | **Combination-only** program where pre-t0 animal data exist only for backbone therapy, not investigational agent | Attribution ambiguity |
| E3 | **Device, diagnostic, or surgical** intervention | Out of scope for drug translation MVP |
| E4 | **Cell/gene therapy** without any pre-t0 peer-reviewed animal efficacy (flag, don't auto-exclude) | Document missing preclinical stratum |
| E5 | **Acquired program** where sponsor changed before t0 without traceable drug identity | Provenance break |
| E6 | **t0 ambiguous** (>30 day gap between sources with material literature in between) | Manual resolution required |
| E7 | **Outcome date before t0** (data error) | Invalid row |
| E8 | **Duplicate program** (same drug-indication-NCT already in cohort) | Dedup |
| E9 | **SPAC shell / no trading history** around event date | Event study infeasible |

## Survivorship bias prevention

**Explicitly include:**

- Programs terminated for **lack of efficacy**
- Programs terminated for **safety**
- Programs discontinued for **commercial/strategic** reasons (separate label)
- Programs with **inconclusive** Phase II (label `clinical_success = 0` with `outcome_unknown` flag if ambiguous)

**Do not restrict to:**

- Approved drugs only
- Programs still active
- Companies still listed (delisted sponsors included if price history exists)

## Temporal cohort splits

| Split | Programs entering Phase II | Purpose |
|-------|---------------------------|---------|
| **Train** | 2010–2016 | Model fitting |
| **Validation** | 2017–2018 | Hyperparameter / calibration tuning |
| **Test (temporal holdout)** | 2019–2020 | Unbiased performance & event study |

Programs from the same company may appear in multiple splits **if different programs**; never split the same `program_id`.

## Indication normalization

Map raw CT.gov conditions to canonical labels:

| Canonical | Examples |
|-----------|----------|
| NSCLC | Non-small cell lung cancer |
| SCLC | Small cell lung cancer |
| Melanoma | Cutaneous melanoma |
| Breast | HR+, HER2+, TNBC subtags optional |
| CRC | Colorectal cancer |
| Prostate | mCRPC, etc. |
| Lymphoma | DLBCL, follicular, etc. |
| AML | Acute myeloid leukemia |
| Other_oncology | Bucket with notes |

Sub-indication tags stored separately; MVP baselines may roll up to indication_group.

## Modality taxonomy

`small_molecule`, `monoclonal_antibody`, `bispecific`, `ADC`, `CAR_T`, `TCR_T`, `oncolytic_virus`, `vaccine`, `radiopharmaceutical`, `other`, `unknown`

## Sponsor classification

| Class | Definition |
|-------|------------|
| `large_pharma` | Market cap > $50B at t0 |
| `mid_cap` | $2B–$50B |
| `small_biotech` | < $2B |
| `single_asset` | ≥60% of pipeline value in one program (**manual**, uncertain) |

## Cohort size targets

| Wave | N programs | Status |
|------|------------|--------|
| MVP wave 1 | 20–30 | Curation in progress |
| MVP wave 2 | +20 | Expand diversity of modality/outcome |
| Validation wave | 15–25 (2019–2020 only) | Held out from all modeling decisions |

## Documentation per included program

Required fields before `cohort_status = included`:

- [ ] `primary_nct_id` verified on CT.gov
- [ ] `t0_date` + source
- [ ] `clinical_success` label + adjudication note
- [ ] Sponsor ticker at t0
- [ ] Pre-t0 literature search completed (even if zero results)
- [ ] Leakage audit passed

## Edge cases — adjudication rules

1. **Multiple Phase II trials same drug-indication:** Select **pivotal or first** Phase II; link others as secondary NCT IDs in notes.
2. **Phase II/III seamless design:** t0 = Phase II portion start; outcome = Phase II primary unless protocol pre-specifies combined.
3. **Fast Track approval without traditional Phase III:** Label regulatory outcome separately; Phase II success may still be defined on primary endpoint.
4. **Partnership mid-development:** Attribute to sponsor of record on CT.gov at t0.
