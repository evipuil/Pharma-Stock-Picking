"""Local CSV price adapter for delisted tickers (Polygon/CRSP exports)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import project_root
from src.market_data.adapters.base import PriceAdapter


class LocalCsvAdapter(PriceAdapter):
    """
    Read daily OHLCV from data/external/prices/{TICKER}.csv.

    Expected columns (case-insensitive): date, open, high, low, close,
    adj_close (or adj close), volume.

    Populate via Polygon export, CRSP extract, or manual curation.
    """

    name = "local_csv"

    def __init__(self, prices_dir: Path | None = None) -> None:
        self.prices_dir = prices_dir or project_root() / "data" / "external" / "prices"

    def supports_ticker(self, ticker: str) -> bool:
        return self._csv_path(ticker).exists()

    def fetch_daily(
        self,
        ticker: str,
        start: str,
        end: str | None = None,
    ) -> pd.DataFrame:
        path = self._csv_path(ticker)
        if not path.exists():
            return _empty_frame()

        df = pd.read_csv(path)
        df.columns = [str(c).strip().lower() for c in df.columns]
        rename = {"adj close": "adj_close", "adjclose": "adj_close"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

        if "date" not in df.columns:
            return _empty_frame()

        df["date"] = pd.to_datetime(df["date"])
        if "adj_close" not in df.columns and "close" in df.columns:
            df["adj_close"] = df["close"]

        start_ts = pd.Timestamp(start) if start else None
        if start_ts is not None:
            df = df[df["date"] >= start_ts]
        if end:
            df = df[df["date"] <= pd.Timestamp(end)]

        cols = [
            c
            for c in ["date", "open", "high", "low", "close", "adj_close", "volume"]
            if c in df.columns
        ]
        return df[cols].sort_values("date").reset_index(drop=True)

    def _csv_path(self, ticker: str) -> Path:
        return self.prices_dir / f"{ticker.upper()}.csv"


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["date", "open", "high", "low", "close", "adj_close", "volume"]
    )
