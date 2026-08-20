"""Export manual extraction summary to CSV."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from src.config import project_root
from src.preclinical.aggregate import export_extraction_summary


def main() -> None:
    db = project_root() / "data" / "processed" / "research.db"
    out = project_root() / "data" / "processed" / "manual_extraction_summary.csv"
    conn = sqlite3.connect(db)
    rows = export_extraction_summary(conn)
    conn.close()
    if not rows:
        print("No rows")
        return
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
