"""CRSP price adapter (STUB — requires WRDS/CRSP license)."""

from __future__ import annotations

import pandas as pd

from src.market_data.adapters.base import MissingCredentialsError, PriceAdapter


class CRSPAdapter(PriceAdapter):
    """
    CRSP daily stock file via WRDS or local extract.

    Setup:
      - WRDS account with CRSP access, OR
      - Local CRSP .csv extract mounted at data/external/crsp/

    Required for survivorship-bias-free delisted biotech history.
    """

    name = "crsp"

    def __init__(self, wrds_username: str | None = None) -> None:
        import os

        self.wrds_username = wrds_username or os.environ.get("WRDS_USERNAME")

    def supports_ticker(self, ticker: str) -> bool:
        return bool(ticker)

    def fetch_daily(
        self,
        ticker: str,
        start: str,
        end: str | None = None,
    ) -> pd.DataFrame:
        raise MissingCredentialsError(
            "CRSPAdapter requires WRDS CRSP access or a local CRSP extract. "
            "Configure WRDS_USERNAME or place data in data/external/crsp/. "
            "See docs/STOCK_PICKING_ARCHITECTURE.md"
        )
