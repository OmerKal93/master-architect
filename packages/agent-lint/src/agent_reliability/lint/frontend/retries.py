"""Retry-pattern recognition: turning decorators and manual loops into ``RetryPolicy`` entities.

**Honest capability statement.** Three patterns are recognized, each with a documented,
conservative rule for when the bound is considered ``UNKNOWN`` versus a guessed value:

1. **tenacity** (``@retry(...)`` / ``@tenacity.retry(...)``): tenacity's well-documented default
   ``stop`` strategy, when the ``stop=`` keyword is omitted entirely, is "never stop" — so an
   omitted ``stop=`` is recorded as ``UNBOUNDED``, matching PLAN.md's own description of AR014
   ("tenacity `stop=None`/missing"). An explicit ``stop=stop_after_attempt(N)`` with a literal
   ``N`` is recorded as ``BOUNDED(N)``. Any other ``stop=`` value (a variable, a composed
   strategy, a custom callable) is recorded as ``UNKNOWN`` — we are not confident enough in
   tenacity's broader API surface to interpret it, and guessing would be worse than silence.
2. **stamina** (``@stamina.retry(...)``): an explicit literal ``attempts=N`` is ``BOUNDED(N)``;
   an explicit ``attempts=None`` is ``UNBOUNDED`` (stamina's documented "retry forever" value).
   If ``attempts=`` is omitted, this is recorded as ``UNKNOWN`` rather than assuming a specific
   library default — the exact default has changed across stamina versions and asserting one
   with confidence here would risk being wrong.
3. **Manual retry loops**: a ``for`` loop over a literal ``range(N)`` whose body contains a
   ``try``/``except`` is ``BOUNDED(N)``. A ``while True:``/``while 1:`` loop whose body contains
   a ``try``/``except`` with a ``break`` inside the ``try`` body (the "keep retrying until it
   succeeds" shape) is ``UNBOUNDED``. More elaborate manual patterns (a hand-rolled counter
   compared against a variable limit, for instance) are not detected — a stated limitation,
   consistent with "silence over guessing" everywhere else in this frontend.
"""

from __future__ import annotations

import ast

from agent_reliability.core.model.ir import RetryBound, RetryPolicy
from agent_reliability.lint.frontend.ast_utils import dotted_name, span_of

_TENACITY_DECORATOR_NAMES = {"retry", "tenacity.retry"}
_STAMINA_DECORATOR_NAMES = {"stamina.retry", "retry"}


def _decorator_call(decorator: ast.expr) -> ast.Call | None:
    return decorator if isinstance(decorator, ast.Call) else None


def _literal_int(node: ast.expr | None) -> int | None:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    ):
        return node.value
    return None


def _is_none(node: ast.expr | None) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _tenacity_policy_from_call(call: ast.Call, *, relative_path: str) -> RetryPolicy:
    stop_kw = next((kw for kw in call.keywords if kw.arg == "stop"), None)
    if stop_kw is None:
        return RetryPolicy(
            span=span_of(call, relative_path=relative_path),
            bound=RetryBound.UNBOUNDED,
            source="tenacity",
        )
    stop_value = stop_kw.value
    if (
        isinstance(stop_value, ast.Call)
        and dotted_name(stop_value.func) == "stop_after_attempt"
        and stop_value.args
    ):
        literal = _literal_int(stop_value.args[0])
        if literal is not None:
            return RetryPolicy(
                span=span_of(call, relative_path=relative_path),
                bound=RetryBound.BOUNDED,
                source="tenacity",
                max_attempts=literal,
            )
    return RetryPolicy(
        span=span_of(call, relative_path=relative_path),
        bound=RetryBound.UNKNOWN,
        source="tenacity",
    )


