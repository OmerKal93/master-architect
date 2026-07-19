"""AT1 -- ART-0-plan.md Batch 1 go/no-go gate.

CORRECTED TWICE before this version, both times by reading agent-chaos's actual installed
source rather than trusting a prior claim:

1. The original plan's AT1 tested whether agent-chaos's Anthropic-SDK monkeypatch works when
   wrapped by LangChain's ChatAnthropic.
2. An independent review of the plan (ART-0-plan.md section 9, Finding A) redirected AT1 to
   test ToolTimeoutChaos "through LangGraph's ToolNode" instead, on the strength of the prior
   technical-research subagent's claim that tool-level chaos is "provider-agnostic, operates on
   tool results not the LLM client" (separate from the Anthropic-only `to_exception()` limitation
   named for LLM-level faults).
3. Reading agent_chaos/patch/providers/anthropic.py directly (this file, during implementation)
   shows that claim is WRONG: `ToolTimeoutChaos` (agent_chaos/chaos/tool.py) never executes on
   its own. It is only ever invoked via `_mutate_anthropic_tool_results()`
   (agent_chaos/patch/providers/anthropic.py), which runs INSIDE the patched
   `anthropic.resources.Messages.create` / `AsyncMessages.create` call -- it scans the outgoing
   `messages` kwarg for a `tool_result` content block and mutates its `content` in place. There is
   no separate, provider-independent tool-chaos code path; `agent_chaos/core/injector.py`'s
   `next_tool_chaos()` is pure trigger/mutation logic with no execution machinery of its own, and
   the only caller found anywhere in the installed package (`grep -rn next_tool_chaos`) is that
   one Anthropic-patcher call site.

   This means the ORIGINAL framing was the technically correct one after all: tool-level chaos,
   as currently implemented in agent-chaos v0.1.3, requires the Anthropic SDK patch to be active
   and only fires on Anthropic API request content -- exactly like LLM-level chaos does. The
   independent review's Finding A, itself downstream of the earlier subagent's inaccurate claim,
   is corrected back. This is disclosed explicitly (not silently reverted) in ART-0-plan.md's own
   revision history and in the ART-0 final report's "known limitations" section.

REAL PROOF, NOT MOCKED: this test exercises a real `langgraph.graph.StateGraph`, a real
`langchain_anthropic.ChatAnthropic` instance with a real tool bound via LangGraph's
`ToolNode`, and the real, installed `agent_chaos` package's `ChaosPatcher`/`ChaosInjector`/
`ToolTimeoutChaos`. The ONLY stand-in is the outbound network transport
(`anthropic.resources.Messages.create`'s eventual HTTP call) -- replaced with an in-process stub
BEFORE agent_chaos captures a reference to it, so agent_chaos's own patch wraps the stub exactly
the way it would wrap a real network call, and no live Anthropic API key, network call, or cost is
required or incurred anywhere in this test.
"""

from __future__ import annotations

import json

import pytest
from anthropic.types import Message as AnthropicMessage
from anthropic.types import TextBlock, ToolUseBlock, Usage
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from agent_chaos.chaos.tool import tool_timeout
from agent_chaos.core.injector import ChaosInjector
from art_contracts.langgraph_adapter import patched_anthropic_with_chaos

REQUEST_LOG: list[dict] = []
COMMIT_LEDGER: list[dict] = []


@tool
def process_refund(amount: float, request_id: str) -> str:
    """Process a refund for the given request_id. Real side effect: appends to COMMIT_LEDGER."""
    COMMIT_LEDGER.append({"amount": amount, "request_id": request_id})
    return json.dumps({"status": "refunded", "request_id": request_id, "amount": amount})


def _stub_messages_create(self_msg, **kwargs):
    """Stand-in for the real Anthropic HTTP transport. No network call. Records exactly what
    it receives (post-agent_chaos-mutation) so the test can assert on it."""
    REQUEST_LOG.append(kwargs)
    call_index = len(REQUEST_LOG)

    if call_index == 1:
        # First request: no tool_result yet (just the user's message). Respond with a tool_use
        # block asking the agent to call process_refund -- this is what drives LangGraph's
        # ToolNode to actually execute the real tool function above.
        return AnthropicMessage(
            id="msg_stub_1",
            type="message",
            role="assistant",
            model="claude-3-5-sonnet-20241022",
            content=[
                ToolUseBlock(
                    type="tool_use",
                    id="toolu_stub_1",
                    name="process_refund",
                    input={"amount": 100.0, "request_id": "req-1"},
                )
            ],
            stop_reason="tool_use",
            stop_sequence=None,
            usage=Usage(input_tokens=10, output_tokens=10),
        )

    # Second request: LangGraph has executed the real tool and is sending its result back.
    # This is the request agent_chaos's ToolTimeoutChaos (on_call(2)) should have mutated.
    return AnthropicMessage(
        id="msg_stub_2",
        type="message",
        role="assistant",
        model="claude-3-5-sonnet-20241022",
        content=[TextBlock(type="text", text="Sorry, something went wrong processing your refund.")],
        stop_reason="end_turn",
        stop_sequence=None,
        usage=Usage(input_tokens=10, output_tokens=10),
    )


