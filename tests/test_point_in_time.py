"""Tests for strict point-in-time feature provenance."""

import pandas as pd

from src.validation.point_in_time import (
    point_in_time_mask,
    sanitize_feature_family,
    summarize_point_in_time_audit,
)


def test_unverified_feature_family_is_nulled():
    frame = pd.DataFrame(
        {
            "feature_cutoff_date": ["2020-01-10", "2020-01-10", "2020-01-10"],
            "observed_at": ["2020-01-09", "2020-01-11", None],
            "feature": [1.0, 2.0, 3.0],
        }
    )

    safe = point_in_time_mask(frame, "observed_at")
    out = sanitize_feature_family(
        frame,
        ["feature"],
        "observed_at",
        flag_col="feature_point_in_time",
    )

    assert safe.tolist() == [True, False, False]
    assert out.loc[0, "feature"] == 1.0
    assert out.loc[1:, "feature"].isna().all()


def test_point_in_time_summary_separates_failures_from_unverified():
    audit = pd.DataFrame(
        {
            "catalyst_id": ["A", "A", "B"],
            "check": ["market", "trial", "trial"],
            "severity": ["FAIL", "UNVERIFIED", "UNVERIFIED"],
        }
    )

    summary = summarize_point_in_time_audit(audit)

    assert summary["violations"] == 1
    assert summary["unverified"] == 2
    assert summary["affected_catalysts"] == 2
