"""AR003: Tool or external call without timeout.

Follows the AR001 reference layout (see ``agent_reliability.lint.rules.ar001.rule``): this file
(logic + metadata), ``docs.md`` (catalog page), and fixtures + ``expected.json`` under
``fixtures/rules/AR003/`` at the repo root.

Detection: fires once per ``ToolCall`` in the micro-IR whose ``callee`` matches the named
call-shape allowlist below (``requests``/``httpx``/``urllib3`` module-level HTTP methods, plus
OpenAI/Anthropic SDK method-chain shapes already recognizable from the frontend's textual
``callee`` string, per CODEX_HANDOFF.md's explicit E05 scope) and whose ``timeout`` evidence
shows the timeout keyword was checked and found either absent (``TimeoutPolicy(present=False)``)
or explicitly ``None``. This rule trusts the frontend's ``ToolCall``/``TimeoutPolicy`` evidence
as-is (see ``agent_reliability.lint.frontend.calls``) and does not re-derive it. A ``ToolCall``
whose ``timeout`` field is the Python value ``None`` (not a ``TimeoutPolicy`` at all) means "no
timeout evidence was even looked for" per that field's own IR contract -- unknown, not
known-absent -- and never fires; an earlier version of this rule conflated the two, caught by
independent review.

**Why an allowlist, not "any attribute call".** The frontend records *every* attribute-chain call
site as a candidate ``ToolCall`` (see ``calls.py``'s module docstring) -- it deliberately does not
filter by known-SDK name, leaving that classification to this rule. Firing on every such call
would flag arbitrary in-process method calls (``obj.method(...)``) that have nothing to do with
external I/O, which is exactly the false-positive shape this rule's own docs.md documents as
out of scope (e.g. a bare ``client.payments.charges.create(...)`` is not in this allowlist and
produces no finding -- silence over guessing, per this repo's stated philosophy). The allowlist is
a plain, reviewable Python constant (not a bundled data file) so this rule stays as pure and
I/O-free as AR001; see docs.md for the "known limits" this trade-off implies.

**Short (2-segment) SDK suffixes are included but at reduced confidence, not excluded.**
CODEX_HANDOFF.md explicitly requires recognizing OpenAI/Anthropic calls "already recognizable by
the current frontend" -- the frontend's textual callee already IS ``client.messages.create`` for
Anthropic's most common call shape -- while *also* requiring conservative, low-false-positive
matching. Independent review oscillated between these two requirements across several rounds
(narrow the allowlist to cut false positives vs. widen it to cover required scope) because a
binary include/exclude allowlist genuinely cannot satisfy both at once: a 2-segment suffix like
``messages.create`` is real, common Anthropic usage AND collides with unrelated application code
using the same method name (e.g. a notification service's own
``notification.messages.create(...)``). The resolution is a third axis: match it, but at
``Confidence.LOW`` rather than ``Confidence.HIGH`` -- honestly representing "this looks like it
could be the pattern, but the match is name-only, not structurally provable the way a
module-qualified ``requests.post`` or a specific 3+-segment shape like
``chat.completions.create`` is". See ``_confidence_for`` below and docs.md for the full writeup.
"""

from __future__ import annotations

from collections.abc import Iterable

from agent_reliability.core.contracts import RuleContext, RuleMeta
from agent_reliability.core.model import (
    Category,
    Confidence,
    Finding,
    Severity,
    compute_fingerprint,
    derive_finding_id,
)
from agent_reliability.core.model.ir import ToolCall

# PLAN.md's rule catalog (section 14) records AR003 as high-severity/high-confidence: a missing
# `timeout=` on a recognized external-call shape is provably present in the source, not a guess.
META = RuleMeta(
    id="AR003",
    version=1,
    title="Tool or external call without timeout",
    default_severity=Severity.HIGH,
    default_confidence=Confidence.HIGH,
    category=Category.TIMEOUTS,
)

WHY_IT_MATTERS = (
    "A call to an external service with no timeout can hang the calling process indefinitely if "
    "the remote end never responds -- a stalled connection, a slow upstream, or a network "
    "partition. In an agent loop this blocks the whole run (or, if the loop itself is unbounded, "
    "combines with AR001 into a process that never returns and never stops accruing cost)."
)

