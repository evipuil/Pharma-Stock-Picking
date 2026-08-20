"""Tests for pipeline completion audit."""

from src.validation.pipeline_audit import run_pipeline_audit


def test_pipeline_audit_runs():
    checks = run_pipeline_audit()
    assert len(checks) >= 10
    reqs = {c.requirement for c in checks}
    assert "Cohort N≥100 catalysts" in reqs
    assert any("Walk-forward" in c.requirement for c in checks)


def test_cohort_target_met():
    checks = run_pipeline_audit()
    cohort = next(c for c in checks if c.requirement == "Cohort N≥100 catalysts")
    assert cohort.status == "pass"
