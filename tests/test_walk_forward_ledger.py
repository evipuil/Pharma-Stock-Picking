"""Tests for walk-forward ledger persistence."""

import uuid
from unittest.mock import MagicMock, patch

import pandas as pd

from src.return_models.walk_forward import _persist_ledger


def test_persist_ledger_deletes_before_insert():
    ledger = pd.DataFrame(
        [
            {
                "ledger_id": str(uuid.uuid4()),
                "catalyst_id": "CAT-1",
                "train_end_year": 2014,
                "test_year": 2015,
                "p_success": 0.5,
                "expected_car": 0.03,
                "realized_car": 0.02,
                "clinical_success": 1,
                "trade_signal": "LONG",
                "model_version": "wf_2014",
            }
        ]
    )
    mock_conn = MagicMock()
    with patch("sqlite3.connect", return_value=mock_conn):
        with patch("src.return_models.walk_forward.project_root") as mock_root:
            mock_root.return_value.__truediv__ = lambda self, x: MagicMock(
                exists=lambda: True,
                read_text=lambda encoding: "CREATE TABLE walk_forward_ledger (ledger_id TEXT);",
            )
            _persist_ledger(ledger)

    calls = [str(c) for c in mock_conn.execute.call_args_list]
    assert any("DELETE FROM walk_forward_ledger" in c for c in calls)
