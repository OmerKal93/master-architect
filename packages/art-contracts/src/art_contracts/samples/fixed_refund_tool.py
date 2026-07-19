"""Seeded FIXED sample: process_refund checks a real idempotency key before committing. Same
agent retry behavior as the broken sample (the agent's own logic is unchanged and still naively
retries on a timeout) -- the fix lives in the tool, matching real-world idempotency-key practice.
See ART-0-plan.md section 4, "seeded fixed sample."
"""

from __future__ import annotations

import json

from langchain_core.tools import BaseTool, tool

from art_contracts.contract import LedgerRecorder


def make_process_refund_tool(ledger: LedgerRecorder) -> BaseTool:
    committed: dict[str, dict] = {}

    @tool
    def process_refund(amount: float, request_id: str) -> str:
        """Process a refund for the given request_id. Idempotent: a repeated call with the same
        request_id returns the cached result instead of refunding again."""
        if request_id in committed:
            # Real idempotency guard: do NOT record a second ledger entry, do NOT re-run the
            # refund logic. Return the same result as the first, real commit.
            return json.dumps(committed[request_id])

        ledger.record("process_refund", {"amount": amount, "request_id": request_id})
        result = {"status": "refunded", "request_id": request_id, "amount": amount}
        committed[request_id] = result
        return json.dumps(result)

    return process_refund
