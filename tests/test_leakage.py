"""Tests for leakage prevention utilities."""

from datetime import date

from src.validation.leakage import effective_public_date


def test_effective_public_date_uses_earlier_online_first():
    eff = effective_public_date(
        publication_date=date(2015, 6, 1),
        online_first_date=date(2015, 3, 1),
    )
    assert eff == date(2015, 3, 1)


def test_effective_public_date_single_date():
    eff = effective_public_date(publication_date=date(2014, 1, 15), online_first_date=None)
    assert eff == date(2014, 1, 15)


def test_effective_public_date_none():
    assert effective_public_date(None, None) is None
