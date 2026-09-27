"""Download and normalize public datasets from GitHub (and linked free archives)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from src.config import project_root
from src.market_data.seed_pystock import DEFAULT_TICKERS, seed_pystock_prices

GITHUB_ROOT = project_root() / "data" / "external" / "github"

EVENTS_XLSX_URL = (
    "https://raw.githubusercontent.com/ejeej/EventsStockPrices/main/EventsStockPricesApp/Events.xlsx"
)
APIFY_DELISTED_SAMPLE = "https://api.apify.com/v2/datasets/nKdbdRjuYPmBDPNJT/items"


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def download_events_stock_prices(force: bool = False) -> dict:
    """BioPharmCatalyst events 2017–2022 from ejeej/EventsStockPrices."""
    out_dir = _ensure_dir(GITHUB_ROOT / "EventsStockPrices")
    xlsx_path = out_dir / "Events.xlsx"
    csv_path = out_dir / "events.csv"
    meta_path = out_dir / "manifest.json"

    if not xlsx_path.exists() or force:
        resp = requests.get(EVENTS_XLSX_URL, timeout=120)
        resp.raise_for_status()
        xlsx_path.write_bytes(resp.content)

    df = pd.read_excel(xlsx_path, engine="openpyxl")
    df.columns = ["ticker", "drug", "disease", "stage", "event_date", "event_desc"]

    # Match app.R date parsing (Excel serial or m/d/Y strings)
    def _parse_date(val):
        if pd.isna(val):
            return pd.NaT
        if isinstance(val, (pd.Timestamp, datetime)):
            return pd.Timestamp(val)
        s = str(val)
        if "/" in s:
            return pd.to_datetime(s, format="%m/%d/%Y", errors="coerce")
        try:
            num = float(val)
            return pd.to_datetime(num, unit="D", origin="1899-12-30")
        except (ValueError, TypeError):
            return pd.to_datetime(val, errors="coerce")

    df["event_date"] = df["event_date"].map(_parse_date)
    df["stage_normalized"] = df["stage"].astype(str).str.strip()
    df["source"] = "ejeej/EventsStockPrices"
    df["source_url"] = "https://github.com/ejeej/EventsStockPrices"
    df.to_csv(csv_path, index=False)

    # Phase 2/3 clinical catalyst subset
    phase_mask = df["stage_normalized"].str.contains(
        r"Phase\s*[23]", case=False, na=False, regex=True
    )
    clinical = df[phase_mask].copy()
    clinical_path = out_dir / "clinical_phase_events.csv"
    clinical.to_csv(clinical_path, index=False)

    meta = {
        "source": "ejeej/EventsStockPrices",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_events": len(df),
        "n_tickers": int(df["ticker"].nunique()),
        "date_min": str(df["event_date"].min()),
        "date_max": str(df["event_date"].max()),
        "n_clinical_phase_events": len(clinical),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def download_apify_delisted_sample(limit: int = 200, force: bool = False) -> dict:
    """
    Free 200-record sample linked from BlackFalconData-org/delisted-stocks-list README.
    Full 36k+ dataset requires Apify actor (paid beyond sample).
    """
    out_dir = _ensure_dir(GITHUB_ROOT / "BlackFalconData")
    json_path = out_dir / "delisted_stocks_sample.json"
    csv_path = out_dir / "delisted_stocks_sample.csv"
    meta_path = out_dir / "manifest.json"

    if json_path.exists() and not force:
        rows = json.loads(json_path.read_text(encoding="utf-8"))
    else:
        rows: list[dict] = []
        offset = 0
        page = min(limit, 1000)
        while len(rows) < limit:
            resp = requests.get(
                APIFY_DELISTED_SAMPLE,
                params={"format": "json", "limit": page, "offset": offset},
                timeout=60,
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            rows.extend(batch)
            if len(batch) < page:
                break
            offset += page
        rows = rows[:limit]
        json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    meta = {
        "source": "BlackFalconData/delisted-stocks-list (Apify public sample)",
        "sample_url": "https://console.apify.com/storage/datasets/nKdbdRjuYPmBDPNJT",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_records": len(df),
        "note": "Sample only; full 36k+ via Apify actor",
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def download_pystock_readme() -> Path:
    """Cache HoleyHan/pystock-data README for provenance."""
    out_dir = _ensure_dir(GITHUB_ROOT / "pystock-data")
    readme = out_dir / "README.md"
    if not readme.exists():
        url = "https://raw.githubusercontent.com/HoleyHan/pystock-data/gh-pages/README.md"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        readme.write_text(resp.text, encoding="utf-8")
    return readme


def seed_all_github_sources(
    force: bool = False,
    pystock_tickers: set[str] | None = None,
) -> dict:
    """Download all available GitHub-linked public datasets."""
    stats: dict = {"started_at_utc": datetime.now(timezone.utc).isoformat()}

    stats["events_stock_prices"] = download_events_stock_prices(force=force)
    stats["apify_delisted_sample"] = download_apify_delisted_sample(force=force)
    stats["pystock_readme"] = str(download_pystock_readme())

    tickers = pystock_tickers or set(DEFAULT_TICKERS)
    stats["pystock_prices"] = seed_pystock_prices(tickers=tickers, force=force)

    # Copy normalized price CSVs into github mirror folder for audit
    prices_src = project_root() / "data" / "external" / "prices"
    prices_mirror = _ensure_dir(GITHUB_ROOT / "pystock-data" / "prices_mirror")
    copied = 0
    for csv in prices_src.glob("*.csv"):
        if csv.name.upper().replace(".CSV", "") in {t.upper() for t in tickers}:
            shutil.copy2(csv, prices_mirror / csv.name)
            copied += 1
    stats["prices_mirrored"] = copied

    stats["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    summary_path = GITHUB_ROOT / "import_summary.json"
    summary_path.write_text(json.dumps(stats, indent=2, default=str), encoding="utf-8")
    return stats
