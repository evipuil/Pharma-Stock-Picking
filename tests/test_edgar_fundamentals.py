"""Tests for SEC EDGAR point-in-time fundamentals."""

from datetime import date
from unittest.mock import MagicMock, patch

from src.fundamentals.point_in_time import _dependency_from_market_cap, extract_point_in_time


def test_dependency_from_market_cap_buckets():
    assert _dependency_from_market_cap(100e9) == 0.15
    assert _dependency_from_market_cap(10e9) == 0.45
    assert _dependency_from_market_cap(500e6) == 0.85


def test_extract_point_in_time_picks_pre_cutoff():
    facts = {
        "facts": {
            "us-gaap": {
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {
                        "USD": [
                            {"val": 100, "end": "2018-06-30", "filed": "2018-08-01", "form": "10-Q"},
                            {"val": 200, "end": "2019-06-30", "filed": "2019-08-01", "form": "10-Q"},
                        ]
                    }
                }
            }
        }
    }
    pit = extract_point_in_time(facts, date(2019, 1, 15))
    assert pit["cash_usd"] == 100
