"""Unified price history fetch + parquet cache."""

from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd

from src.config import load_yaml, project_root
from src.market_data.adapters.base import PriceAdapter
from src.market_data.adapters.yfinance_adapter import YFinanceAdapter


def get_adapter(provider: str | None = None) -> PriceAdapter:
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    name = provider or cfg["market_data"]["default_provider"]
    if name == "yfinance":
        return YFinanceAdapter()
    if name == "polygon":
        from src.market_data.adapters.polygon_adapter import PolygonAdapter

        return PolygonAdapter()
    if name == "eodhd":
        from src.market_data.adapters.eodhd_adapter import EodhdAdapter

        return EodhdAdapter()
    if name == "crsp":
        from src.market_data.adapters.crsp_adapter import CRSPAdapter

        return CRSPAdapter()
    if name == "local_csv":
        from src.market_data.adapters.local_csv_adapter import LocalCsvAdapter

        return LocalCsvAdapter()
    if name == "stooq":
        from src.market_data.adapters.stooq_adapter import StooqAdapter

        return StooqAdapter()
    raise ValueError(f"Unknown price provider: {name}")


def _fallback_fetch(
    ticker: str,
    start: str,
    end: str | None,
    primary_provider: str | None,
) -> tuple[pd.DataFrame, PriceAdapter]:
    """Try alternate adapters when the primary returns no bars."""
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    primary = primary_provider or cfg["market_data"]["default_provider"]
    chain = (
        ["local_csv", "stooq", "eodhd", "polygon", "yfinance"]
        if primary == "yfinance"
        else ["polygon", "eodhd", "stooq", "local_csv", "yfinance"]
    )

    for name in chain:
        if name == primary:
            continue
        try:
            adapter = get_adapter(name)
            if not adapter.supports_ticker(ticker):
                continue
            df = adapter.fetch_daily(ticker, start=start, end=end)
            if not df.empty:
                return df, adapter
        except Exception:
            continue
    return pd.DataFrame(), get_adapter(primary)


def cache_dir() -> Path:
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    return project_root() / cfg["market_data"]["cache_dir"]


def fetch_or_load(
    ticker: str,
    start: str,
    end: str | None = None,
    provider: str | None = None,
    force_refresh: bool = False,
) -> pd.DataFrame:
    adapter = get_adapter(provider)
    path = adapter.cache_path(cache_dir(), ticker)
    start_ts = pd.Timestamp(start) if start else None

    if path.exists() and not force_refresh:
        df = pd.read_parquet(path)
        df["date"] = pd.to_datetime(df["date"])
        if not df.empty:
            cache_covers_start = start_ts is None or df["date"].min() <= start_ts
            if cache_covers_start:
                if end:
                    end_ts = pd.Timestamp(end)
                    return df[df["date"] <= end_ts].copy()
                return df
            # Cache exists but starts too late for requested range — refetch below

    df = adapter.fetch_daily(ticker, start=start, end=end)
    if df.empty:
        df, adapter = _fallback_fetch(ticker, start, end, provider)
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    path = adapter.cache_path(cache_dir(), ticker)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return df


def returns_series(ticker: str, start: str, end: str | None = None) -> pd.Series:
    df = fetch_or_load(ticker, start=start, end=end)
    if df.empty:
        return pd.Series(dtype=float)
    s = df.set_index("date")["adj_close"].astype(float).pct_change().dropna()
    s.name = ticker
    return s


def load_benchmarks(start: str | None = None) -> dict[str, pd.Series]:
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    start = start or cfg["market_data"]["history_start"]
    out: dict[str, pd.Series] = {}
    for t in cfg["market_data"]["benchmark_tickers"]:
        out[t] = returns_series(t, start=start)
    return out


def persist_bars_to_db(
    conn,
    ticker: str,
    df: pd.DataFrame,
    provider: str,
) -> int:
    """Write OHLCV rows to market_bars_daily."""
    if df.empty:
        return 0
    n = 0
    for _, row in df.iterrows():
        conn.execute(
            """
            INSERT OR IGNORE INTO market_bars_daily (
                bar_id, ticker, date, open, high, low, close, adj_close, volume, provider
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                ticker.upper(),
                str(row["date"])[:10],
                row.get("open"),
                row.get("high"),
                row.get("low"),
                row.get("close"),
                row.get("adj_close"),
                row.get("volume"),
                provider,
            ),
        )
        n += 1
    return n