def _stamina_policy_from_call(call: ast.Call, *, relative_path: str) -> RetryPolicy:
    attempts_kw = next((kw for kw in call.keywords if kw.arg == "attempts"), None)
    if attempts_kw is None:
        return RetryPolicy(
            span=span_of(call, relative_path=relative_path),
            bound=RetryBound.UNKNOWN,
            source="stamina",
        )
    if _is_none(attempts_kw.value):
        return RetryPolicy(
            span=span_of(call, relative_path=relative_path),
            bound=RetryBound.UNBOUNDED,
            source="stamina",
        )
    literal = _literal_int(attempts_kw.value)
    if literal is not None:
        return RetryPolicy(
            span=span_of(call, relative_path=relative_path),
            bound=RetryBound.BOUNDED,
            source="stamina",
            max_attempts=literal,
        )
    return RetryPolicy(
        span=span_of(call, relative_path=relative_path), bound=RetryBound.UNKNOWN, source="stamina"
    )


def _decorator_policies(
    func: ast.FunctionDef | ast.AsyncFunctionDef, *, relative_path: str
) -> list[RetryPolicy]:
    policies: list[RetryPolicy] = []
    for decorator in func.decorator_list:
        call = _decorator_call(decorator)
        if call is None:
            continue
        name = dotted_name(call.func)
        if name in _TENACITY_DECORATOR_NAMES and _looks_like_tenacity(call):
            policies.append(_tenacity_policy_from_call(call, relative_path=relative_path))
        elif name in _STAMINA_DECORATOR_NAMES and _looks_like_stamina(call):
            policies.append(_stamina_policy_from_call(call, relative_path=relative_path))
    return policies


def _looks_like_tenacity(call: ast.Call) -> bool:
    # "retry" (unqualified) is ambiguous between tenacity and stamina; disambiguate by keyword
    # vocabulary, since both libraries commonly get imported as a bare `retry` decorator name.
    kwarg_names = {kw.arg for kw in call.keywords}
    return "stop" in kwarg_names or "wait" in kwarg_names or "reraise" in kwarg_names


def _looks_like_stamina(call: ast.Call) -> bool:
    kwarg_names = {kw.arg for kw in call.keywords}
    return "attempts" in kwarg_names or "timeout" in kwarg_names


def _has_try_except(body: list[ast.stmt]) -> ast.Try | None:
    for stmt in body:
        for child in ast.walk(stmt):
            if isinstance(child, ast.Try) and child.handlers:
                return child
    return None


def _try_body_has_break(try_node: ast.Try) -> bool:
    for stmt in try_node.body:
        for child in ast.walk(stmt):
            if isinstance(child, ast.Break):
                return True
    return False


def _manual_loop_policies(tree: ast.Module, *, relative_path: str) -> list[RetryPolicy]:
    policies: list[RetryPolicy] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
            if dotted_name(node.iter.func) != "range" or not node.iter.args:
                continue
            literal = _literal_int(node.iter.args[0])
            if literal is None:
                continue
            if _has_try_except(node.body) is None:
                continue
            policies.append(
                RetryPolicy(
                    span=span_of(node, relative_path=relative_path),
                    bound=RetryBound.BOUNDED,
                    source="manual-loop",
                    max_attempts=literal,
                )
            )
        elif isinstance(node, ast.While):
            test = node.test
            is_unconditional = isinstance(test, ast.Constant) and (
                test.value is True or (test.value == 1 and not isinstance(test.value, bool))
            )
            if not is_unconditional:
                continue
            try_node = _has_try_except(node.body)
            if try_node is None or not _try_body_has_break(try_node):
                continue
            policies.append(
                RetryPolicy(
                    span=span_of(node, relative_path=relative_path),
                    bound=RetryBound.UNBOUNDED,
                    source="manual-loop",
                )
            )
    return policies


def detect_retry_policies(tree: ast.Module, *, relative_path: str) -> tuple[RetryPolicy, ...]:
    """Find candidate retry constructs in a parsed module. See module docstring for heuristics."""
    policies: list[RetryPolicy] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            policies.extend(_decorator_policies(node, relative_path=relative_path))

    policies.extend(_manual_loop_policies(tree, relative_path=relative_path))

    return tuple(policies)
