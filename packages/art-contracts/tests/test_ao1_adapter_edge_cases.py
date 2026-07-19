"""Regression tests for independent-review findings against art_contracts.ao1_adapter."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from art_contracts.ao1_adapter import MalformedClaimLogEntryError, ingest_ao1_claim_log


def test_ok_true_entry_missing_decision_id_raises_clear_error():
    """A differently-shaped success line (ok:true, no decision_id) must raise a clear, named
    error, not an opaque KeyError with no indication of which line/log or what was wrong."""
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "malformed.ndjson"
        log_path.write_text('{"ok": true, "dispatch_id": "d1"}\n', encoding="utf-8")

        with pytest.raises(MalformedClaimLogEntryError) as excinfo:
            ingest_ao1_claim_log(log_path)

        assert "decision_id" in str(excinfo.value)
        assert str(log_path) in str(excinfo.value)


def test_ok_false_entries_are_skipped_not_recorded():
    """A refused claim attempt (ok:false) must never contribute a ledger entry, even if it also
    happens to lack decision_id -- only ok:true lines are validated/recorded."""
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "refused.ndjson"
        log_path.write_text('{"ok": false, "reason": "duplicate_dispatch_for_decision"}\n', encoding="utf-8")
        ledger = ingest_ao1_claim_log(log_path)
        assert len(ledger.invocations) == 0
