"""Tests for trial design feature extraction."""

from src.trial_design.endpoint_classifier import classify_endpoint
from src.trial_design.features import _is_combination, _phase_numeric


def test_classify_os_endpoint():
    flags = classify_endpoint(["Overall Survival (OS)"])
    assert flags["endpoint_os"] == 1
    assert flags["endpoint_pfs"] == 0


def test_classify_pfs_and_orr():
    flags = classify_endpoint(["Progression-free survival", "Objective response rate"])
    assert flags["endpoint_pfs"] == 1
    assert flags["endpoint_orr"] == 1


def test_phase_numeric_mapping():
    assert _phase_numeric("PHASE2") == 2.0
    assert _phase_numeric("PHASE1/PHASE2") == 1.5


def test_combination_detection():
    assert _is_combination('["Drug A", "Drug B"]') == 1
    assert _is_combination('["Pembrolizumab"]') == 0
