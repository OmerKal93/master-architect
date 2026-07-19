"""Seeded BROKEN sample: process_refund has no idempotency-key check. If the agent retries after
seeing a (possibly fault-injected) timeout, the real refund logic runs again, unconditionally --
a genuine double-charge bug. This is the deliberate defect the `at_most_once` contract must
detect (ART-0-plan.md section 4, "seeded broken sample").
"""

from __future__ import annotations

import json

from langchain_core.tools import BaseTool, tool

from art_contracts.contract import LedgerRecorder


def make_process_refund_tool(ledger: LedgerRecorder) -> BaseTool:
    @tool
    def process_refund(amount: float, request_id: str) -> str:
        """Process a refund for the given request_id. BUG: no idempotency check -- calling this
        twice with the same request_id genuinely refunds twice."""
        # No check for an existing request_id -- this is the real bug.
        ledger.record("process_refund", {"amount": amount, "request_id": request_id})
        return json.dumps({"status": "refunded", "request_id": request_id, "amount": amount})

    return process_refund
