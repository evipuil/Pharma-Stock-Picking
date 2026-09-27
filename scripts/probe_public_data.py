"""Probe public data APIs and print availability summary."""

from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
HEADERS = {"User-Agent": "StockPickingResearch research@example.com"}


def probe(name: str, fn) -> dict:
    try:
        return {"source": name, "status": "ok", **fn()}
    except Exception as e:
        return {"source": name, "status": "error", "error": str(e)}


def main() -> None:
    results = []

    def ctgov():
        r = requests.get(
            "https://clinicaltrials.gov/api/v2/studies",
            params={
                "query.cond": "cancer",
                "filter.overallStatus": "COMPLETED",
                "filter.phase": "PHASE2,PHASE3",
                "filter.studyType": "INTERVENTIONAL",
                "pageSize": 1,
                "countTotal": "true",
            },
            timeout=30,
        )
        r.raise_for_status()
        return {"total_oncology_ph2_ph3_completed": r.json().get("totalCount")}

    def ctgov_results():
        r = requests.get(
            "https://clinicaltrials.gov/api/v2/studies",
            params={
                "query.cond": "neoplasms",
                "filter.overallStatus": "COMPLETED",
                "filter.phase": "PHASE2,PHASE3",
                "filter.resultsFirstPostDate": "2015-01-01:2020-12-31",
                "pageSize": 1,
                "countTotal": "true",
            },
            timeout=30,
        )
        r.raise_for_status()
        return {"total_with_results_2015_2020": r.json().get("totalCount")}

    def sec_tickers():
        r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=HEADERS, timeout=20)
        r.raise_for_status()
        return {"n_tickers": len(r.json())}

    def sec_efts():
        r = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={
                "q": "top-line results",
                "forms": "8-K",
                "startdt": "2018-01-01",
                "enddt": "2019-12-31",
            },
            headers=HEADERS,
            timeout=20,
        )
        r.raise_for_status()
        total = r.json().get("hits", {}).get("total", {})
        return {"hits_8k_topline_2018_2019": total}

    def openfda_drugs():
        r = requests.get(
            "https://api.fda.gov/drug/drugsfda.json",
            params={"search": 'sponsor_name:"Mirati"', "limit": 1},
            timeout=15,
        )
        return {"status_code": r.status_code, "found": r.status_code == 200}

    def openfda_events():
        r = requests.get(
            "https://api.fda.gov/drug/event.json",
            params={"count": "patient.reaction.reactionmeddrapt.exact", "limit": 1},
            timeout=15,
        )
        r.raise_for_status()
        return {"faers_reaction_buckets": len(r.json().get("results", []))}

    def nih_reporter():
        r = requests.post(
            "https://api.reporter.nih.gov/v2/projects/search",
            json={"criteria": {"fiscal_years": [2020]}, "limit": 1},
            timeout=15,
        )
        r.raise_for_status()
        return {"sample_projects": len(r.json().get("results", []))}

    def finra_short():
        r = requests.post(
            "https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest",
            json={
                "compareFilters": [{"fieldName": "symbol", "compareType": "EQUAL", "fieldValue": "MRNA"}],
                "limit": 1,
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=15,
        )
        return {"status_code": r.status_code, "body_preview": r.text[:120]}

    def ken_french():
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip"
        r = requests.head(url, timeout=15)
        return {"status_code": r.status_code}

    for name, fn in [
        ("clinicaltrials_gov", ctgov),
        ("clinicaltrials_gov_results", ctgov_results),
        ("sec_company_tickers", sec_tickers),
        ("sec_efts_8k", sec_efts),
        ("openfda_drugsfda", openfda_drugs),
        ("openfda_faers", openfda_events),
        ("nih_reporter", nih_reporter),
        ("finra_short_interest", finra_short),
        ("ken_french_factors", ken_french),
    ]:
        results.append(probe(name, fn))
        print(json.dumps(results[-1]))

    out = ROOT / "data" / "processed" / "public_data_probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
