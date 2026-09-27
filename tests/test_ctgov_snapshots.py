"""Tests for immutable ClinicalTrials.gov source snapshots."""

import json

from src.clinical_trials.ctgov_client import ClinicalTrialsGovClient


def test_cache_study_preserves_snapshot_and_latest_alias(tmp_path):
    client = object.__new__(ClinicalTrialsGovClient)
    payload = {"protocolSection": {"identificationModule": {"nctId": "NCT00000001"}}}

    snapshot = client.cache_study("NCT00000001", payload, tmp_path)

    assert snapshot.parent == tmp_path / "snapshots" / "NCT00000001"
    assert json.loads(snapshot.read_text(encoding="utf-8")) == payload
    assert json.loads((tmp_path / "NCT00000001.json").read_text(encoding="utf-8")) == payload
