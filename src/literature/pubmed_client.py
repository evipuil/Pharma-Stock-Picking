"""PubMed E-utilities client (Phase 1)."""

from __future__ import annotations

import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import requests

from src.config import load_yaml, project_root


class PubMedClient:
    def __init__(self, config_path: str | None = None) -> None:
        cfg = load_yaml(config_path or project_root() / "configs" / "data_sources.yaml")
        pubmed = cfg["pubmed"]
        self.esearch_url = pubmed["esearch_url"]
        self.efetch_url = pubmed["efetch_url"]
        self.db = pubmed["db"]
        self.rate_limit = pubmed["rate_limit_per_second"]
        self._last_request = 0.0

    def search(
        self,
        query: str,
        max_date: str | None = None,
        retmax: int = 100,
    ) -> list[str]:
        """Return PMIDs matching query, optionally filtered by max publication date (YYYY/MM/DD)."""
        term = query
        if max_date:
            # Restrict to publications on or before max_date (pre-t0)
            term = f"({query}) AND (1800/01/01[PDAT] : {max_date}[PDAT])"

        self._throttle(min_interval=0.4)
        params: dict[str, Any] = {
            "db": self.db,
            "term": term,
            "retmax": retmax,
            "retmode": "json",
        }
        resp = requests.get(self.esearch_url, params=params, timeout=30)
        if resp.status_code == 429:
            time.sleep(3)
            resp = requests.get(self.esearch_url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("esearchresult", {}).get("idlist", [])

    def fetch_metadata(self, pmids: list[str]) -> list[dict[str, Any]]:
        if not pmids:
            return []
        records: list[dict[str, Any]] = []
        # NCBI recommends <= 200 IDs per request; we batch smaller to avoid 429
        batch_size = 5
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i : i + batch_size]
            records.extend(self._fetch_metadata_batch(batch))
        return records

    def _fetch_metadata_batch(self, pmids: list[str], retries: int = 4) -> list[dict[str, Any]]:
        for attempt in range(retries):
            self._throttle(min_interval=0.5)
            params = {
                "db": self.db,
                "id": ",".join(pmids),
                "retmode": "xml",
            }
            resp = requests.get(self.efetch_url, params=params, timeout=60)
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            return self._parse_efetch_xml(resp.text)
        return []

    def search_animal_literature(
        self,
        drug_name: str,
        max_date: str,
        animal_keywords: list[str] | None = None,
        retmax: int = 30,
        alt_names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search pre-t0 animal studies for a drug."""
        keywords = animal_keywords or ["mice", "mouse", "xenograft", "murine", "rat"]
        animal_clause = " OR ".join(f'"{k}"[Title/Abstract]' for k in keywords)
        names = [drug_name] + (alt_names or [])
        name_clause = " OR ".join(f'"{n}"[Title/Abstract]' for n in names)
        query = f"({name_clause}) AND ({animal_clause})"
        pmids = self.search(query, max_date=max_date, retmax=retmax)
        return self.fetch_metadata(pmids)

    def cache_search(
        self,
        results: list[dict[str, Any]],
        out_dir: Path,
        program_id: str,
    ) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{program_id}_pubmed.json"
        path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
        return path

    def _parse_efetch_xml(self, xml_text: str) -> list[dict[str, Any]]:
        root = ET.fromstring(xml_text)
        records = []
        for article in root.findall(".//PubmedArticle"):
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else None
            title_el = article.find(".//ArticleTitle")
            title = "".join(title_el.itertext()) if title_el is not None else None
            abstract_parts = article.findall(".//AbstractText")
            abstract = " ".join("".join(a.itertext()) for a in abstract_parts)
            pub_date = self._extract_pub_date(article)
            doi = None
            for id_el in article.findall(".//ArticleId"):
                if id_el.get("IdType") == "doi":
                    doi = id_el.text
            records.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "publication_date": pub_date,
                    "doi": doi,
                }
            )
        return records

    def _extract_pub_date(self, article: ET.Element) -> str | None:
        pub_date = article.find(".//PubDate")
        if pub_date is None:
            return None
        year = pub_date.findtext("Year")
        month = pub_date.findtext("Month") or "1"
        day = pub_date.findtext("Day") or "1"
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
        }
        if month in month_map:
            month = month_map[month]
        try:
            int(month)
        except ValueError:
            month = "1"
        if year:
            return f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
        return None

    def _throttle(self, min_interval: float | None = None) -> None:
        interval = min_interval or (1.0 / self.rate_limit)
        elapsed = time.time() - self._last_request
        wait = interval - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()
