# Public Data Inventory

**Generated:** 2026-08-19  
**Purpose:** Catalog free/public sources to expand catalyst coverage, fill delisted price gaps, and enrich human-evidence features.

Probe results: `data/processed/public_data_probe.json`  
Missing price requirements: `data/processed/missing_price_requirements.csv`

---

## Executive summary

| Need | Best free source | Gap |
|------|------------------|-----|
| **Delisted prices post-2017** | None fully free at API scale | CLVS, MRTX, SGEN, OMED stop at 2017-03-31 in pystock |
| **Catalyst dates** | SEC 8-K + company IR | Partially wired; EFTS can be flaky |
| **Trial design / NCT** | ClinicalTrials.gov v2 | **Already integrated** — 123 NCT JSON cached |
| **Human efficacy (ORR/PFS)** | CT.gov `resultsSection` | Sparse; many trials lack posted results |
| **Fundamentals / cash** | SEC EDGAR XBRL | **Partially integrated** — 48/112 catalysts |
| **Short interest / borrow** | FINRA API | Free with registration; not yet wired |
| **PoS benchmarks** | Wong 2019 CSV | Manual; BIO/Informa is paid |
| **Cohort expansion** | CT.gov search | Thousands of Ph2/3 oncology trials available |

**Bottom line:** The largest blocker remains **post-2017 delisted OHLCV**. Everything else has viable free public paths.

---

## 1. Price data (delisted gap)

### Currently in repo
| Source | Coverage | Cost | Status |
|--------|----------|------|--------|
| **yfinance** | Active tickers | Free | ✅ Integrated |
| **HoleyHan/pystock-data** | US equities → **2017-03-31** | Free (GitHub) | ✅ `seed-delisted-prices` |
| **local CSV** | `data/external/prices/*.csv` | Free | ✅ 21 tickers, truncated post-2017 |

### Missing tickers (need 2017–2022 history)
| Ticker | Latest event | Required through |
|--------|--------------|------------------|
| CLVS | 2018-08-24, 2022-06-08 | 2022-07 |
| MRTX | 2019-01-15 | 2019-02 |
| SGEN | 2019-01-08 | 2019-02 |
| OMED | 2017-04-10 | 2017-05 |

### Public / freemium options (not yet integrated)

| Source | URL | Free tier | Delisted? | Notes |
|--------|-----|-----------|-----------|-------|
| **Stooq** | https://stooq.com/q/d/l/ | Free w/ CAPTCHA API key | Often yes | As of 2026 requires `apikey` param; daily quota |
| **FMP** | https://site.financialmodelingprep.com | 250 req/day | Yes (delisted list endpoint) | Requires free API key |
| **EODHD** | https://eodhd.com | Limited free | **Yes — best delisted support** | Adapter exists; needs `EODHD_API_KEY` |
| **Polygon.io** | https://polygon.io | Limited free | Yes | Adapter exists; needs `POLYGON_API_KEY` |
| **Tiingo** | https://www.tiingo.com | Free tier | Some delisted | Not wired |
| **Alpha Vantage** | https://www.alphavantage.co | 25 req/day | Limited | Not wired |
| **Kaggle: Arandkei delisted archive** | https://www.kaggle.com/datasets/rodas86/arandkei-historical-delisted-assets-archive | Free w/ account | Yes | CC BY 4.0; manual download → local CSV |
| **Apify delisted SEC list** | https://apify.com/blackfalcondata/delisted-stocks-list | Sample free | Metadata only | 36k+ Form 25/15 filings since 2002; not OHLCV |
| **CRSP** | WRDS | **Paid (academic)** | Gold standard | Stub adapter only |

### Recommended action for 5 missing CARs
1. **Free:** Register Stooq or FMP free key → export CLVS/MRTX/SGEN/OMED for required date ranges → drop in `data/external/prices/`
2. **Paid (best):** EODHD All-World ($19.99/mo) or Polygon — run `python -m src.cli export-delisted-prices`
3. **Manual:** Kaggle Arandkei archive if tickers present

---

## 2. Catalyst & event dates (free)

| Source | API | Key? | Use case | Status |
|--------|-----|------|----------|--------|
| **SEC EDGAR EFTS** | `https://efts.sec.gov/LATEST/search-index` | No | 8-K "top-line results", "primary endpoint" | Config exists; probe hit 500 — retry with simpler queries |
| **SEC Submissions** | `https://data.sec.gov/submissions/CIK{cik}.json` | No | Filing dates, accession numbers | ✅ CIK map cached |
| **SEC CompanyFacts** | `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` | No | Cash, revenue, shares outstanding | ✅ `edgar_client.py` |
| **SEC company tickers** | `https://www.sec.gov/files/company_tickers.json` | No | Ticker ↔ CIK | ✅ 10,387 tickers probed OK |
| **ClinicalTrials.gov v2** | `https://clinicaltrials.gov/api/v2/studies` | No | Trial dates, phases, results | ✅ 123 studies cached |
| **openFDA Drugs@FDA** | `https://api.fda.gov/drug/drugsfda.json` | Optional | Approvals, sponsors, discontinuations | Not wired; 404 for pre-approval drugs |
| **openFDA FAERS** | `https://api.fda.gov/drug/event.json` | Optional | Safety signals | ✅ Probe OK |
| **NIH RePORTER** | `https://api.reporter.nih.gov/v2/projects/search` | No | Grant funding, sponsor activity | ✅ Probe OK; not wired |
| **PubMed E-utilities** | `https://eutils.ncbi.nlm.nih.gov/` | Optional | Prior trial publications | ✅ Integrated |
| **Europe PMC** | `https://www.ebi.ac.uk/europepmc/webservices/rest/search` | No | Full-text OA papers | Config only |
| **Crossref** | `https://api.crossref.org/works/{doi}` | No | Publication dates | ✅ Integrated |
| **Ken French factors** | Tuck Dartmouth ZIP | No | FF3 risk adjustment | ✅ Config; probe OK |

