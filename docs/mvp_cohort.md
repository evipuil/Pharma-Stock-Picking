# MVP Cohort: 20–50 Oncology Phase II Programs

**Status:** PROPOSED — requires verification on ClinicalTrials.gov before inclusion  
**Do not treat this document as populated data.** Each row is a **candidate** with explicit verification checklist.

---

## Selection strategy

Build cohort in three waves:

1. **Wave 1 (N≈15):** High-profile, well-documented programs with clear outcomes and literature
2. **Wave 2 (N≈15):** Balanced failures + successes; diverse modalities
3. **Wave 3 (N≈10–20):** 2019–2020 starts for temporal holdout only

Target outcome mix (Wave 1+2):

- ~40% Phase II success (advancement)
- ~40% technical/safety failure
- ~20% commercial discontinuation or ambiguous (for labeling practice)

Target modality mix:

- Small molecule, mAb, ADC, targeted therapy, IO combination

---

## Candidate programs (verify before locking)

The table below lists **archetypal, publicly discussed** oncology programs from U.S.-listed sponsors.  
**Action required:** Confirm NCT ID, t0 date, ticker at t0, and outcome before setting `cohort_status: included`.

| candidate_id | drug (working) | indication | sponsor (ticker) | est. Phase II era | modality | outcome (hypothesis) | primary_nct_id | verification_status |
|--------------|----------------|------------|------------------|-------------------|----------|----------------------|----------------|---------------------|
| C001 | Selumetinib + docetaxel | NSCLC (KRAS+) | AstraZeneca (AZN) | ~2012–2014 | small molecule | **Verify** — mixed KRAS story | TBD | `pending` |
| C002 | Idelalisib | CLL / indolent NHL | Gilead (GILD) | ~2010–2012 | small molecule | Success path | TBD | `pending` |
| C003 | Palbociclib | HR+ breast | Pfizer (PFE) | ~2010–2012 | small molecule | Success | TBD | `pending` |
| C004 | Osimertinib (AZD9291) | EGFR+ NSCLC | AstraZeneca (AZN) | ~2013–2015 | small molecule | Success | TBD | `pending` |
| C005 | Rucaparib | ovarian BRCA | Clovis (CLVS) | ~2012–2014 | small molecule | Mixed/verify | TBD | `pending` |
| C006 | Abemaciclib | breast | Lilly (LLY) | ~2013–2015 | small molecule | Success | TBD | `pending` |
| C007 | Neratinib | HER2+ breast | Puma (PBYI) | ~2010–2012 | small molecule | Success (toxicity notes) | TBD | `pending` |
| C008 | Mirvetuximab soravtansine | FRα+ ovarian | ImmunoGen (IMGN) | ~2013–2016 | ADC | Verify outcome | TBD | `pending` |
| C009 | Sacituzumab govitecan | TNBC | Immunomedics (IMMU) | ~2013–2016 | ADC | Success | TBD | `pending` |
| C010 | Belantamab mafodotin | myeloma | GSK (GSK) | ~2014–2017 | ADC | Verify (withdrawn later) | TBD | `pending` |
| C011 | Tivozanib | RCC | AVEO (AVEO) | ~2010–2012 | small molecule | **Failure** (FDA CRL context) | TBD | `pending` |
| C012 | Banoxantrone (AQ4N) | solid tumors | Novacea→transitions | ~2008–2010 | small molecule | **Failure** — check era | TBD | `pending` |
| C013 | Gedatolisib | breast | Celgene→BMS | ~2014–2016 | small molecule | Verify | TBD | `pending` |
| C014 | Epacadostat + pembrolizumab | melanoma | Incyte (INCY) | ~2015–2017 | small molecule + IO | **Failure** (ECHO trial) | NCT02178722 | `partial` — NCT only |
| C015 | Umbralisib + ublituximab | CLL | TG Therapeutics (TGTX) | ~2017–2019 | small molecule | Verify (later safety) | TBD | `pending` |
| C016 | Larotrectinib | NTRK+ solid | Loxo (LOXO) | ~2015–2017 | small molecule | Success | TBD | `pending` |
| C017 | Entrectinib | NTRK+ / ROS1 | Ignyta (RXDX) / Roche | ~2015–2017 | small molecule | Success | TBD | `pending` |
| C018 | Copanlisib | NHL | Bayer (BAYRY) | ~2013–2015 | small molecule | Verify | TBD | `pending` |
| C019 | Duvelisib | CLL/iNHL | Verastem (VSTM) | ~2014–2016 | small molecule | Verify | TBD | `pending` |
| C020 | Axicabtagene ciloleucel (axi-cel) | DLBCL | Kite/Gilead (GILD) | ~2014–2016 | CAR-T | Success (label path) | TBD | `pending` |
| C021 | Enasidenib | IDH2+ AML | Celgene (CELG) | ~2014–2016 | small molecule | Success | TBD | `pending` |
| C022 | Midostaurin + chemo | FLT3+ AML | Novartis (NVS) | ~2010–2013 | small molecule | Success | TBD | `pending` |
| C023 | Vemurafenib | BRAF+ melanoma | Roche/Genentech | ~2010–2011 | small molecule | Success (earlier era) | TBD | `pending` |
| C024 | Cobimetinib + vemurafenib | melanoma | Exelixis/Roche | ~2012–2014 | small molecule | Success | TBD | `pending` |
| C025 | Olaparib | ovarian BRCA | AstraZeneca (AZN) | ~2010–2012 | small molecule | Success | TBD | `pending` |
| C026 | Talazoparib | BRCA+ breast | Medivation/Pfizer | ~2013–2015 | small molecule | Success | TBD | `pending` |
| C027 | Binimetinib + encorafenib | BRAF+ melanoma | Array/Pfizer | ~2013–2015 | small molecule | Success | TBD | `pending` |
| C028 | Tipifarnib | HRAS+ head/neck | Kura (KURA) | ~2018–2020 | small molecule | Holdout candidate | TBD | `pending` |
| C029 | Sotorasib (AMG 510) | KRAS G12C NSCLC | Amgen (AMGN) | ~2018–2020 | small molecule | Holdout candidate | TBD | `pending` |
| C030 | Adagrasib (MRTX849) | KRAS G12C NSCLC | Mirati (MRTX) | ~2019–2020 | small molecule | Holdout candidate | TBD | `pending` |

