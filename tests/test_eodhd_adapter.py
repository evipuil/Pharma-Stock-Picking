"""Tests for EODHD price adapter."""

from unittest.mock import MagicMock, patch

from src.market_data.adapters.eodhd_adapter import EodhdAdapter


def test_eodhd_fetch_parses_bars():
    adapter = EodhdAdapter(api_key="test-key")
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = [
        {
            "date": "2020-01-02",
            "open": 10.0,
            "high": 11.0,
            "low": 9.5,
            "close": 10.5,
            "adjusted_close": 10.5,
            "volume": 100000,
        }
    ]
    with patch("src.market_data.adapters.eodhd_adapter.requests.get", return_value=mock_resp):
        df = adapter.fetch_daily("CELG", start="2020-01-01", end="2020-01-31")

    assert len(df) == 1
    assert df["adj_close"].iloc[0] == 10.5
