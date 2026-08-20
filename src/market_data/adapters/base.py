"""Price data adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class PriceBar:
    ticker: str
    date: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    adj_close: float | None
    volume: float | None


class PriceAdapter(ABC):
    """Abstract daily OHLCV provider."""

    name: str

    @abstractmethod
    def fetch_daily(
        self,
        ticker: str,
        start: str,
        end: str | None = None,
    ) -> pd.DataFrame:
        """Return columns: date, open, high, low, close, adj_close, volume."""

    @abstractmethod
    def supports_ticker(self, ticker: str) -> bool:
        """Whether this adapter can serve the ticker (may still return empty)."""

    def cache_path(self, cache_dir: Path, ticker: str) -> Path:
        return cache_dir / self.name / f"{ticker.upper()}.parquet"


class MissingCredentialsError(RuntimeError):
    """Raised when a paid adapter is configured but credentials are absent."""
