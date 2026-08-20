"""Fix missing publication dates on verified animal studies (leakage repair)."""

from __future__ import annotations

import sqlite3
from datetime import date

from src.config import project_root
from src.literature.pubmed_client import PubMedClient
from src.preclinical.aggregate import compute_program_aggregates
from src.validation.leakage import run_leakage_audit

DB = project_root() / "data" / "processed" / "research.db"

# Known dates for inherited failure-program studies (same PMIDs as Wave 1 manual curation)
KNOWN_DATES = {
    "20799147": "2010-09-15",  # tivozanib xenograft
    "20978505": "2010-11-09",  # rucaparib xenograft
}


def fix_missing_dates() -> dict:
    conn = sqlite3.connect(DB)
    pubmed = PubMedClient()
    stats = {"updated": 0, "rejected_post_t0": 0}

    rows = conn.execute(
        """
        SELECT s.study_id, s.program_id, p.pmid, t0.t0_date
        FROM animal_studies s
        JOIN publications p ON s.publication_id = p.publication_id
        JOIN source_records sr ON p.source_record_id = sr.source_record_id
        JOIN program_t0 t0 ON s.program_id = t0.program_id
        WHERE s.verification_status = 'verified'
          AND (sr.publication_date IS NULL OR sr.publication_date = '')
        """
    ).fetchall()

    for study_id, program_id, pmid, t0_str in rows:
        pub_date = KNOWN_DATES.get(pmid)
        if not pub_date:
            hits = pubmed.fetch_metadata([pmid])
            if hits:
                pub_date = hits[0].get("publication_date")

        if not pub_date:
            conn.execute(
                "UPDATE animal_studies SET verification_status='pending' WHERE study_id=?",
                (study_id,),
            )
            stats["rejected_post_t0"] += 1
            continue

        t0 = date.fromisoformat(t0_str[:10])
        eff = date.fromisoformat(pub_date[:10])
        if eff > t0:
            conn.execute(
                "UPDATE animal_studies SET verification_status='rejected' WHERE study_id=?",
                (study_id,),
            )
            stats["rejected_post_t0"] += 1
            continue

        conn.execute(
            """
            UPDATE source_records SET publication_date = ?
            WHERE source_record_id = (
                SELECT p.source_record_id FROM publications p
                JOIN animal_studies s ON s.publication_id = p.publication_id
                WHERE s.study_id = ?
            )
            """,
            (pub_date, study_id),
        )
        stats["updated"] += 1
        compute_program_aggregates(conn, program_id)

    conn.commit()
    conn.close()
    audit = run_leakage_audit(DB)
    stats["leakage_passed"] = sum(1 for r in audit if r.passed)
    stats["leakage_total"] = len(audit)
    stats["leakage_failed"] = [
        (r.program_id, r.check_type, r.violation_detail)
        for r in audit
        if not r.passed
    ]
    return stats


if __name__ == "__main__":
    print(fix_missing_dates())
