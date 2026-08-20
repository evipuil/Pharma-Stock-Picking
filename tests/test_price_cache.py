"""Tests for price cache coverage logic."""

from pathlib import Path

import pandas as pd

from src.market_data.history import fetch_or_load


def test_cache_refetch_when_starts_too_late(tmp_path, monkeypatch):
    cache_root = tmp_path / "market_history" / "yfinance"
    cache_root.mkdir(parents=True)
    ticker = "TEST"
    cache_path = cache_root / f"{ticker}.parquet"

    # Cache only has 2015+ data
    pd.DataFrame(
        {
            "date": pd.date_range("2015-01-01", periods=10, freq="B"),
            "open": 1.0,
            "high": 1.0,
            "low": 1.0,
            "close": 1.0,
            "adj_close": 1.0,
            "volume": 1000,
        }
    ).to_parquet(cache_path, index=False)

    calls: list[str] = []

    class FakeAdapter:
        name = "yfinance"

        def supports_ticker(self, ticker: str) -> bool:
            return True

        def cache_path(self, cache_dir: Path, ticker: str) -> Path:
            return cache_dir / "yfinance" / f"{ticker.upper()}.parquet"

        def fetch_daily(self, ticker: str, start: str, end: str | None = None) -> pd.DataFrame:
            calls.append(start)
            return pd.DataFrame(
                {
                    "date": pd.date_range(start, periods=20, freq="B"),
                    "open": 1.0,
                    "high": 1.0,
                    "low": 1.0,
                    "close": 1.0,
                    "adj_close": 1.0,
                    "volume": 1000,
                }
            )

    import src.market_data.history as hist

    monkeypatch.setattr(hist, "get_adapter", lambda provider=None: FakeAdapter())
    monkeypatch.setattr(hist, "cache_dir", lambda: tmp_path / "market_history")
    monkeypatch.setattr(hist, "_fallback_fetch", lambda *a, **k: (pd.DataFrame(), FakeAdapter()))

    df = fetch_or_load(ticker, start="2010-01-01")
    assert not df.empty
    assert df["date"].min() <= pd.Timestamp("2010-01-01")
    assert calls  # refetched because cache started at 2015
