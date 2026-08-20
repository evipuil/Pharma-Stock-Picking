"""Tests for local CSV price adapter."""

from pathlib import Path

import pandas as pd

from src.market_data.adapters.local_csv_adapter import LocalCsvAdapter


def test_local_csv_reads_ohlcv(tmp_path: Path):
    prices_dir = tmp_path / "prices"
    prices_dir.mkdir()
    csv_path = prices_dir / "PCYC.csv"
    pd.DataFrame(
        {
            "Date": ["2012-01-03", "2012-01-04", "2012-12-07"],
            "Open": [50.0, 51.0, 90.0],
            "High": [52.0, 53.0, 95.0],
            "Low": [49.0, 50.0, 88.0],
            "Close": [51.0, 52.0, 92.0],
            "Adj Close": [51.0, 52.0, 92.0],
            "Volume": [100000, 110000, 500000],
        }
    ).to_csv(csv_path, index=False)

    adapter = LocalCsvAdapter(prices_dir=prices_dir)
    assert adapter.supports_ticker("PCYC")

    df = adapter.fetch_daily("PCYC", start="2012-01-01", end="2012-12-31")
    assert len(df) == 3
    assert "adj_close" in df.columns
    assert df["adj_close"].iloc[-1] == 92.0


def test_local_csv_missing_returns_empty(tmp_path: Path):
    adapter = LocalCsvAdapter(prices_dir=tmp_path / "prices")
    assert not adapter.supports_ticker("MISSING")
    assert adapter.fetch_daily("MISSING", start="2010-01-01").empty
