"""Market data download utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def download_adj_close(ticker: str, start: str, end: str | None = None) -> pd.DataFrame:
    import yfinance as yf

    data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if data.empty:
        return pd.DataFrame(columns=["date", "adj_close", "volume"])

    out = data.reset_index()

    # Flatten MultiIndex columns from newer yfinance (e.g. ('Close', 'SPY'))
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [
            str(c[0]).lower() if isinstance(c, tuple) else str(c).lower() for c in out.columns
        ]
    else:
        out.columns = [str(c).lower() for c in out.columns]

    if "close" in out.columns:
        out = out.rename(columns={"close": "adj_close"})
    elif "adj close" in out.columns:
        out = out.rename(columns={"adj close": "adj_close"})

    cols = [c for c in ["date", "adj_close", "volume"] if c in out.columns]
    return out[cols].copy()


def cache_ticker(ticker: str, start: str, out_dir: Path) -> Path:
    df = download_adj_close(ticker, start=start)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{ticker}.parquet"
    df.to_parquet(path, index=False)
    return path
