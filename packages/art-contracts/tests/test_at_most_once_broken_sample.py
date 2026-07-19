"""AT2 + AT3 -- ART-0-plan.md section 6.

Runs the seeded BROKEN sample (art_contracts.samples.broken_refund_tool) 10 times under the
timeout_after_commit fault. The `at_most_once` contract must fail on all 10 runs -- the real bug
(no idempotency check) genuinely double-charges every time the naive retry fires, and the fault
fires deterministically on call #2 every run (AT2: no probabilistic/random-seed dependency).
"""

from __future__ import annotations

import pytest
from langchain_anthropic import ChatAnthropic

from agent_chaos.chaos.tool import tool_timeout
from agent_chaos.core.injector import ChaosInjector
from art_contracts.contract import ContractViolation, check_at_most_once
from art_contracts.langgraph_adapter import patched_anthropic_with_chaos, run_scenario
from art_contracts.samples.broken_refund_tool import make_process_refund_tool

from ._scripted_agent_stub import make_naive_retry_stub


@pytest.mark.parametrize("run_index", range(1, 11))
def test_broken_sample_at_most_once_fails_every_run(art_ledger, run_index):
    request_log: list[dict] = []
    tool = make_process_refund_tool(art_ledger)
    injector = ChaosInjector(chaos=[tool_timeout(timeout_seconds=30.0).for_tool("process_refund").on_call(2)])

    with patched_anthropic_with_chaos(injector, make_naive_retry_stub(request_log)):
        model = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key="sk-ant-test-stub-no-real-key")
        run_scenario(model, tool, "Please refund request req-1 for $100")

    # AT2: the fault fired on exactly the 2nd request, every run, deterministically (call-index
    # trigger, not a clock -- see ART-0-plan.md section 9, Finding E disposition).
    assert len(request_log) == 3, f"run {run_index}: expected exactly 3 Messages.create calls (retry happened), got {len(request_log)}"

    # AT3: the real, ground-truth side-effect ledger shows 2 executions for the same request_id
    # -- a genuine double charge -- so the contract must fail on every run.
    with pytest.raises(ContractViolation) as excinfo:
        check_at_most_once(art_ledger)

    assert excinfo.value.contract_name == "at_most_once"
    assert excinfo.value.tool_name == "process_refund"
    assert "req-1" in str(excinfo.value)
    assert len(art_ledger.invocations) == 2, f"run {run_index}: expected the real double-charge (2 ledger entries), got {len(art_ledger.invocations)}"
