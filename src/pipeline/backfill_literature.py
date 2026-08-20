"""Backfill PubMed animal literature for programs with zero verified studies."""

from __future__ import annotations

import sqlite3
import yaml

from src.config import project_root
from src.literature.pubmed_client import PubMedClient
from src.pipeline.batch_expand_cohort import _auto_extract_studies
from src.pipeline.wave1_curation import DRUG_ALT_NAMES

DB = project_root() / "data" / "processed" / "research.db"
BATCH_CONFIG = project_root() / "configs" / "batch_candidates.yaml"


def backfill(min_pubs: int = 1) -> dict:
    conn = sqlite3.connect(DB)
    pubmed = PubMedClient()
    templates = yaml.safe_load(BATCH_CONFIG.read_text(encoding="utf-8")).get(
        "drug_extraction_templates", {}
    )
    stats = {"programs": 0, "new_studies": 0}

    rows = conn.execute(
        """
        SELECT p.program_id, p.drug_name, t0.t0_date,
               COALESCE(pf.n_animal_studies, 0) AS n
        FROM programs p
        JOIN program_t0 t0 ON p.program_id = t0.program_id
        LEFT JOIN program_preclinical_features pf ON p.program_id = pf.program_id
        WHERE COALESCE(pf.n_animal_studies, 0) < ?
        ORDER BY p.program_id
        """,
        (min_pubs,),
    ).fetchall()

    for program_id, drug_name, t0_str, _ in rows:
        from datetime import date

        t0 = date.fromisoformat(t0_str[:10])
        max_pub = t0.strftime("%Y/%m/%d")
        alt = list(
            dict.fromkeys(
                DRUG_ALT_NAMES.get(drug_name, [])
                + templates.get(drug_name, {}).get("search_terms", [])
            )
        )
        pubs = pubmed.search_animal_literature(
            drug_name, max_date=max_pub, alt_names=alt, retmax=25
        )
        pubs = [
            p
            for p in pubs
            if p.get("publication_date")
            and date.fromisoformat(p["publication_date"][:10]) <= t0
        ]
        n = _auto_extract_studies(conn, program_id, drug_name, t0, pubs)
        conn.commit()
        if n:
            stats["programs"] += 1
            stats["new_studies"] += n
            print(f"Backfill {program_id} {drug_name}: +{n} studies from {len(pubs)} pubs")

    conn.close()
    return stats


if __name__ == "__main__":
    print(backfill())