### High-value addition: SEC 8-K clinical readout miner
Search EFTS for biotech catalyst language on 8-K filings:
- `"top-line results"`, `"primary endpoint"`, `"did not meet"`, `"statistically significant"`
- Filter by CIK for cohort tickers
- Extract `file_date` as candidate announcement date (better than CT.gov `resultsFirstPostDate`)

### GitHub event datasets (free, manual import)
| Repo | Content | Period |
|------|---------|--------|
| **ejeej/EventsStockPrices** | BioPharmCatalyst events + Yahoo prices | 2017–2022 |
| **BlackFalconData/delisted-stocks-list** | SEC Form 25 delisting metadata | 2002–present |

---

## 3. Human evidence & efficacy benchmarks (free)

| Source | Fields | Limitation |
|--------|--------|------------|
| **CT.gov resultsSection** | ORR, PFS, OS, AE rates | Only ~30–40% of completed trials post results |
| **PubMed / Europe PMC** | Published Phase I/II readouts before Phase III | Manual NCT→PMID linking |
| **openFDA FAERS** | Adverse event rates post-approval | Not pre-catalyst |
| **Wong et al. 2019** | Indication-level PoS benchmarks | Manual CSV; 2000–2015 |
| **Hay et al. Nature Biotech** | Updated PoS tables | Manual transcription from paper |

### CT.gov expansion potential
Search returns **100+ studies per query** for "oncology phase 2" / "cancer phase 3 randomized" (client-side phase filter). This can expand cohort toward 250+ **without paid data**, provided:
- Sponsor → ticker mapping is curated
- Announcement dates come from SEC 8-K, not CT.gov alone

---

## 4. Market microstructure & short feasibility (free w/ registration)

| Source | Data | Registration |
|--------|------|--------------|
| **FINRA consolidated short interest** | `api.finra.org/.../consolidatedShortInterest` | Free FINRA developer account |
| **FINRA Reg SHO daily** | Short sale volume | Same |
| **SEC EDGAR** | Shares outstanding (for ADV proxy) | None |

Not yet integrated — would support liquidity/borrow filters in short-edge validation.

---

## 5. Already probed (2026-08-19)

| Source | Result |
|--------|--------|
| SEC company tickers | ✅ 10,387 entries |
| openFDA FAERS | ✅ Working |
| NIH RePORTER | ✅ Working |
| Ken French daily factors | ✅ HTTP 200 |
| yfinance CLVS/MRTX/SGEN/OMED post-2017 | ❌ Empty |
| Stooq CLVS 2017–2020 | ❌ 404 (needs API key format) |
| FMP delisted | ❌ 401 without key |
| FINRA short interest | ⚠️ 400 without proper auth/filters |
| CT.gov filtered bulk query | ⚠️ 400 — use `query.term` + client-side filter instead |

Full probe output: `data/processed/public_data_probe.json`

---

## 6. Recommended integration priority

### Tier 1 — Free, high impact (do next)
1. **SEC 8-K catalyst date miner** — improve announcement timing for all 112 catalysts
2. **CT.gov cohort candidate exporter** — pre-register expansion to 250+ trials
3. **FINRA short interest adapter** — borrow feasibility proxy
4. **Stooq or FMP free-tier adapter** — close 5 missing CARs without paid EODHD

### Tier 2 — Free, moderate effort
5. **NIH RePORTER** — funding/runway proxy for small biotech
6. **openFDA Drugs@FDA** — approval/discontinuation for large-cap controls
7. **Europe PMC full-text** — prior human evidence extraction
8. **Kaggle Arandkei bulk import script** — one-time delisted price backfill

### Tier 3 — Paid but best for production
9. **EODHD** — delisted EOD through acquisition dates (~$20/mo)
10. **CRSP via WRDS** — academic gold standard for event studies

---

## 7. Commands

```bash
# Re-probe public APIs
python scripts/probe_public_data.py

# Export missing price requirements
python -c "from src.short_edge.price_recovery import export_missing_price_requirements; print(export_missing_price_requirements())"

# Seed pystock (free, ends 2017-03-31)
python -m src.cli seed-delisted-prices

# With API key (paid/freemium)
export EODHD_API_KEY=...
python -m src.cli export-delisted-prices
```

---

## 8. What we cannot get for free

- Complete post-acquisition OHLCV for all delisted biotech without Stooq/FMP/EODHD/Polygon/CRSP
- Historical options-implied move (OptionMetrics)
- Point-in-time analyst success probabilities (Refinitiv/FactSet)
- Real-time borrow fees (S3 Partners, IBKR pro)
- BIO/Informa indication PoS tables (paid reports)
