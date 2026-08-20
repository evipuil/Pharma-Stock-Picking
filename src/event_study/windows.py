"""Trading-day helpers and event window parsing."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

import pandas as pd


def parse_window(label: str) -> tuple[int, int]:
    """Parse '[-1,+1]' -> (-1, 1) trading-day offsets from event index."""
    m = re.match(r"\[([+-]?\d+),([+-]?\d+)\]", label.strip())
    if not m:
        raise ValueError(f"Invalid window label: {label}")
    return int(m.group(1)), int(m.group(2))


def window_slice(index: pd.DatetimeIndex, event_idx: int, start_off: int, end_off: int) -> pd.DatetimeIndex:
    lo = max(0, event_idx + start_off)
    hi = min(len(index) - 1, event_idx + end_off)
    if lo > hi:
        return index[:0]
    return index[lo : hi + 1]


def infer_trading_cutoff(
    announcement_date: date,
    timing: str = "UNKNOWN",
) -> tuple[date, date, date, str]:
    """
    Return (trading_cutoff, trading_day_before, first_trading_day_after, confidence).

    Without a full exchange calendar we approximate:
    - BMO: cutoff = prior calendar day (entry at prior close)
    - AMC: cutoff = announcement day close
    - DURING/UNKNOWN: prior calendar day (conservative)
    """
    timing = (timing or "UNKNOWN").upper()
    if timing == "AMC":
        cutoff = announcement_date
        confidence = "MEDIUM"
    else:
        cutoff = announcement_date - timedelta(days=1)
        confidence = "HIGH" if timing == "BMO" else "LOW"
    day_before = cutoff
    day_after = announcement_date + timedelta(days=1)
    return cutoff, day_before, day_after, confidence


def nearest_trading_index(dates: pd.DatetimeIndex, target: date | datetime) -> int | None:
    if dates.empty:
        return None
    ts = pd.Timestamp(target)
    idx = dates.get_indexer([ts], method="nearest")[0]
    if idx < 0:
        return None
    return int(idx)
