"""Tool-call site recognition: turning call expressions into ``ToolCall`` IR entities.

**Honest capability statement.** This frontend does not yet know which calls are "really" tool
calls versus ordinary local function calls — that classification (matching against a known-SDK
table, or reading explicit annotations) is a rule-level concern that arrives in a later PR (see
``PLAN.md`` section 4.2's AR003 detection sketch: "known-library call-shape table"). To keep the
IR proportional to plausible call sites rather than every function call in a file, this frontend
applies one narrowing heuristic: **only attribute-chain calls are recorded** (``obj.method(...)``
or ``obj.attr.method(...)`` shapes), not bare-name calls (``len(...)``, ``my_helper(...)``).
Nearly all HTTP/SDK/tool calls in Python are method calls on a client object; nearly all bare-
name calls are local helpers or builtins. This is a stated trade-off: it misses call sites where
a callable was imported directly by name (e.g. ``from openai import chat; chat(...)``) or
aliased to a bare name before use — a known, documented limitation, not a claim of completeness.

Timeout evidence is extracted by looking for a keyword argument named exactly ``timeout`` at the
call site — the near-universal kwarg name across ``requests``, ``httpx``, ``urllib3``, and the
major LLM provider SDKs.
"""

from __future__ import annotations

import ast

from agent_reliability.core.model.ir import TimeoutPolicy, ToolCall
from agent_reliability.lint.frontend.ast_utils import dotted_name, span_of, structural_hash


def _extract_timeout(call: ast.Call, *, relative_path: str) -> TimeoutPolicy:
    for kw in call.keywords:
        if kw.arg != "timeout":
            continue
        seconds: float | None = None
        if (
            isinstance(kw.value, ast.Constant)
            and isinstance(kw.value.value, (int, float))
            and not isinstance(kw.value.value, bool)
        ):
            seconds = float(kw.value.value)
        return TimeoutPolicy(
            span=span_of(call, relative_path=relative_path), present=True, seconds=seconds
        )
    return TimeoutPolicy(span=span_of(call, relative_path=relative_path), present=False)


def detect_tool_calls(tree: ast.Module, *, relative_path: str) -> tuple[ToolCall, ...]:
    """Find candidate tool-call sites in a parsed module. See module docstring for the heuristic."""
    calls: list[ToolCall] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        callee = dotted_name(node.func)
        if callee is None:
            continue
        calls.append(
            ToolCall(
                span=span_of(node, relative_path=relative_path),
                callee=callee,
                structural_hash=structural_hash(node),
                timeout=_extract_timeout(node, relative_path=relative_path),
            )
        )

    return tuple(calls)
