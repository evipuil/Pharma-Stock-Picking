# GitHub Data Import Report

**Command:** `python -m src.cli seed-github-data`  
**Output root:** `data/external/github/`  
**Summary JSON:** `data/external/github/import_summary.json`

---

## Imported sources

| Source | Location | Records | Notes |
|--------|----------|---------|-------|
| **ejeej/EventsStockPrices** | `EventsStockPrices/events.csv` | **3,810 events**, 567 tickers | BioPharmCatalyst events 2009–2022 |
| Clinical subset | `EventsStockPrices/clinical_phase_events.csv` | **2,288** Phase 1/2/3 events | Filtered for trial readouts |
| **BlackFalconData** (Apify sample) | `BlackFalconData/delisted_stocks_sample.csv` | **200** delistings | Free public sample; full 36k+ is Apify-paid |
| **HoleyHan/pystock-data** | `data/external/prices/*.csv` | **20 tickers** | OHLCV through **2017-03-31** |
| Mirror | `pystock-data/prices_mirror/` | 20 CSV copies | Audit copy of price exports |

---

## EventsStockPrices schema

| Column | Description |
|--------|-------------|
| ticker | US ticker symbol |
| drug | Drug name |
| disease | Indication |
| stage | Event type (Phase 2, Phase 3, PDUFA, Approved, CRL, etc.) |
| event_date | Parsed announcement/event date |
| event_desc | Free-text description |
| stage_normalized | Raw stage string |

**Potential uses:**
- Independent catalyst date validation vs CT.gov proxies
- Cohort expansion candidates (567 tickers with dated events)
- Human-readable event classification for short-edge research

---

## Delisted sample schema (BlackFalcon / Apify)

Key fields: `ticker`, `issuerName`, `cik`, `formType`, `fileDate`, `effectiveDelistingDate`, `exchange`, `filingUrl`

**Limitation:** GitHub repo contains README only; this CSV is the linked **200-record free sample**. Full survivorship-bias correction requires Apify actor subscription.

---

## Pystock prices

Still ends **2017-03-31** — does **not** close CLVS/MRTX/SGEN/OMED gaps for 2018–2022 events.

---

## Re-import

```bash
python -m src.cli seed-github-data          # skip existing files
python -m src.cli seed-github-data --force  # re-download all
```
