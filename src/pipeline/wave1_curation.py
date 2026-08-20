"""
Wave 1 MVP curation pipeline:
1. Resolve NCT IDs (search or manual override)
2. Fetch CT.gov metadata
3. Apply manual outcome adjudication
4. PubMed pre-t0 animal literature search
5. Load into SQLite
6. Run leakage audit
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import yaml

from src.clinical_trials.ctgov_client import ClinicalTrialsGovClient
from src.clinical_trials.parse_study import infer_outcome_labels, infer_t0, parse_study
from src.config import load_yaml, project_root
from src.db.load_program import insert_program_bundle
from src.literature.pubmed_client import PubMedClient
from src.validation.leakage import run_leakage_audit

ROOT = project_root()
RAW_CTGOV = ROOT / "data" / "raw" / "ctgov"
RAW_PUBMED = ROOT / "data" / "raw" / "pubmed"
DB_PATH = ROOT / "data" / "processed" / "research.db"

DRUG_ALT_NAMES: dict[str, list[str]] = {
    "epacadostat": ["INCB024360", "INCB 024360"],
    "sacituzumab govitecan": ["IMMU-132", "SN-38", "sacituzumab"],
    "tivozanib": ["AV-951", "AV951"],
    "neratinib": ["HKI-272", "HKI 272"],
    "rucaparib": ["CO-338", "AG-014699", "PF-01367338"],
    "palbociclib": ["PD-0332991", "PD0332991"],
    "osimertinib": ["AZD9291", "mereletinib"],
    "abemaciclib": ["LY2835219"],
    "mirvetuximab soravtansine": ["mirvetuximab", "IMGN853", "IMGN-853"],
    "belantamab mafodotin": ["belantamab", "GSK2857916"],
    "umbralisib": ["TGR-1202", "RP5264"],
    "larotrectinib": ["LOXO-101", "LOXO101"],
    "entrectinib": ["RXDX-101", "RXDX101"],
    "copanlisib": ["BAY 80-6946", "BAY80-6946"],
    "duvelisib": ["IPI-145", "IPI145"],
    "enasidenib": ["AG-221", "AG221"],
    "midostaurin": ["PKC412", "CGP 41251"],
    "olaparib": ["AZD2281", "KU-0059436"],
    "talazoparib": ["BMN 673", "BMN673"],
    "encorafenib": ["LGX818", "LGX-818"],
    "idelalisib": ["GS-1101", "CAL-101"],
    "gedatolisib": ["PF-05212384"],
    "tipifarnib": ["R115777", "Zarnestra"],
    "sotorasib": ["AMG 510", "AMG510"],
    "adagrasib": ["MRTX849", "MRTX-849"],
}


def _pick_phase2_study(studies: list[dict], drug: str, indication_hint: str) -> dict | None:
    """Select best matching Phase II study from search results."""
    from src.clinical_trials.parse_study import parse_study as ps

    candidates = []
    for raw in studies:
        parsed = ps(raw)
        phase = parsed.get("phase", "")
        if "2" not in phase.upper():
            continue
        start = parsed.get("start_date")
        if start and (start.year < 2010 or start.year > 2020):
            continue
        title = (parsed.get("brief_title") or "").lower()
        conditions = " ".join(parsed.get("conditions") or []).lower()
        score = 0
        if drug.lower() in title.lower() or any(drug.lower() in i.lower() for i in parsed.get("interventions") or []):
            score += 2
        if indication_hint.lower().replace("_", " ")[:4] in conditions or indication_hint.lower()[:4] in title:
            score += 1
        candidates.append((score, start or date(2000, 1, 1), parsed, raw))

    if not candidates:
        return None
    candidates.sort(key=lambda x: (-x[0], x[1]))
    return candidates[0][3]


def curate_wave1() -> list[dict]:
    cohort_cfg = load_yaml(ROOT / "configs" / "cohort_mvp.yaml")
    adjudication = load_yaml(ROOT / "configs" / "manual_adjudication.yaml")
    animal_kw = cohort_cfg["search_protocol"]["animal_keywords"]

    ctgov = ClinicalTrialsGovClient()
    pubmed = PubMedClient()
    bundles: list[dict] = []

    for cand in cohort_cfg["candidates"]:
        if cand.get("mvp_wave") != "wave_1":
            continue

        cid = cand["candidate_id"]
        drug = cand["drug_name"]
        adj = adjudication.get(cid, {})

        nct_id = adj.get("primary_nct_id") or cand.get("primary_nct_id")
        raw: dict

        if nct_id:
            raw_path = ctgov.fetch_and_cache(nct_id, RAW_CTGOV)
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
        else:
            studies = ctgov.search_studies(drug, phase="PHASE2")
            picked = _pick_phase2_study(studies, drug, cand["indication"])
            if not picked:
                print(f"WARN: No Phase II study found for {cid} ({drug})", file=sys.stderr)
                continue
            nct_id = picked["protocolSection"]["identificationModule"]["nctId"]
            raw_path = RAW_CTGOV / f"{nct_id}.json"
            raw_path.write_text(json.dumps(picked, indent=2), encoding="utf-8")
            raw = picked

        parsed = parse_study(raw)
        t0_date, t0_def = infer_t0(parsed)

        # Apply manual adjudication
        outcome = infer_outcome_labels(parsed)
        if "outcome" in adj:
            outcome.update({k: v for k, v in adj["outcome"].items() if k != "notes"})
            outcome["notes"] = adj["outcome"].get("notes")

        max_pub_date = t0_date.strftime("%Y/%m/%d") if t0_date else "2020/12/31"
        alt = DRUG_ALT_NAMES.get(drug, [])
        publications = pubmed.search_animal_literature(
            drug, max_date=max_pub_date, animal_keywords=animal_kw, alt_names=alt, retmax=20
        )
        pubmed.cache_search(publications, RAW_PUBMED, cid)

        # Filter publications strictly before t0
        if t0_date:
            pre_t0_pubs = []
            for p in publications:
                pd_str = p.get("publication_date")
                if pd_str:
                    try:
                        pd = date.fromisoformat(pd_str[:10])
                        if pd <= t0_date:
                            pre_t0_pubs.append(p)
                    except ValueError:
                        pass
            publications = pre_t0_pubs

        bundle = {
            "candidate_id": cid,
            "program_id": cid,
            "ticker": cand["ticker"],
            "company_name": cand["company_name"],
            "drug_name": drug,
            "indication": cand["indication"],
            "modality": cand.get("modality"),
            "primary_nct_id": nct_id,
            "mvp_wave": cand.get("mvp_wave"),
            "notes": adj.get("notes") or cand.get("notes"),
            "brief_title": parsed.get("brief_title"),
            "t0_date": t0_date,
            "t0_definition": t0_def,
            "t0_rationale": f"CT.gov start date for {nct_id}",
            "trial": parsed,
            "outcome": outcome,
            "publications": publications[:10],  # cap for MVP
            "raw_json_path": str(raw_path.relative_to(ROOT)),
            "financial_event": adj.get("financial_event"),
        }
        bundles.append(bundle)
        print(f"OK {cid}: {drug} | {nct_id} | t0={t0_date} | pubs={len(publications)} | success={outcome.get('clinical_success')}")

    return bundles


def load_and_audit(bundles: list[dict]) -> None:
    import sqlite3

    from src.db.init_db import init_database

    # Fresh database each curation run for reproducibility
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_database(DB_PATH, ROOT / "sql" / "schema.sql")
    conn = sqlite3.connect(DB_PATH)
    try:
        program_ids = []
        for b in bundles:
            pid = insert_program_bundle(conn, b)
            program_ids.append(pid)
        conn.commit()
    finally:
        conn.close()

    results = run_leakage_audit(DB_PATH, program_ids)
    passed = sum(1 for r in results if r.passed)
    failed = [r for r in results if not r.passed]
    print(f"\nLeakage audit: {passed}/{len(results)} checks passed")
    for f in failed:
        print(f"  FAIL {f.program_id} {f.check_type}: {f.violation_detail}")


def main() -> None:
    bundles = curate_wave1()
    summary_path = ROOT / "data" / "interim" / "wave1_bundles.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(bundles, indent=2, default=str),
        encoding="utf-8",
    )
    load_and_audit(bundles)
    print(f"\nSaved {len(bundles)} programs to {DB_PATH}")


if __name__ == "__main__":
    main()