**Note:** Large pharma entries (Pfizer, AZ, Lilly) useful for event-study heterogeneity (portfolio effects) but may have weaker sponsor-stock signal — include mix of **small/mid biotech** (PBYI, CLVS, IMMU, INCY, TGTX, KURA, MRTX, AVEO).

---

## Priority small-biotech subset (recommended Wave 1 start)

Start manual curation with **5 programs** covering outcome diversity:

| Priority | candidate_id | Rationale |
|----------|--------------|-----------|
| 1 | C014 | Well-known IO combo failure; literature-rich |
| 2 | C009 | ADC success; ImmunoGen literature |
| 3 | C011 | Clear efficacy failure; small biotech |
| 4 | C007 | Success with toxicity narrative |
| 5 | C005 | Mixed/clinical controversy |

For each: fetch NCT → define t0 → label outcome → PubMed search → feature template.

---

## Curation workflow

```
configs/cohort_mvp.yaml  →  CT.gov fetch  →  manual review sheet
        →  SQLite insert  →  leakage audit  →  literature pass
```

### Spreadsheet columns (export from `templates/program_curation.csv`)

`candidate_id, program_id, ticker, drug_name, indication, primary_nct_id, t0_date, t0_source, clinical_success, failure_type, event_date, cohort_status, notes`

---

## Verification checklist (per program)

- [ ] NCT exists and phase includes Phase 2
- [ ] Start date within 2010–2020 (or holdout 2019–2020)
- [ ] Sponsor maps to U.S. ticker with trading history
- [ ] Outcome adjudicated with primary source URL
- [ ] PubMed search log saved (query + date filter ≤ t0)
- [ ] At least one pre-t0 animal paper **or** documented zero-result search
- [ ] Leakage audit pass

---

## Known gaps (honest assessment)

- **NCT IDs marked TBD** must be resolved — do not model until set
- Some candidates may fail inclusion (combination-only, t0 ambiguity)
- Delisted tickers (LOXO, IMMU, CELG) require historical symbol mapping
- CAR-T programs may lack traditional xenograft efficacy in public lit — document as stratum

---

## Config linkage

Program-level machine-readable status: `configs/cohort_mvp.yaml`

After verification, set:

```yaml
cohort_status: included  # pending | included | excluded
primary_nct_id: NCTxxxxxxxx
t0_date: YYYY-MM-DD
```
