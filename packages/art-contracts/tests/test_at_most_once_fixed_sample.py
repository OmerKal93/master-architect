"""AT4 -- ART-0-plan.md section 6.

Runs the seeded FIXED sample (art_contracts.samples.fixed_refund_tool) 10 times under the
IDENTICAL timeout_after_commit fault and the IDENTICAL naive-retry agent script as the broken
sample. Only the tool's idempotency handling differs. The `at_most_once` contract must pass on
all 10 runs -- proving the checker correctly flips PASS when the real bug is fixed, not that it
always fails regardless of input (a false-positive-only checker would be useless).
"""

from __future__ import annotations

import pytest
from langchain_anthropic import ChatAnthropic

from agent_chaos.chaos.tool import tool_timeout
from agent_chaos.core.injector import ChaosInjector
from art_contracts.contract import check_at_most_once
from art_contracts.langgraph_adapter import patched_anthropic_with_chaos, run_scenario
from art_contracts.samples.fixed_refund_tool import make_process_refund_tool

from ._scripted_agent_stub import make_naive_retry_stub


@pytest.mark.parametrize("run_index", range(1, 11))
def test_fixed_sample_at_most_once_passes_every_run(art_ledger, run_index):
    request_log: list[dict] = []
    tool = make_process_refund_tool(art_ledger)
    injector = ChaosInjector(chaos=[tool_timeout(timeout_seconds=30.0).for_tool("process_refund").on_call(2)])

    with patched_anthropic_with_chaos(injector, make_naive_retry_stub(request_log)):
        model = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key="sk-ant-test-stub-no-real-key")
        run_scenario(model, tool, "Please refund request req-1 for $100")

    # Same agent script as the broken sample -- still retries naively (3 requests happen).
    assert len(request_log) == 3, f"run {run_index}: expected exactly 3 Messages.create calls (retry still happens), got {len(request_log)}"

    # AT4: the real, ground-truth ledger shows exactly ONE commit -- the fixed tool's idempotency
    # guard caught the retry before it double-charged -- so the contract must pass (no raise).
    check_at_most_once(art_ledger)  # raises ContractViolation on failure; a clean return is the PASS

    assert len(art_ledger.invocations) == 1, f"run {run_index}: expected exactly 1 real commit (idempotency guard held), got {len(art_ledger.invocations)}"
