from __future__ import annotations

from agent_reliability.core.contracts import RuleContext
from agent_reliability.core.model import Category, Confidence, Severity, default_config
from agent_reliability.core.model.ir import IRFragment, TimeoutPolicy, ToolCall
from agent_reliability.core.model.span import SourceSpan
from agent_reliability.lint.rules.ar003.rule import RULE


def _span(line: int = 1) -> SourceSpan:
    return SourceSpan(file="a.py", start_line=line, start_col=0, end_line=line, end_col=1)


def _tool_call(
    *,
    callee: str,
    structural_hash: str,
    timeout: TimeoutPolicy | None,
) -> ToolCall:
    return ToolCall(span=_span(), callee=callee, structural_hash=structural_hash, timeout=timeout)


def test_meta() -> None:
    assert RULE.meta.id == "AR003"
    assert RULE.meta.version == 1
    assert RULE.meta.default_severity is Severity.HIGH
    assert RULE.meta.default_confidence is Confidence.HIGH
    assert RULE.meta.category is Category.TIMEOUTS
    assert RULE.meta.frameworks == ()


def test_no_tool_calls_no_findings() -> None:
    ctx = RuleContext(_fragment=IRFragment(file="a.py"), _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_recognized_callee_with_timeout_present_produces_no_finding() -> None:
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="requests.post",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=True, seconds=10.0),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_recognized_callee_with_non_literal_timeout_present_produces_no_finding() -> None:
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="requests.post",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=True, seconds=None),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_explicit_timeout_equals_none_produces_one_finding() -> None:
    # `timeout=None` disables the timeout entirely for requests/httpx -- as unbounded as an
    # absent keyword, not the weaker-but-present "non-literal timeout" case above. Caught by
    # independent review: the original implementation only checked `.present`, so a call with
    # `timeout=None` was incorrectly treated as safe.
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="requests.post",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=True, seconds=None, explicit_none=True),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 1


def test_explicit_timeout_none_on_sdk_shape_does_not_fire() -> None:
    # explicit_none's "unsafe" semantics are verified for requests/httpx specifically -- that
    # verification does not extend to OpenAI/Anthropic SDK shapes. Generalizing an unverified
    # claim across every recognized callee is exactly the mistake independent review caught
    # elsewhere in this same PR (the max_retries=None removal); this test guards against
    # repeating it here.
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="client.chat.completions.create",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=True, seconds=None, explicit_none=True),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_recognized_callee_with_timeout_absent_produces_one_finding() -> None:
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="requests.post",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=False),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 1
    assert findings[0].rule_id == "AR003"
    assert findings[0].severity is Severity.HIGH
    assert findings[0].confidence is Confidence.HIGH
    assert "requests.post" in findings[0].evidence


def test_tool_call_with_timeout_field_itself_none_produces_no_finding() -> None:
    # ToolCall.timeout being the Python value None (not a TimeoutPolicy at all) means "no timeout
    # evidence was even looked for at this call site" per that field's own IR contract -- unknown,
    # not known-absent. Firing here would turn unknown evidence into a high-confidence positive
    # finding. An earlier version of this rule (and this exact test, inverted) got this backwards;
    # caught by independent review.
    fragment = IRFragment(
        file="a.py",
        tool_calls=(_tool_call(callee="httpx.get", structural_hash="h", timeout=None),),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_openai_sdk_shape_is_recognized_at_high_confidence() -> None:
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="client.chat.completions.create",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=False),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 1
    assert findings[0].confidence is Confidence.HIGH


def test_openai_audio_transcription_shape_is_recognized_at_high_confidence() -> None:
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="client.audio.transcriptions.create",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=False),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 1
    assert findings[0].confidence is Confidence.HIGH


def test_anthropic_messages_create_shape_is_recognized_at_low_confidence() -> None:
    # `client.messages.create` is Anthropic's single most common real call shape.
    # CODEX_HANDOFF.md explicitly requires Anthropic calls "already recognizable by the current
    # frontend" -- the frontend's textual callee already is this exact string, so this must fire.
    # But it's a 2-segment, name-only match (see the next test for the exact collision this
    # implies), so it fires at Confidence.LOW, not HIGH -- independent review oscillated between
    # excluding this shape entirely (over collision risk) and including it at full confidence
    # (silently dropping required scope) across several rounds; variable confidence resolves both.
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="client.messages.create",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=False),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 1
    assert findings[0].confidence is Confidence.LOW


def test_generic_two_segment_suffix_fires_at_low_confidence() -> None:
    # An unrelated notification service exposing its own `messages.create` method IS
    # indistinguishable, by text alone, from Anthropic's `messages.create` -- this rule fires on
    # it too, but only at Confidence.LOW, honestly reflecting that the match is name-only, not
    # structurally provable. Documented, accepted trade-off (see docs.md and AR001's identical
    # precedent for its loop heuristic), not a bug.
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="notification.messages.create",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=False),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 1
    assert findings[0].confidence is Confidence.LOW


def test_allowlist_rejects_unrecognized_callee() -> None:
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="client.payments.charges.create",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=False),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_allowlist_rejects_bare_module_name_without_method() -> None:
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="requests.session",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=False),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_two_structurally_identical_calls_get_distinct_fingerprints() -> None:
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="requests.post",
                structural_hash="same-shape",
                timeout=TimeoutPolicy(span=_span(), present=False),
            ),
            _tool_call(
                callee="requests.post",
                structural_hash="same-shape",
                timeout=TimeoutPolicy(span=_span(), present=False),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 2
    assert findings[0].fingerprint != findings[1].fingerprint
    assert findings[0].finding_id != findings[1].finding_id


def test_fingerprint_is_deterministic_across_evaluations() -> None:
    fragment = IRFragment(
        file="a.py",
        tool_calls=(
            _tool_call(
                callee="requests.post",
                structural_hash="h",
                timeout=TimeoutPolicy(span=_span(), present=False),
            ),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    first = list(RULE.evaluate(ctx))
    second = list(RULE.evaluate(ctx))
    assert first[0].fingerprint == second[0].fingerprint
