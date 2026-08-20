"""Freeze baseline artifacts before short-edge research iteration."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from src.config import load_yaml, project_root


def _copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return True


def freeze_baseline(baseline_id: str = "baseline_2026_08_19") -> Path:
    root = project_root()
    out = root / "experiments" / baseline_id
    out.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "predictions": [
            root / "data" / "out_of_sample_predictions.csv",
            root / "data" / "processed" / "expected_car_predictions.csv",
        ],
        "ledger": [
            root / "data" / "trade_ledger.csv",
        ],
        "models": [
            root / "data" / "processed" / "models" / "expected_car_v1.pkl",
        ],
        "configs": [
            root / "configs" / "stock_picking.yaml",
            root / "configs" / "exposure.yaml",
            root / "configs" / "feature_sets.yaml",
            root / "configs" / "catalyst_announcement_overrides.yaml",
            root / "configs" / "ticker_history_map.yaml",
        ],
        "reports": [
            root / "reports" / "model_performance.md",
            root / "reports" / "backtest.md",
            root / "reports" / "backtest_grid.md",
            root / "reports" / "event_study.md",
            root / "reports" / "catalyst_coverage.md",
            root / "reports" / "ablation_study.md",
            root / "reports" / "holdout_evaluation.md",
        ],
        "db_snapshot": [
            root / "data" / "processed" / "research.db",
        ],
    }

    manifest: dict = {
        "baseline_id": baseline_id,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "copied": [],
        "missing": [],
    }

    for category, paths in artifacts.items():
        for src in paths:
            rel = src.relative_to(root)
            dst = out / rel
            if _copy_if_exists(src, dst):
                manifest["copied"].append(str(rel))
            else:
                manifest["missing"].append(str(rel))

    # Walk-forward ledger from DB
    import sqlite3

    db = root / "data" / "processed" / "research.db"
    if db.exists():
        conn = sqlite3.connect(db)
        try:
            import pandas as pd

            wf = pd.read_sql("SELECT * FROM walk_forward_ledger", conn)
            wf_path = out / "data" / "walk_forward_ledger.csv"
            wf_path.parent.mkdir(parents=True, exist_ok=True)
            wf.to_csv(wf_path, index=False)
            manifest["copied"].append("data/walk_forward_ledger.csv")
        finally:
            conn.close()

    cfg = load_yaml(root / "configs" / "stock_picking.yaml")
    manifest["walk_forward_config"] = cfg.get("walk_forward", {})
    manifest["ranking_config"] = cfg.get("ranking", {})

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out
