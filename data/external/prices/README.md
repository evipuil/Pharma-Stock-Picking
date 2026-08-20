# Local price CSVs for delisted tickers

Place one file per ticker: `{TICKER}.csv` (e.g. `PCYC.csv`, `CELG.csv`).

Required columns (case-insensitive):

- `date`
- `close` (or `adj_close` / `Adj Close`)
- Optional: `open`, `high`, `low`, `volume`

Sources:

- Polygon.io daily aggregates export (set `POLYGON_API_KEY` and run `python -m src.cli export-delisted-prices`)
- EODHD daily EOD API (set `EODHD_API_KEY` and run the same command)
- CRSP daily stock file via WRDS
- Manual curation

The `local_csv` adapter is tried automatically after yfinance and Polygon in `fetch_or_load()`.
