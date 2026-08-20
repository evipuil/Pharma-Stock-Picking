# Data Sources & APIs

Public/free sources first. Paid or uncertain sources explicitly marked.

---

## Summary matrix

| Domain | Source | Access | Cost | Historical depth | Automation | Reliability |
|--------|--------|--------|------|------------------|------------|-------------|
| Clinical trials | ClinicalTrials.gov API v2 | Public | Free | Full | **High** | High |
| Literature metadata | PubMed E-utilities | Public | Free | Full | **High** | High |
| Full text | PMC Open Access | Public | Free | Partial | Medium | Medium |
| DOI metadata | Crossref REST | Public | Free | Full | **High** | High |
| Europe full text | Europe PMC API | Public | Free | Partial | Medium | Medium |
| SEC filings | EDGAR full-text search | Public | Free | Full | Medium | High |
| Stock prices | Yahoo Finance (yfinance) | Public | Free* | ~1990s+ | **High** | Medium |
| Sector ETF | XBI, IBB via yfinance | Public | Free* | ETF inception | **High** | Medium |
| Fama-French | Ken French data library | Public | Free | Full | Medium | High |
| PoS benchmarks | Wong 2019 supplementary | Academic | Free | 2000–2015 | Manual | High |
| PoS benchmarks | BIO/Informa reports | Industry | **Paid** | 2011–2020 | Manual | High |
| Analyst estimates | Refinitiv/FactSet | Commercial | **Paid** | Limited | Low | — |
| Options-implied | OptionMetrics/IQFeed | Commercial | **Paid** | Variable | Low | — |
| Press releases | Company IR pages | Public | Free | Variable | Low | Medium |
| Conference abstracts | ASCO/ASH abstracts | Mixed | Free/paid | Variable | Low | Medium |

\* Yahoo Finance is unofficial; validate against CRSP/Compustat for publication (paid).

---

## ClinicalTrials.gov API v2

- **Base URL:** `https://clinicaltrials.gov/api/v2/studies`
- **Docs:** https://clinicaltrials.gov/data-api/api
- **Key fields:** NCT ID, phases, conditions, interventions, dates, status, results
- **Rate limit:** Be polite; ~1 req/s recommended
- **Notes:**
  - `resultsSection` only populated for subset — many trials lack posted results
  - `startDate` vs `primaryCompletionDate` — use for t0 with documented rule
  - Sponsor name may not match public ticker — manual mapping required

**Implementation:** `src/clinical_trials/ctgov_client.py`

---

## PubMed / NCBI E-utilities

- **Search:** `esearch.fcgi` → PMIDs
- **Fetch:** `efetch.fcgi` → XML metadata
- **API key:** Optional (raises rate limits)
- **Key fields:** Title, abstract, authors, journal, PubDate, epub date, MeSH
- **Limitations:**
  - Full text not in PubMed — link to PMC via `elink`
  - Author keywords unreliable for animal study detection
  - Date ambiguity common

**Implementation:** `src/literature/pubmed_client.py`

---

## Crossref

- **URL:** `https://api.crossref.org/works/{doi}`
- **Use:** Resolve DOI → online-first vs print dates
- **Polite pool:** Include mailto in User-Agent

**Implementation:** `src/literature/crossref_client.py`

---

## Europe PMC

- **URL:** `https://www.ebi.ac.uk/europepmc/webservices/rest/search`
- **Use:** Full-text search, OA XML retrieval
- **Good for:** Open-access animal study sections

---

## SEC EDGAR

- **Search:** `https://efts.sec.gov/LATEST/search-index` or full-text API
- **Use:** 8-K clinical readouts, 10-K pipeline disclosures
- **CIK lookup:** `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}`
- **Limitations:** Event date precision; narrative not structured

---

## Market data

### Yahoo Finance (MVP)

```python
import yfinance as yf
yf.download("XBI", start="2010-01-01", auto_adjust=True)
```

- **Tickers:** Program sponsor + XBI/IBB/SPY
- **Adjustments:** Use auto-adjusted close for splits
- **Gaps:** Delisted tickers may be incomplete — document coverage

### Ken French factors

- **URL:** https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
- **Use:** Optional FF3/Fama-French for abnormal return robustness

---

## Benchmark probability-of-success tables

### Wong, Siah & Lo (2019)

- **Source:** Biostatistics + supplementary materials
- **Fields:** Phase, disease group, biomarker selection
- **Action:** Manually transcribe to `data/external/wong2019_pos_rates.csv`
- **Citation required for publication**

### BIO/Informa/QLS 2011–2020

- **Access:** **Paid report** (~$thousands)
- **Workaround:** Use published summaries in press releases/slide decks; mark uncertainty
- **Alternative free proxy:** Hay et al. Nature Biotechnology 2014 updates (older)

---

## Event date sources (priority)

1. Company press release (IR site) — store URL + datetime
2. SEC 8-K Item 8.01
3. CT.gov `resultsFirstPostDate` (often later than market reaction)
4. Major media (Reuters) — backup only

**Uncertain:** Intraday announcement time often unavailable historically → use close-to-close windows; robustness with [0,+1] vs [-1,+1].

---

## Data we cannot reliably reconstruct (MVP)

| Data | Issue |
|------|-------|
| Historical options-implied move | Requires OptionMetrics |
| Real-time analyst success probabilities | Not archived consistently pre-2018 |
| Private pre-t0 internal reports | Not public |
| Exact FPI dates for all trials | Often undisclosed; proxy trial start |
| Complete animal study data in paywalled papers | Manual access via institutional login |
| Historical short interest / borrow | Paid data |

---

## Storage conventions

```
data/raw/ctgov/{nct_id}.json
data/raw/pubmed/{pmid}.xml
data/raw/sec/{cik}/{accession}.txt
data/raw/market/{ticker}.parquet
data/external/benchmark_pos_rates.csv
```

Each file referenced from `source_records.raw_storage_path`.

---

## API keys (optional)

Store in `.env` (gitignored):

```
NCBI_API_KEY=
SEC_USER_AGENT=YourName your@email.com
```

Never commit credentials.
