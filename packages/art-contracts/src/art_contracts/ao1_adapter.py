"""ART-0 Batch 5: AO-1 trace-ingestion adapter (ART-0-plan.md section 5, Target 1).

AO-1's dispatch-claim trace shape (an ndjson log of {decision_id, dispatch_id, ok, reason} claim
attempts, produced by tests/ao1_fixtures/run_real_claim.js or run_mutant_claim.js) is structurally
different from the LangGraph tool-call trace shape Target 2 uses -- this adapter is the explicitly
budgeted piece that converts AO-1's shape into the same `art_contracts.contract.LedgerRecorder`
ground-truth ledger `check_at_most_once` already knows how to check, so the SAME contract checker
covers both targets without duplicating checking logic.
"""

from __future__ import annotations

import json
from pathlib import Path

from art_contracts.contract import LedgerRecorder


class MalformedClaimLogEntryError(ValueError):
    """Raised when a successful (ok:true) claim-log line lacks a decision_id -- independent-review
    fix: this used to be a raw, uncaught KeyError, which is technically fail-closed (the adapter
    doesn't silently drop the entry) but gives no clear indication of what actually went wrong."""


def ingest_ao1_claim_log(log_path: str | Path) -> LedgerRecorder:
    """Reads an ndjson claim-attempt log and records one ledger entry per SUCCESSFUL claim
    (ok:true) -- a real AO-1 dedup guard should produce exactly one successful claim per
    decision_id; a broken one may produce more than one, which is exactly what `at_most_once`
    is checking for here.
    """
    ledger = LedgerRecorder()
    text = Path(log_path).read_text(encoding="utf-8")
    for line_num, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        if entry.get("ok") is True:
            if "decision_id" not in entry:
                raise MalformedClaimLogEntryError(
                    f"{log_path}:{line_num}: ok:true entry has no 'decision_id' field: {entry!r}"
                )
            ledger.record("claim_decision_dispatch", {"decision_id": entry["decision_id"]})
    return ledger
