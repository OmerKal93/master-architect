from __future__ import annotations

from agent_reliability.core.contracts import RuleContext
from agent_reliability.core.model import Category, Confidence, Severity, default_config
from agent_reliability.core.model.ir import IRFragment, RetryBound, RetryPolicy
from agent_reliability.core.model.span import SourceSpan
from agent_reliability.lint.rules.ar014.rule import RULE


def _span(line: int = 1) -> SourceSpan:
    return SourceSpan(file="a.py", start_line=line, start_col=0, end_line=line, end_col=1)


def _retry_policy(
    *,
    bound: RetryBound,
    structural_hash: str,
    source: str = "tenacity",
    max_attempts: int | None = None,
) -> RetryPolicy:
    return RetryPolicy(
        span=_span(),
        bound=bound,
        source=source,
        structural_hash=structural_hash,
        max_attempts=max_attempts,
    )


def test_meta() -> None:
    assert RULE.meta.id == "AR014"
    assert RULE.meta.version == 1
    assert RULE.meta.default_severity is Severity.HIGH
    assert RULE.meta.default_confidence is Confidence.HIGH
    assert RULE.meta.category is Category.RETRY_SAFETY
    assert RULE.meta.frameworks == ()


def test_no_retry_policies_no_findings() -> None:
    ctx = RuleContext(_fragment=IRFragment(file="a.py"), _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_bounded_retry_produces_no_finding() -> None:
    fragment = IRFragment(
        file="a.py",
        retry_policies=(
            _retry_policy(bound=RetryBound.BOUNDED, structural_hash="h", max_attempts=3),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_unknown_retry_produces_no_finding() -> None:
    fragment = IRFragment(
        file="a.py",
        retry_policies=(_retry_policy(bound=RetryBound.UNKNOWN, structural_hash="h"),),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_unbounded_retry_produces_one_finding() -> None:
    fragment = IRFragment(
        file="a.py",
        retry_policies=(
            _retry_policy(bound=RetryBound.UNBOUNDED, structural_hash="h", source="tenacity"),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 1
    assert findings[0].rule_id == "AR014"
    assert findings[0].severity is Severity.HIGH
    assert findings[0].confidence is Confidence.HIGH
    assert "tenacity" in findings[0].evidence


def test_unbounded_manual_loop_retry_produces_one_finding() -> None:
    fragment = IRFragment(
        file="a.py",
        retry_policies=(
            _retry_policy(bound=RetryBound.UNBOUNDED, structural_hash="h", source="manual-loop"),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 1
    assert "manual-loop" in findings[0].evidence
    assert findings[0].confidence is Confidence.HIGH


def test_two_structurally_identical_retries_get_distinct_fingerprints() -> None:
    fragment = IRFragment(
        file="a.py",
        retry_policies=(
            _retry_policy(bound=RetryBound.UNBOUNDED, structural_hash="same-shape"),
            _retry_policy(bound=RetryBound.UNBOUNDED, structural_hash="same-shape"),
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
        retry_policies=(_retry_policy(bound=RetryBound.UNBOUNDED, structural_hash="h"),),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    first = list(RULE.evaluate(ctx))
    second = list(RULE.evaluate(ctx))
    assert first[0].fingerprint == second[0].fingerprint
