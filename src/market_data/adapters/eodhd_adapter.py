"""EODHD price adapter (delisted + active US equities; requires EODHD_API_KEY)."""

from __future__ import annotations

import os
from datetime import date

import pandas as pd
import requests

from src.market_data.adapters.base import MissingCredentialsError, PriceAdapter


class EodhdAdapter(PriceAdapter):
    """
    EOD Historical Data daily OHLCV.

    Setup:
      export EODHD_API_KEY=your_key
      https://eodhd.com/register
    """

    name = "eodhd"
    BASE_URL = "https://eodhd.com/api/eod"

    def __init__(self, api_key: str | None = None, timeout: int = 30) -> None:
        self.api_key = api_key or os.environ.get("EODHD_API_KEY") or os.environ.get(
            "EODHD_API_TOKEN"
        )
        self.timeout = timeout

    def supports_ticker(self, ticker: str) -> bool:
        return bool(self.api_key and ticker)

    def _symbol(self, ticker: str) -> str:
        t = ticker.upper()
        return t if "." in t else f"{t}.US"

    def fetch_daily(
        self,
        ticker: str,
        start: str,
        end: str | None = None,
    ) -> pd.DataFrame:
        if not self.api_key:
            raise MissingCredentialsError(
                "EodhdAdapter requires EODHD_API_KEY. "
                "Register free at https://eodhd.com/register"
            )

        end_str = end or date.today().isoformat()
        url = (
            f"{self.BASE_URL}/{self._symbol(ticker)}"
            f"?from={start}&to={end_str}&period=d&fmt=json&api_token={self.api_key}"
        )
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()
        if not isinstance(payload, list) or not payload:
            return _empty_frame()

        rows = []
        for bar in payload:
            rows.append(
                {
                    "date": pd.to_datetime(bar["date"]),
                    "open": bar.get("open"),
                    "high": bar.get("high"),
                    "low": bar.get("low"),
                    "close": bar.get("close"),
                    "adj_close": bar.get("adjusted_close", bar.get("close")),
                    "volume": bar.get("volume"),
                }
            )
        return pd.DataFrame(rows)


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["date", "open", "high", "low", "close", "adj_close", "volume"]
    )