# Client/session-level configuration is deliberately NOT offered as remediation here: this rule
# cannot see it (see docs.md's "Known limitation") and would keep reporting the finding even
# after a user applied that fix, directing them at a "fix" the analyzer can't verify. An earlier
# version of this string suggested it anyway -- remediation text is part of the emitted finding
# contract, so this was a real bug, not wording drift. Caught by independent review.
#
# TS/JS parity (E-ts01): language-neutral wording -- ToolCall is a language-neutral IR entity
# (see AR001's own `_evidence_for` fix), and "timeout=" is Python-keyword-argument-specific
# syntax that reads as wrong on a JS/TS finding (whose idiom is a `{ timeout: ... }` options
# object, not a keyword argument). Caught by independent review of the TS/JS frontend slice.
REMEDIATION = (
    "Add an explicit timeout configuration at this call site (a `timeout=` keyword argument, a "
    "`{ timeout: ... }` option, or a library-specific timeout object, depending on the "
    "language/library). Configuring a timeout on the client/session instead does make the call "
    "genuinely safe, but this rule cannot see that and will keep reporting the finding "
    'regardless -- see docs.md\'s "Known limitation" section.'
)

# Module-qualified HTTP client calls: the textual callee itself names the library (e.g.
# "requests.post"), so no further disambiguation is needed. See docs.md for the exact method
# lists and why session/instance-based calls (e.g. `session.post(...)`) are not included --
# the frontend cannot statically know what `session` is bound to.
#
# TS/JS parity (E-ts01): "axios" is the JS-ecosystem sibling of requests/httpx here -- same
# concept (a named HTTP client library's module-qualified method call), same allowlist, not a
# new rule.
#
# Known, accepted consequence of sharing one language-neutral allowlist across both frontends
# (flagged by independent review): a .py file with a local object literally named `axios`
# calling `.post(...)`/`.get(...)`/etc with no timeout would now also match, since this rule
# only ever sees the frontend's textual `callee` string, never which language produced it. Not
# special-cased -- the blast radius is a Python identifier that happens to share a name with a
# JS HTTP library, and per this rule's own "silence over guessing" philosophy elsewhere, a false
# positive here is far less likely than a real `axios.post(...)` call going unflagged in TS/JS.
#
# Bare `fetch(...)` is deliberately NOT included: it is a bare-name call, not an
# attribute-chain call, and calls.py's own module docstring already documents "only
# attribute-chain calls are recorded" as a stated Python-frontend trade-off -- the TS/JS frontend
# (ts_js_frontend.py / tools/ts_frontend/parse_one_file.mjs) keeps that same scope rather than
# special-casing one bare-name callee just because it is common in JS. A documented limitation,
# not a silent gap -- see docs.md.
_HTTP_LIBRARY_METHOD_NAMES = ("get", "post", "put", "patch", "delete", "head", "options", "request")
_HTTP_LIBRARY_CALLEES: frozenset[str] = frozenset(
    f"{library}.{method}"
    for library in ("requests", "httpx", "axios")
    for method in _HTTP_LIBRARY_METHOD_NAMES
) | frozenset({"httpx.stream", "urllib3.request", "urllib3.urlopen"})

# Dotted-suffix shapes recognized as OpenAI/Anthropic SDK calls, matched against the trailing
# segments of the callee (e.g. "client.chat.completions.create" ends with
# "chat.completions.create"). Sources: OpenAI Python SDK
# (https://github.com/openai/openai-python) and Anthropic Python SDK
# (https://github.com/anthropics/anthropic-sdk-python) public method surfaces as of this PR.
#
# Split by specificity, not by inclusion -- see module docstring and _confidence_for(). >= 3
# segments = structurally distinctive enough to trust at Confidence.HIGH. 2 segments = real SDK
# usage but textually indistinguishable from unrelated application code = Confidence.LOW.
_LLM_SDK_HIGH_CONFIDENCE_SUFFIXES: tuple[str, ...] = (
    "chat.completions.create",
    "audio.transcriptions.create",
    "audio.translations.create",
    "audio.speech.create",
)
_LLM_SDK_LOW_CONFIDENCE_SUFFIXES: tuple[str, ...] = (
    "completions.create",
    "embeddings.create",
    "images.generate",
    "images.edit",
    "moderations.create",
    "responses.create",
    "messages.create",
    "messages.stream",
)


def _matches_any_suffix(callee: str, suffixes: tuple[str, ...]) -> bool:
    return any(callee == suffix or callee.endswith(f".{suffix}") for suffix in suffixes)


def _is_recognized_call_shape(callee: str) -> bool:
    """The AR003 allowlist. See module docstring for the conservative-matching rationale."""
    return (
        callee in _HTTP_LIBRARY_CALLEES
        or _matches_any_suffix(callee, _LLM_SDK_HIGH_CONFIDENCE_SUFFIXES)
        or _matches_any_suffix(callee, _LLM_SDK_LOW_CONFIDENCE_SUFFIXES)
    )


