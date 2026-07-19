"""ART-0 LangGraph adapter -- the minimal, real integration proven by AT1
(tests/test_at1_go_no_go_spike.py) generalized into a reusable helper.

Wires: a real langgraph.graph.StateGraph tool-calling loop, a real langchain_anthropic.ChatAnthropic
instance, and the real, installed, UNMODIFIED agent_chaos package (pinned agent-chaos==0.1.3, no
fork -- see docs/ART-0-plan.md section 3). The only stand-in is the outbound Anthropic transport,
replaced by a caller-supplied deterministic stub function so contract tests are reproducible and
require no live API key, network call, or cost.

Independent-review fix: the original version of this module only stubbed the SYNC
`anthropic.resources.Messages.create`. agent_chaos's own patcher separately wraps FOUR methods
(sync/async x regular/beta). A reviewer mechanically proved that calling `.ainvoke()` on the same
model instance reaches the real, unstubbed `AsyncMessages.create` -> real `httpx.AsyncClient.send`
-- a genuine outbound-HTTPS-attempt path, latent because every test in this spike only uses sync
`.invoke()`. Fixed by ALSO patching the async method with a loud, explicit guard that raises
immediately rather than silently reaching the network -- this spike's scope never needed a working
async stub, so failing closed (clear error) is the correct fix, not building one.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable


class AsyncPathNotStubbedError(RuntimeError):
    """Raised by the async-guard stub -- see module docstring. Fails loudly and immediately,
    before any real network call could occur, rather than silently reaching the real Anthropic
    async transport."""


def _async_guard_stub(self_msg, **kwargs):
    raise AsyncPathNotStubbedError(
        "ART-0's patched_anthropic_with_chaos only stubs the SYNC Anthropic transport. "
        "AsyncMessages.create was about to be called for real (e.g. via .ainvoke() or an async "
        "graph) -- refusing rather than silently reaching a real network call. Add a real async "
        "stub before using this helper with async LangGraph execution."
    )


from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from agent_chaos.core.injector import ChaosInjector
from agent_chaos.core.recorder import Recorder
from agent_chaos.patch.patcher import ChaosPatcher


@contextmanager
def patched_anthropic_with_chaos(injector: ChaosInjector, stub_create: Callable):
    """Install `stub_create` as the SYNC Anthropic transport, install a loud-failure guard as the
    ASYNC transport (see module docstring), apply agent_chaos's real patch on top of both (so
    agent_chaos wraps the stubs exactly as it would wrap a real network call), and restore the
    originals on exit -- even on error.
    """
    import anthropic.resources as anthropic_resources

    original_create = anthropic_resources.Messages.create
    original_async_create = anthropic_resources.AsyncMessages.create
    anthropic_resources.Messages.create = stub_create
    anthropic_resources.AsyncMessages.create = _async_guard_stub
    recorder = Recorder()
    patcher = ChaosPatcher(injector, recorder)
    try:
        patcher.patch_providers(["anthropic"])
        yield recorder
    finally:
        patcher.unpatch_all()
        anthropic_resources.Messages.create = original_create
        anthropic_resources.AsyncMessages.create = original_async_create


def build_tool_calling_graph(model, tool: BaseTool):
    """One agent node (calls the bound model) + one tools node (real LangGraph ToolNode executing
    `tool` for real) + the standard tool-call routing loop. Mirrors AT1's proven graph shape.
    """
    bound_model = model.bind_tools([tool])

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
    graph.add_node("tools", ToolNode([tool]))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


def run_scenario(model, tool: BaseTool, user_message: str):
    """Real invocation entry point: builds the graph and runs it once against `user_message`."""
    app = build_tool_calling_graph(model, tool)
    return app.invoke({"messages": [HumanMessage(content=user_message)]})