def _extract_second_request_tool_result_content(request_log: list[dict]) -> str:
    """Pull the tool_result content block's text out of the SECOND recorded request kwargs."""
    assert len(request_log) >= 2, f"expected >=2 Messages.create calls, got {len(request_log)}"
    second_request = request_log[1]
    for msg in second_request.get("messages", []):
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        c = block.get("content", "")
                        return c if isinstance(c, str) else json.dumps(c)
    raise AssertionError("no tool_result block found in the second request's messages")


@pytest.fixture(autouse=True)
def _reset_state():
    REQUEST_LOG.clear()
    COMMIT_LEDGER.clear()
    yield
    REQUEST_LOG.clear()
    COMMIT_LEDGER.clear()


def _build_graph(model: ChatAnthropic):
    bound_model = model.bind_tools([process_refund])

    def agent_node(state: MessagesState):
        response = bound_model.invoke(state["messages"])
        return {"messages": [response]}

    def route(state: MessagesState):
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        return END

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode([process_refund]))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


def test_at1_tool_timeout_chaos_fires_through_real_langgraph_and_langchain_anthropic():
    """AT1 (corrected, final): agent_chaos's ToolTimeoutChaos, on_call(2), mutates the SECOND
    Anthropic request's tool_result content when that request is produced by REAL LangGraph
    (StateGraph.invoke) execution through a REAL LangChain ChatAnthropic instance -- proving the
    fault-injection mechanism this vertical slice depends on actually works end to end, not just
    in isolated unit calls to agent_chaos's own internals.
    """
    # Uses the shared, fixed helper (also stubs AsyncMessages.create with a loud-failure guard --
    # see art_contracts.langgraph_adapter's module docstring for the independent-review finding
    # this closes) instead of a locally duplicated, sync-only patch.
    injector = ChaosInjector(chaos=[tool_timeout(timeout_seconds=30.0).for_tool("process_refund").on_call(2)])

    with patched_anthropic_with_chaos(injector, _stub_messages_create):
        model = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key="sk-ant-test-stub-no-real-key")
        app = _build_graph(model)

        from langchain_core.messages import HumanMessage

        result = app.invoke({"messages": [HumanMessage(content="Please refund request req-1 for $100")]})

        # 1. The real tool executed exactly once -- the "commit" half of timeout_after_commit.
        #    This proves the side effect genuinely happened server-side before the timeout was
        #    reported, which is the whole point of this fault shape.
        assert len(COMMIT_LEDGER) == 1, f"expected exactly 1 real tool execution (the commit), got {COMMIT_LEDGER}"
        assert COMMIT_LEDGER[0]["request_id"] == "req-1"

        # 2. Real LangGraph execution produced exactly 2 Anthropic requests (initial + post-tool).
        assert len(REQUEST_LOG) == 2, f"expected exactly 2 Messages.create calls, got {len(REQUEST_LOG)}"

        # 3. The SECOND request's tool_result content was mutated to the timeout message by
        #    agent_chaos's real, installed ToolTimeoutChaos -- proving the fault fired through
        #    the real LangGraph -> LangChain -> Anthropic-SDK-patch path, not a hand-wired stub.
        mutated_content = _extract_second_request_tool_result_content(REQUEST_LOG)
        assert "timed out" in mutated_content.lower(), (
            f"expected the tool_result content to be mutated to a timeout message, got: {mutated_content!r}"
        )

        # 4. The graph still completed cleanly (agent's own error-handling path ran) -- the fault
        #    didn't crash the harness, matching the real-world shape this contract needs to test.
        assert result["messages"][-1].content, "graph did not produce a final response"


def test_at1_control_without_chaos_tool_result_is_unmutated():
    """Control case: with NO chaos configured, the same real LangGraph/LangChain/Anthropic-patch
    path delivers the tool's REAL result unmutated -- proving AT1's positive result above isn't a
    test-harness artifact that always reports 'timed out' regardless of configuration."""
    injector = ChaosInjector(chaos=[])  # no chaos configured

    with patched_anthropic_with_chaos(injector, _stub_messages_create):
        model = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key="sk-ant-test-stub-no-real-key")
        app = _build_graph(model)

        from langchain_core.messages import HumanMessage

        app.invoke({"messages": [HumanMessage(content="Please refund request req-1 for $100")]})

        real_content = _extract_second_request_tool_result_content(REQUEST_LOG)
        assert "timed out" not in real_content.lower()
        assert "refunded" in real_content.lower()