def _confidence_for(callee: str) -> Confidence:
    """HIGH for structurally-distinctive matches (module-qualified HTTP calls, >= 3-segment SDK
    shapes); LOW for the 2-segment SDK suffixes that are real usage but name-only matches
    indistinguishable from unrelated code. See module docstring for the full rationale."""
    if callee in _HTTP_LIBRARY_CALLEES:
        return Confidence.HIGH
    if _matches_any_suffix(callee, _LLM_SDK_HIGH_CONFIDENCE_SUFFIXES):
        return Confidence.HIGH
    return Confidence.LOW


def _lacks_timeout(tool_call: ToolCall) -> bool:
    if tool_call.timeout is None:
        # Per ToolCall.timeout's own IR contract (agent_reliability.core.model.ir): None means
        # "no timeout evidence was even looked for at this call site", distinct from
        # TimeoutPolicy(present=False), which means it WAS checked and found absent. Treating
        # "we don't know" as "we know it's missing" would turn unknown evidence into a
        # high-confidence positive finding -- exactly the kind of guess this codebase's stated
        # philosophy exists to avoid. Silence, not a guess. Caught by independent review: an
        # earlier version of this rule fired on this case, and a unit test baked the wrong
        # semantics in as expected behavior.
        return False
    if not tool_call.timeout.present:
        return True
    if not tool_call.timeout.explicit_none:
        return False
    # `timeout=None` disables the timeout entirely for requests/httpx -- verified, documented
    # library behavior (TimeoutPolicy.explicit_none's own docstring is scoped to exactly these
    # two libraries). That verification does NOT extend to the OpenAI/Anthropic SDK shapes this
    # rule also recognizes -- generalizing a claim proven for one library family to every
    # recognized callee is exactly the mistake independent review caught elsewhere in this same
    # PR (the max_retries=None removal). Rather than repeat it, `explicit_none` only counts as
    # unsafe for the HTTP-library callees it was actually verified for; for SDK shapes it's
    # treated the same as a non-literal timeout (present, not provably absent) -- silence, not an
    # unverified guess.
    return tool_call.callee in _HTTP_LIBRARY_CALLEES


def _evidence_for(tool_call: ToolCall) -> str:
    # explicit_none is a real, explicit null/None timeout value -- "no timeout= keyword argument"
    # would be factually wrong for that case, caught by independent review. Not reached when
    # tool_call.timeout is None (that shape reads "no timeout evidence was even looked for",
    # a different, correct meaning of "no timeout configuration").
    #
    # TS/JS parity (E-ts01): language-neutral wording, matching AR001's own evidence-text fix --
    # "timeout=" keyword-argument phrasing is Python-specific and reads as wrong for a JS/TS
    # finding (whose timeout idiom is a `{ timeout: ... }` object property).
    if tool_call.timeout is not None and tool_call.timeout.explicit_none:
        return (
            f"{tool_call.callee}(...) has an explicit null timeout, which disables the timeout "
            "entirely"
        )
    return f"{tool_call.callee}(...) has no visible timeout configuration"


def _description_for(tool_call: ToolCall) -> str:
    return f"This call to `{tool_call.callee}` has no statically visible timeout."


class AR003Rule:
    """See module docstring."""

    meta = META

    def evaluate(self, ctx: RuleContext) -> Iterable[Finding]:
        # Same occurrence_index disambiguation strategy as AR001 -- see that rule's evaluate().
        occurrence_counts: dict[str, int] = {}

        for tool_call in ctx.tool_calls():
            if not _is_recognized_call_shape(tool_call.callee):
                continue
            if not _lacks_timeout(tool_call):
                continue

            occurrence_index = occurrence_counts.get(tool_call.structural_hash, 0)
            occurrence_counts[tool_call.structural_hash] = occurrence_index + 1

            fingerprint = compute_fingerprint(
                rule_id=self.meta.id,
                rule_major_version=self.meta.version,
                normalized_path=tool_call.span.file,
                structural_hash=tool_call.structural_hash,
                occurrence_index=occurrence_index,
            )

            yield Finding(
                rule_id=self.meta.id,
                rule_version=self.meta.version,
                title=self.meta.title,
                description=_description_for(tool_call),
                severity=self.meta.default_severity,
                confidence=_confidence_for(tool_call.callee),
                category=self.meta.category,
                span=tool_call.span,
                evidence=_evidence_for(tool_call),
                why_it_matters=WHY_IT_MATTERS,
                remediation=REMEDIATION,
                fingerprint=fingerprint,
                finding_id=derive_finding_id(fingerprint),
            )


RULE = AR003Rule()
