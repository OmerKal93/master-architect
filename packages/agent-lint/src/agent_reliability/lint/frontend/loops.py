"""Agent-loop recognition: turning loop/recursion constructs into ``Agent`` IR entities.

**Honest capability statement.** Recognizing "this loop drives an agent" from syntax alone is
inherently a heuristic — the frontend cannot know an application's intent. Two conservative,
documented patterns are recognized:

1. **Unconditional loops** (``while True:`` / ``while 1:``) whose body contains at least one
   function/method call. A spinning loop that calls nothing is not a plausible agent loop and is
   excluded to reduce noise; beyond that, this pattern is intentionally broad — "some kind of
   unconditional loop doing repeated work with no visible bound" is exactly the shape PLAN.md's
   AR001 describes, and narrowing further (e.g. requiring specific LLM/tool-sounding call names)
   would risk *missing* real agent loops that don't happen to match a keyword list. False
   positives on non-agent ``while True:`` loops are expected and are a rule-confidence question
   (AR001, added in E04), not a frontend-recognition question.
2. **Direct self-recursion**: a function whose body contains a call to its own name. Only
   *direct* recursion is detected (a function literally calling itself by name) — mutual
   recursion (``f`` calls ``g`` calls ``f``) and indirect calls through a variable are not
   detected. This is a stated limitation, not a bug: under-detection here just means no
   ``Agent`` entity is produced (silence), which is the correct, honest behavior when static
   analysis can't tell — never a guess.

**Step-bound evidence.** A loop/function is considered to have a visible step bound
(``has_step_bound=True``) when its body contains an ``if`` statement whose test compares a name
against a value with a relational operator (``>=``, ``>``, ``==``) and whose body contains a
``break`` or ``return`` — the canonical ``if step_count >= MAX_STEPS: break`` / ``if depth >
MAX_DEPTH: return`` shape. This is also a heuristic: it will miss a bound expressed a
sufficiently unusual way, and that is the honest, documented trade-off (a missed bound produces
a true-positive-shaped ``Agent(has_step_bound=False)``, which is the safer failure direction for
a reliability tool than inventing a bound that isn't really there).
"""

from __future__ import annotations

import ast

from agent_reliability.core.model.ir import Agent
from agent_reliability.lint.frontend.ast_utils import dotted_name, span_of, structural_hash

_BOUND_COMPARISON_OPS = (ast.GtE, ast.Gt, ast.Eq)


def _is_unconditional_while(node: ast.While) -> bool:
    test = node.test
    if not isinstance(test, ast.Constant):
        return False
    if test.value is True:
        return True
    return test.value == 1 and not isinstance(test.value, bool)


def _contains_call(body: list[ast.stmt]) -> bool:
    for stmt in body:
        for child in ast.walk(stmt):
            if isinstance(child, ast.Call):
                return True
    return False


def _has_visible_step_bound(body: list[ast.stmt]) -> tuple[bool, str | None]:
    for stmt in body:
        for child in ast.walk(stmt):
            if not isinstance(child, ast.If):
                continue
            test = child.test
            if not isinstance(test, ast.Compare):
                continue
            if not any(isinstance(op, _BOUND_COMPARISON_OPS) for op in test.ops):
                continue
            has_exit = any(isinstance(inner, (ast.Break, ast.Return)) for inner in ast.walk(child))
            if has_exit:
                return True, "counter-check"
    return False, None


def _calls_itself(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            name = dotted_name(node.func)
            if name == func.name:
                return True
    return False


def detect_agents(tree: ast.Module, *, relative_path: str) -> tuple[Agent, ...]:
    """Find candidate agentic loops in a parsed module. See module docstring for the heuristic."""
    agents: list[Agent] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.While) and _is_unconditional_while(node):
            if not _contains_call(node.body):
                continue
            has_bound, source = _has_visible_step_bound(node.body)
            agents.append(
                Agent(
                    span=span_of(node, relative_path=relative_path),
                    name=None,
                    has_step_bound=has_bound,
                    structural_hash=structural_hash(node),
                    step_bound_source=source,
                )
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _calls_itself(node):
            has_bound, source = _has_visible_step_bound(node.body)
            agents.append(
                Agent(
                    span=span_of(node, relative_path=relative_path),
                    name=node.name,
                    has_step_bound=has_bound,
                    structural_hash=structural_hash(node),
                    step_bound_source=source,
                )
            )

    return tuple(agents)
