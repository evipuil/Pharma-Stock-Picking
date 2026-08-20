"""Seed delisted ticker prices from HoleyHan/pystock-data GitHub archives."""

from __future__ import annotations

import io
import sqlite3
import tarfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

from src.config import load_yaml, project_root

PYSTOCK_BASE = "https://raw.githubusercontent.com/HoleyHan/pystock-data/master"
INITIAL_ARCHIVES = ("0001_initial.tar.gz", "0002_initial.tar.gz", "0003_initial.tar.gz")
DEFAULT_TICKERS = (
    "PCYC",
    "CELG",
    "LOXO",
    "IMMU",
    "IMGN",
    "CLVS",
    "SGEN",
    "PTLA",
    "PPHM",
    "MRTX",
    "AVEO",
    "RXDX",
    "SNTA",
    "CTIC",
    "EPZM",
    "SGMO",
    "OCN",
    "CYTR",
    "STML",
    "OMED",
)


def _cache_dir() -> Path:
    path = project_root() / "data" / "external" / "pystock_cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _output_dir() -> Path:
    path = project_root() / "data" / "external" / "prices"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _download(url: str, dest: Path, timeout: int = 180) -> bool:
    if dest.exists() and dest.stat().st_size > 1000:
        return True
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200 or len(resp.content) < 1000:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(resp.content)
    return True


def _extract_prices(tar_bytes: bytes, tickers: set[str]) -> dict[str, pd.DataFrame]:
    found: dict[str, list[pd.DataFrame]] = defaultdict(list)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tf:
        for member in tf.getmembers():
            if not member.name.endswith("prices.csv"):
                continue
            f = tf.extractfile(member)
            if f is None:
                continue
            try:
                df = pd.read_csv(f)
            except pd.errors.EmptyDataError:
                continue
            if df.empty or "symbol" not in df.columns:
                continue
            sub = df[df["symbol"].isin(tickers)]
            for sym, grp in sub.groupby("symbol"):
                found[sym].append(grp)
    out: dict[str, pd.DataFrame] = {}
    for sym, parts in found.items():
        merged = pd.concat(parts, ignore_index=True)
        merged["date"] = pd.to_datetime(merged["date"])
        out[sym] = merged.drop_duplicates("date").sort_values("date")
    return out


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "date": df["date"],
            "open": df.get("open"),
            "high": df.get("high"),
            "low": df.get("low"),
            "close": df.get("close"),
            "adj_close": df.get("adj_close", df.get("close")),
            "volume": df.get("volume"),
        }
    )
    return out.sort_values("date").reset_index(drop=True)


def _required_end_dates(db_path: Path | None = None) -> dict[str, date]:
    """Latest catalyst event date (+ buffer) per resolved ticker candidate."""
    delist = load_yaml(project_root() / "configs" / "ticker_delist_map.yaml").get("tickers", {})
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """
        SELECT ct.ticker_at_event, c.announcement_date
        FROM catalysts c
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        WHERE c.announcement_date IS NOT NULL
        """
    ).fetchall()
    conn.close()

    from src.market_data.ticker_resolver import resolve_price_tickers

    ends: dict[str, date] = {}
    for ticker_at_event, ann in rows:
        if ticker_at_event.upper() not in delist and ticker_at_event.upper() not in DEFAULT_TICKERS:
            continue
        ann_d = date.fromisoformat(str(ann)[:10])
        for t in resolve_price_tickers(ticker_at_event, ann_d):
            if t not in DEFAULT_TICKERS and t not in delist:
                continue
            buffer = ann_d + timedelta(days=30)
            ends[t] = max(ends.get(t, ann_d), buffer)
    return ends


def _daily_archive_urls(start: date, end: date) -> list[tuple[str, str]]:
    """Return (year, filename) pairs for pystock daily archives in [start, end]."""
    urls: list[tuple[str, str]] = []
    cur = start
    while cur <= end:
        if cur.weekday() < 5:
            fname = f"{cur.strftime('%Y%m%d')}.tar.gz"
            urls.append((str(cur.year), fname))
        cur += timedelta(days=1)
    return urls


def _last_pystock_date() -> date:
    """Last available archive date in the public pystock-data repo."""
    for year in range(2020, 2014, -1):
        url = f"https://api.github.com/repos/HoleyHan/pystock-data/contents/{year}?per_page=100"
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            continue
        names = [
            item["name"]
            for item in resp.json()
            if item["name"].endswith(".tar.gz") and item["name"][:4].isdigit()
        ]
        if names:
            latest = max(names)
            return date.fromisoformat(f"{latest[:4]}-{latest[4:6]}-{latest[6:8]}")
    return date(2017, 3, 31)


def seed_pystock_prices(
    tickers: set[str] | None = None,
    db_path: Path | None = None,
    force: bool = False,
) -> dict:
    """
    Download pystock archives and write data/external/prices/{TICKER}.csv.

    Covers 2009-01-02 through ~2017-03 for delisted US biotech tickers.
    """
    tickers = set(tickers or DEFAULT_TICKERS)
    cache = _cache_dir()
    out_dir = _output_dir()
    required_ends = _required_end_dates(db_path)
    repo_end = _last_pystock_date()

    stats = {"initial_bars": 0, "daily_bars": 0, "exported": 0, "skipped": 0}

    combined: dict[str, list[pd.DataFrame]] = defaultdict(list)
    for fname in INITIAL_ARCHIVES:
        url = f"{PYSTOCK_BASE}/2015/{fname}"
        dest = cache / fname
        if not _download(url, dest):
            continue
        parts = _extract_prices(dest.read_bytes(), tickers)
        for sym, df in parts.items():
            combined[sym].append(df)
            stats["initial_bars"] += len(df)

    daily_start = date(2015, 3, 21)
    daily_end = min(repo_end, max(required_ends.values()) if required_ends else repo_end)
    for year, fname in _daily_archive_urls(daily_start, daily_end):
        url = f"{PYSTOCK_BASE}/{year}/{fname}"
        dest = cache / year / fname
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            if not _download(url, dest):
                continue
        except Exception:
            continue
        try:
            parts = _extract_prices(dest.read_bytes(), tickers)
        except (tarfile.ReadError, pd.errors.EmptyDataError):
            continue
        for sym, df in parts.items():
            combined[sym].append(df)
            stats["daily_bars"] += len(df)

    for sym in tickers:
        csv_path = out_dir / f"{sym}.csv"
        if sym not in combined:
            continue
        merged = pd.concat(combined[sym], ignore_index=True)
        merged["date"] = pd.to_datetime(merged["date"])
        merged = merged.drop_duplicates("date").sort_values("date")
        normalized = _normalize(merged)
        if csv_path.exists() and not force:
            existing = pd.read_csv(csv_path, parse_dates=["date"])
            normalized = (
                pd.concat([existing, normalized], ignore_index=True)
                .drop_duplicates("date")
                .sort_values("date")
            )
        normalized.to_csv(csv_path, index=False)
        stats["exported"] += 1

    stats["repo_end"] = repo_end.isoformat()
    stats["daily_end"] = daily_end.isoformat()
    return stats
