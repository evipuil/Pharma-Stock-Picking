# Cohort Construction Audit

**Purpose:** Assess discovery bias, survivorship, and outcome-dependent selection in the 112-catalyst registry.

## How catalysts were discovered

- Migrated from Wave 1 `programs` table via `migrate-catalysts`
- Expanded via `configs/catalyst_candidates.yaml` and `expand-catalysts`
- Announcement dates from CT.gov proxies + curated overrides (`catalyst_announcement_overrides.yaml`)
- **Not** selected based on realized CAR or trading outcomes

## Outcome representation

| Category | N |
|----------|--:|
| SUCCESS | 63 |
| EFFICACY_FAILURE | 24 |
| SAFETY_FAILURE | 3 |
| UNKNOWN | 22 |

Failures (clinical_success=0): **27/107 priced** (25%)

## Survivorship / delisting concerns

- **5 catalysts lack CAR** due to truncated/delisted price history (CLVS, MRTX, SGEN, OMED post-2017)
- Delisted tickers are disproportionately **failures or small-cap** programs
- `data/processed/missing_price_requirements.csv` lists exact date ranges needed
- **Risk:** failed companies may be underrepresented if price history unavailable → short-edge estimates may be **optimistic** for live trading

## Selection bias checks

| Question | Assessment |
|----------|------------|
| Could selection depend on known outcome? | **Low risk** for core registry; candidates YAML is outcome-agnostic |
| Are successes over-captured? | Large pharma successes (MRK, BMY, NVS) well represented |
| Are failures under-captured? | **Moderate risk** — delisted failures harder to price |
| Era overrepresentation? | 2015–2018 dense; 2023+ sparse in OOS folds |
| Phase bias? | Phase II oncology overweight vs rare disease |

## Implications for short-edge validation

1. **Do not extrapolate** short returns to delisted/unpriced failures
2. Expand cohort **before** outcome lookup (Phase II/III oncology, neurology, immunology, rare disease)
3. Require Polygon/EODHD/CRSP for post-2017 delistings before claiming full-sample validity
4. Locked holdout (`FINAL_HOLDOUT_START = 2022-01-01` in `configs/short_edge.yaml`) must stay untouched

## Recommended next cohort expansion

Target **≥250 catalysts** with:
- Independent identification from CT.gov / press releases
- Pre-registration of inclusion criteria
- Mandatory price coverage check **before** outcome labeling
- Stratified by phase and sponsor size
