"""Retry-pattern recognition: turning decorators and manual loops into ``RetryPolicy`` entities.

**Honest capability statement.** Three patterns are recognized, each with a documented,
conservative rule for when the bound is considered ``UNKNOWN`` versus a guessed value:

1. **tenacity** (``@retry(...)`` / ``@tenacity.retry(...)``, the bare qualified ``@tenacity.retry``
   form with no parentheses at all, and ``@tenacity.retry()`` with empty parentheses — all three
   are tenacity's real all-defaults config; the latter two were initially missed entirely by this
   frontend and added after independent review caught the gaps in separate rounds): tenacity's
   well-documented default ``stop`` strategy, when the ``stop=`` keyword is omitted (with or
   without a call at all), is "never stop" — so all three forms are recorded as ``UNBOUNDED``,
   matching PLAN.md's own description of AR014 ("tenacity `stop=None`/missing"). A qualified name
   (``tenacity.retry``/``stamina.retry``) is unambiguous on its own and is never gated behind
   keyword-vocabulary disambiguation — only the truly ambiguous **unqualified** ``retry(...)``
   call form needs that (see ``_looks_like_tenacity``/``_looks_like_stamina``); gating the
   qualified call form behind the same kwarg check was a real bug (``@tenacity.retry()`` has no
   kwargs to check, so it was silently dropped).
   **Unqualified ``retry`` is a genuinely different case, not merely an unfixed version of the
   same bug**: bare, no-call ``@retry`` and call-with-no-disambiguating-kwargs ``@retry()`` are
   BOTH deliberately NOT recognized (no ``RetryPolicy`` at all) — the unqualified name is
   ambiguous between tenacity, stamina, and an unrelated local decorator
   (`from myproject.retry import retry`), and with no kwargs present there is nothing left to
   disambiguate with. An earlier version of this fix guessed tenacity for the bare no-call form;
   independent review correctly rejected that as an unsafe name-only upgrade, and the same
   reasoning applies identically to the empty-call form — silence, not a guess, in both cases.
   An explicit literal
   ``stop=None`` is likewise ``UNBOUNDED`` (also initially missed, also added after review). An
   explicit ``stop=stop_after_attempt(N)`` **or the qualified
   ``stop=tenacity.stop_after_attempt(N)`` form** with a literal ``N`` is recorded as
   ``BOUNDED(N)`` — matched against exactly these two known-real dotted names (a real gap
   independent review caught: the original match required an exact ``"stop_after_attempt"``
   string, missing the common fully-qualified form entirely). A LATER review round caught a
   regression in the first attempt at this fix: matching by trailing-attribute-name alone (e.g.
   anything ending in ``.stop_after_attempt``) would treat an unrelated
   ``myproject.stop_after_attempt(3)`` as tenacity's real stop strategy too, silently suppressing
   a real ``UNBOUNDED``/``UNKNOWN`` finding -- exactly the kind of guess this file's own
   philosophy exists to avoid. Any other ``stop=`` value (a variable, a composed strategy, a
   custom callable, or an unrecognized dotted name) is recorded as ``UNKNOWN`` — we are not
   confident enough in tenacity's broader API surface to interpret it, and guessing would be
   worse than silence.
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

**Named gap, verified rather than guessed at: ``max_retries=None`` is not detected.** E05's
required scope names it explicitly, and an earlier version of this file detected it (any call
site with a literal ``max_retries=None`` → ``UNBOUNDED``). Independent review challenged the
premise with real upstream source and was right to: ``requests.adapters.HTTPAdapter(max_retries=
None)`` resolves through ``urllib3.util.retry.Retry.from_int(None)``, which falls back to
urllib3's *default* (bounded) retry policy, not "unlimited" -- and the OpenAI Python SDK's client
constructor rejects ``max_retries=None`` outright with a ``TypeError``. "``max_retries=None``
means unbounded" is not actually true for either library named as motivating context, so
asserting ``UNBOUNDED`` for it would itself be a guess dressed up as a verified pattern -- exactly
what this frontend's own philosophy exists to avoid. Removed rather than kept and reworded;
recognizing this pattern correctly would require knowing which specific library's `max_retries`
parameter is being set (each has its own real semantics), which this frontend's dotted-name-only
evidence cannot establish.
"""

from __future__ import annotations

import ast

