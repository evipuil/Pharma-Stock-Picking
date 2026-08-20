"""Classify primary endpoint type from CT.gov outcome measure text."""

from __future__ import annotations

import re


def classify_endpoint(outcome_texts: list[str]) -> dict[str, int]:
    """Return binary flags for common endpoint families."""
    text = " ".join(outcome_texts).lower()
    return {
        "endpoint_os": int(bool(re.search(r"\boverall survival\b|\bos\b", text))),
        "endpoint_pfs": int(
            bool(re.search(r"\bprogression.free survival\b|\bpfs\b|\bprogression free\b", text))
        ),
        "endpoint_orr": int(
            bool(
                re.search(
                    r"\bobjective response\b|\borr\b|\bresponse rate\b|\boverall response\b",
                    text,
                )
            )
        ),
        "endpoint_safety": int(
            bool(re.search(r"\bsafety\b|\btolerability\b|\badverse event\b|\bmtb?d\b", text))
        ),
    }
