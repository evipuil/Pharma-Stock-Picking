"""Polygon.io price adapter (requires POLYGON_API_KEY for delisted/historical US equities)."""

from __future__ import annotations

import os
from datetime import date

import pandas as pd
import requests

from src.market_data.adapters.base import MissingCredentialsError, PriceAdapter


class PolygonAdapter(PriceAdapter):
    """
    Polygon.io daily aggregates.

    Setup:
      export POLYGON_API_KEY=your_key
      https://polygon.io/pricing
    """

    name = "polygon"
    BASE_URL = "https://api.polygon.io/v2/aggs/ticker"

    def __init__(self, api_key: str | None = None, timeout: int = 30) -> None:
        self.api_key = api_key or os.environ.get("POLYGON_API_KEY")
        self.timeout = timeout

    def supports_ticker(self, ticker: str) -> bool:
        return bool(self.api_key and ticker)

    def fetch_daily(
        self,
        ticker: str,
        start: str,
        end: str | None = None,
    ) -> pd.DataFrame:
        if not self.api_key:
            raise MissingCredentialsError(
                "PolygonAdapter requires POLYGON_API_KEY. "
                "Set env var or pass api_key=. See docs/STOCK_PICKING_ARCHITECTURE.md"
            )

        end_str = end or date.today().isoformat()
        url = (
            f"{self.BASE_URL}/{ticker.upper()}/range/1/day/{start}/{end_str}"
            f"?adjusted=true&sort=asc&limit=50000&apiKey={self.api_key}"
        )
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("status") == "ERROR" or not payload.get("results"):
            return _empty_frame()

        rows = []
        for bar in payload["results"]:
            rows.append(
                {
                    "date": pd.to_datetime(bar["t"], unit="ms", utc=True).tz_convert(None),
                    "open": bar.get("o"),
                    "high": bar.get("h"),
                    "low": bar.get("l"),
                    "close": bar.get("c"),
                    "adj_close": bar.get("c"),
                    "volume": bar.get("v"),
                }
            )
        return pd.DataFrame(rows)


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["date", "open", "high", "low", "close", "adj_close", "volume"]
    )