from agent_reliability.core.model.ir import RetryBound, RetryPolicy
from agent_reliability.lint.frontend.ast_utils import dotted_name, span_of, structural_hash


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
    hash_ = structural_hash(call)
    stop_kw = next((kw for kw in call.keywords if kw.arg == "stop"), None)
    if stop_kw is None:
        return RetryPolicy(
            span=span_of(call, relative_path=relative_path),
            bound=RetryBound.UNBOUNDED,
            source="tenacity",
            structural_hash=hash_,
        )
    stop_value = stop_kw.value
    if _is_none(stop_value):
        # Explicit `stop=None` is documented tenacity behavior for "never stop" -- as unbounded
        # as omitting `stop=` entirely, not merely "we don't know". Named explicitly in E05's
        # required scope (EXECUTION.md / CODEX_HANDOFF.md: "explicit stop=None"). Found missing
        # by independent review during E05 -- the omitted-entirely case above was implemented,
        # this explicit-None sibling case was not.
        return RetryPolicy(
            span=span_of(call, relative_path=relative_path),
            bound=RetryBound.UNBOUNDED,
            source="tenacity",
            structural_hash=hash_,
        )
    if (
        isinstance(stop_value, ast.Call)
        and dotted_name(stop_value.func) in ("stop_after_attempt", "tenacity.stop_after_attempt")
        and stop_value.args
    ):
        literal = _literal_int(stop_value.args[0])
        if literal is not None:
            return RetryPolicy(
                span=span_of(call, relative_path=relative_path),
                bound=RetryBound.BOUNDED,
                source="tenacity",
                structural_hash=hash_,
                max_attempts=literal,
            )
    return RetryPolicy(
        span=span_of(call, relative_path=relative_path),
        bound=RetryBound.UNKNOWN,
        source="tenacity",
        structural_hash=hash_,
    )


def _stamina_policy_from_call(call: ast.Call, *, relative_path: str) -> RetryPolicy:
    hash_ = structural_hash(call)
    attempts_kw = next((kw for kw in call.keywords if kw.arg == "attempts"), None)
    if attempts_kw is None:
        return RetryPolicy(
            span=span_of(call, relative_path=relative_path),
            bound=RetryBound.UNKNOWN,
            source="stamina",
            structural_hash=hash_,
        )
    if _is_none(attempts_kw.value):
        return RetryPolicy(
            span=span_of(call, relative_path=relative_path),
            bound=RetryBound.UNBOUNDED,
            source="stamina",
            structural_hash=hash_,
        )
    literal = _literal_int(attempts_kw.value)
    if literal is not None:
        return RetryPolicy(
            span=span_of(call, relative_path=relative_path),
            bound=RetryBound.BOUNDED,
            source="stamina",
            structural_hash=hash_,
            max_attempts=literal,
        )
    return RetryPolicy(
        span=span_of(call, relative_path=relative_path),
        bound=RetryBound.UNKNOWN,
        source="stamina",
        structural_hash=hash_,
    )


def _decorator_policies(
    func: ast.FunctionDef | ast.AsyncFunctionDef, *, relative_path: str
) -> list[RetryPolicy]:
    policies: list[RetryPolicy] = []
    for decorator in func.decorator_list:
        call = _decorator_call(decorator)
        if call is not None:
            name = dotted_name(call.func)
            # A QUALIFIED name ("tenacity.retry"/"stamina.retry") is already unambiguous --
            # `_looks_like_tenacity`/`_looks_like_stamina`'s kwarg-vocabulary check exists only to
            # disambiguate the AMBIGUOUS unqualified "retry" name, and must not gate the
            # qualified case too. Gating it unconditionally was a real bug: `@tenacity.retry()`
            # with empty parens (tenacity's own all-defaults call form -- as unbounded as the
            # bare no-parens form) has no kwargs at all, so it failed `_looks_like_tenacity` and
            # was silently dropped entirely. Found by independent review.
            if name == "tenacity.retry":
                policies.append(_tenacity_policy_from_call(call, relative_path=relative_path))
            elif name == "stamina.retry":
                policies.append(_stamina_policy_from_call(call, relative_path=relative_path))
            elif name == "retry":
                if _looks_like_tenacity(call):
                    policies.append(_tenacity_policy_from_call(call, relative_path=relative_path))
                elif _looks_like_stamina(call):
                    policies.append(_stamina_policy_from_call(call, relative_path=relative_path))
            continue
        # A bare decorator with no call at all (`@tenacity.retry` / `@stamina.retry`, no parens)
        # uses the library's all-defaults configuration -- no kwargs exist to disambiguate
        # tenacity from stamina the way `_looks_like_tenacity`/`_looks_like_stamina` do for the
        # call form. Only the QUALIFIED, unambiguous names are handled here -- an unqualified
        # bare `@retry` has even less disambiguating evidence than the call form (which at least
        # has kwargs to inspect) and could just as easily be `from myproject.retry import retry`,
        # an unrelated local decorator. An earlier version of this fix treated unqualified bare
        # `@retry` as tenacity by default; independent review correctly called this an unsafe
        # name-only upgrade with no real evidence behind it, so it's silence here (no RetryPolicy
        # at all), consistent with this file's "silence over guessing" philosophy.
        name = dotted_name(decorator)
        if name == "stamina.retry":
            policies.append(
                RetryPolicy(
                    span=span_of(decorator, relative_path=relative_path),
                    bound=RetryBound.UNKNOWN,
                    source="stamina",
                    structural_hash=structural_hash(decorator),
                )
            )
        elif name == "tenacity.retry":
            policies.append(
                RetryPolicy(
                    span=span_of(decorator, relative_path=relative_path),
                    bound=RetryBound.UNBOUNDED,
                    source="tenacity",
                    structural_hash=structural_hash(decorator),
                )
            )
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
                    structural_hash=structural_hash(node),
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
                    structural_hash=structural_hash(node),
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
