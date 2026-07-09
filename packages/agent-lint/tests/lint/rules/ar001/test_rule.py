from __future__ import annotations

from agent_reliability.core.contracts import RuleContext
from agent_reliability.core.model import Category, Confidence, Severity, default_config
from agent_reliability.core.model.ir import Agent, IRFragment
from agent_reliability.core.model.span import SourceSpan
from agent_reliability.lint.rules.ar001.rule import RULE


def _span(line: int = 1) -> SourceSpan:
    return SourceSpan(file="a.py", start_line=line, start_col=0, end_line=line, end_col=1)


def _agent(*, has_step_bound: bool, structural_hash: str, name: str | None = None) -> Agent:
    return Agent(
        span=_span(),
        name=name,
        has_step_bound=has_step_bound,
        structural_hash=structural_hash,
    )


def test_meta() -> None:
    assert RULE.meta.id == "AR001"
    assert RULE.meta.version == 1
    assert RULE.meta.default_severity is Severity.HIGH
    assert RULE.meta.default_confidence is Confidence.HIGH
    assert RULE.meta.category is Category.LOOP_SAFETY
    assert RULE.meta.frameworks == ()


def test_no_agents_no_findings() -> None:
    ctx = RuleContext(_fragment=IRFragment(file="a.py"), _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_bounded_agent_produces_no_finding() -> None:
    fragment = IRFragment(file="a.py", agents=(_agent(has_step_bound=True, structural_hash="h"),))
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    assert list(RULE.evaluate(ctx)) == []


def test_unbounded_agent_produces_one_finding() -> None:
    fragment = IRFragment(file="a.py", agents=(_agent(has_step_bound=False, structural_hash="h"),))
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 1
    assert findings[0].rule_id == "AR001"
    assert findings[0].severity is Severity.HIGH
    assert findings[0].confidence is Confidence.HIGH


def test_named_agent_evidence_mentions_recursion() -> None:
    fragment = IRFragment(
        file="a.py",
        agents=(_agent(has_step_bound=False, structural_hash="h", name="run_agent"),),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    finding = next(iter(RULE.evaluate(ctx)))
    assert "run_agent" in finding.description
    assert "calls itself" in finding.evidence


def test_anonymous_agent_evidence_mentions_while_true() -> None:
    fragment = IRFragment(file="a.py", agents=(_agent(has_step_bound=False, structural_hash="h"),))
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    finding = next(iter(RULE.evaluate(ctx)))
    assert "while True" in finding.evidence


def test_two_structurally_identical_agents_get_distinct_fingerprints() -> None:
    # Same shape (structural_hash) copy-pasted twice in one file -- occurrence_index must
    # disambiguate them so both findings survive dedup/baseline matching independently.
    fragment = IRFragment(
        file="a.py",
        agents=(
            _agent(has_step_bound=False, structural_hash="same-shape"),
            _agent(has_step_bound=False, structural_hash="same-shape"),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 2
    assert findings[0].fingerprint != findings[1].fingerprint
    assert findings[0].finding_id != findings[1].finding_id


def test_structurally_different_agents_each_start_their_own_occurrence_count() -> None:
    fragment = IRFragment(
        file="a.py",
        agents=(
            _agent(has_step_bound=False, structural_hash="shape-a"),
            _agent(has_step_bound=False, structural_hash="shape-b"),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    findings = list(RULE.evaluate(ctx))
    assert len(findings) == 2
    assert findings[0].fingerprint != findings[1].fingerprint


def test_fingerprint_is_deterministic_across_evaluations() -> None:
    fragment = IRFragment(file="a.py", agents=(_agent(has_step_bound=False, structural_hash="h"),))
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    first = list(RULE.evaluate(ctx))
    second = list(RULE.evaluate(ctx))
    assert first[0].fingerprint == second[0].fingerprint
