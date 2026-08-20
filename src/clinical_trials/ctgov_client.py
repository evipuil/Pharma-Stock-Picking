"""ClinicalTrials.gov API client (Phase 1)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from src.config import load_yaml, project_root


class ClinicalTrialsGovClient:
    def __init__(self, config_path: Path | None = None) -> None:
        cfg = load_yaml(config_path or project_root() / "configs" / "data_sources.yaml")
        self.base_url = cfg["clinical_trials"]["base_url"]
        self.rate_limit = cfg["clinical_trials"]["rate_limit_per_second"]
        self.timeout = cfg["clinical_trials"]["timeout_seconds"]
        self._last_request = 0.0

    def fetch_study(self, nct_id: str) -> dict[str, Any]:
        self._throttle()
        url = f"{self.base_url}/{nct_id}"
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def search_studies(
        self,
        query: str,
        phase: str | None = None,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Search CT.gov v2 API; returns list of study JSON dicts."""
        self._throttle()
        params: dict[str, Any] = {
            "query.term": query,
            "pageSize": page_size,
        }
        # Note: filter.phase causes 400 on some API versions; filter client-side instead.
        resp = requests.get(self.base_url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        studies = data.get("studies") or []
        if phase:
            phase_upper = phase.upper()
            filtered = []
            for s in studies:
                phases = (
                    s.get("protocolSection", {})
                    .get("designModule", {})
                    .get("phases")
                    or []
                )
                if any(phase_upper in p.upper() for p in phases):
                    filtered.append(s)
            return filtered
        return studies

    def fetch_and_cache(self, nct_id: str, raw_dir: Path) -> Path:
        raw_dir.mkdir(parents=True, exist_ok=True)
        data = self.fetch_study(nct_id)
        out = raw_dir / f"{nct_id}.json"
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return out

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request
        wait = (1.0 / self.rate_limit) - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()
