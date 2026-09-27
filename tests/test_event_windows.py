"""Tests for event-window trading-session alignment."""

from datetime import date

import pandas as pd

from src.event_study.windows import first_trading_index_on_or_after


def test_weekend_event_uses_next_session_not_prior_session():
    sessions = pd.DatetimeIndex(["2024-01-05", "2024-01-08"])

    index = first_trading_index_on_or_after(sessions, date(2024, 1, 7))

    assert index == 1
    assert sessions[index] == pd.Timestamp("2024-01-08")


def test_event_after_available_prices_has_no_session():
    sessions = pd.DatetimeIndex(["2024-01-05", "2024-01-08"])

    assert first_trading_index_on_or_after(sessions, date(2024, 1, 9)) is None
