"""SEC EDGAR API client for company facts and CIK lookup."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

from src.config import load_yaml, project_root

_CACHE_DIR = project_root() / "data" / "external" / "sec_cache"
_TICKER_CIK_URL = "https://www.sec.gov/files/company_tickers.json"
_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"


def _user_agent() -> str:
    cfg = load_yaml(project_root() / "configs" / "data_sources.yaml")
    return os.environ.get("SEC_EDGAR_USER_AGENT") or cfg["sec_edgar"]["user_agent"]


def _get(url: str, cache_name: str | None = None) -> dict:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _CACHE_DIR / cache_name if cache_name else None
    if cache_path and cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    resp = requests.get(url, headers={"User-Agent": _user_agent()}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if cache_path:
        cache_path.write_text(json.dumps(data), encoding="utf-8")
    time.sleep(0.12)  # SEC fair-use pacing
    return data


def load_ticker_cik_map(force_refresh: bool = False) -> dict[str, int]:
    """Return upper-case ticker → CIK integer."""
    cache_path = _CACHE_DIR / "company_tickers.json"
    if force_refresh and cache_path.exists():
        cache_path.unlink()
    raw = _get(_TICKER_CIK_URL, "company_tickers.json")
    out: dict[str, int] = {}
    for entry in raw.values():
        ticker = str(entry.get("ticker", "")).upper()
        cik = int(entry["cik_str"])
        if ticker:
            out[ticker] = cik
    return out


def lookup_cik(ticker: str, ticker_map: dict[str, int] | None = None) -> int | None:
    ticker_map = ticker_map or load_ticker_cik_map()
    return ticker_map.get(ticker.upper())


def fetch_company_facts(cik: int) -> dict:
    return _get(_COMPANY_FACTS_URL.format(cik=cik), f"companyfacts_{cik:010d}.json")
