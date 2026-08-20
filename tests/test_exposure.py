"""Tests for exposure classification."""

from src.fundamentals.exposure import classify_ticker


def test_large_pharma_low_dependency():
    cls, dep = classify_ticker("PFE")
    assert cls == "large_pharma"
    assert dep < 0.3


def test_unknown_ticker_high_dependency():
    cls, dep = classify_ticker("ONCY")
    assert cls == "small_cap"
    assert dep > 0.8
