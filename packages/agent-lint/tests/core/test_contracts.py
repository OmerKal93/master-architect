from __future__ import annotations

import inspect
from collections.abc import Iterable
from pathlib import Path

from agent_reliability.core.contracts import Frontend, Rule, RuleContext, RuleMeta
from agent_reliability.core.model import (
    Agent,
    Category,
    Confidence,
    Config,
    Finding,
    IRFragment,
    Severity,
    SourceSpan,
    compute_fingerprint,
    default_config,
    derive_finding_id,
)


def _span() -> SourceSpan:
    return SourceSpan(file="a.py", start_line=1, start_col=0, end_line=1, end_col=1)


class TestRuleContextHasNoIOSurface:
    """Structural proof that RuleContext cannot be used to perform I/O.

    This does not (yet) grep rule *implementations* for forbidden calls — that CI guard is
    added in E05 once real rule modules exist to check. This test instead asserts the contract
    itself: every public method on RuleContext returns data, and none of its parameters or
    return types are filesystem/network/process handles.
    """

    def test_public_methods_take_no_arguments_that_could_be_paths_or_handles(self) -> None:
        for name, member in inspect.getmembers(RuleContext):
            if name.startswith("_"):
                continue
            if isinstance(member, property):
                continue
            if not callable(member):
                continue
            sig = inspect.signature(member)
            params = [p for p in sig.parameters if p != "self"]
            assert params == [], (
                f"RuleContext.{name} accepts arguments {params!r} — RuleContext methods must "
                "be pure read accessors with no parameters that could smuggle in a path, "
                "command, or handle."
            )

    def test_context_holds_only_data_and_returns_only_sequences_or_scalars(self) -> None:
        fragment = IRFragment(file="a.py")
        ctx = RuleContext(_fragment=fragment, _config=default_config())
        assert isinstance(ctx.file, str)
        assert isinstance(ctx.config, Config)
        assert isinstance(ctx.agents(), tuple)
        assert isinstance(ctx.tool_calls(), tuple)
        assert isinstance(ctx.retry_policies(), tuple)


class TestRuleContextAccessors:
    def test_exposes_fragment_contents(self) -> None:
        agent = Agent(span=_span(), name="loop", has_step_bound=False)
        fragment = IRFragment(file="agent/loop.py", agents=(agent,))
        ctx = RuleContext(_fragment=fragment, _config=default_config())
        assert ctx.file == "agent/loop.py"
        assert ctx.agents() == (agent,)
        assert ctx.tool_calls() == ()
        assert ctx.retry_policies() == ()


class _ToyRule:
    """A minimal Rule implementation, proving the Protocol is satisfiable and useful."""

    meta = RuleMeta(
        id="TOY001",
        version=1,
        title="Toy rule: flags every agent with no step bound",
        default_severity=Severity.HIGH,
        default_confidence=Confidence.HIGH,
        category=Category.LOOP_SAFETY,
    )

    def evaluate(self, ctx: RuleContext) -> Iterable[Finding]:
        for agent in ctx.agents():
            if agent.has_step_bound:
                continue
            fingerprint = compute_fingerprint(
                rule_id=self.meta.id,
                rule_major_version=self.meta.version,
                normalized_path=agent.span.file,
                structural_hash="toy",
            )
            yield Finding(
                rule_id=self.meta.id,
                rule_version=self.meta.version,
                title=self.meta.title,
                description="toy",
                severity=self.meta.default_severity,
                confidence=self.meta.default_confidence,
                category=self.meta.category,
                span=agent.span,
                evidence="toy evidence",
                why_it_matters="toy",
                remediation="toy",
                fingerprint=fingerprint,
                finding_id=derive_finding_id(fingerprint),
            )


class _ToyFrontend:
    """A minimal Frontend implementation, proving the Protocol is satisfiable."""

    name = "toy"

    def supports(self, path: Path) -> bool:
        return path.suffix == ".toy"

    def lower(self, path: Path, *, root: Path) -> IRFragment:
        relative = path.relative_to(root).as_posix()
        return IRFragment(file=relative)


def test_toy_rule_satisfies_rule_protocol() -> None:
    rule = _ToyRule()
    assert isinstance(rule, Rule)


def test_toy_rule_produces_findings_deterministically() -> None:
    rule = _ToyRule()
    fragment = IRFragment(
        file="a.py",
        agents=(Agent(span=_span(), name=None, has_step_bound=False),),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    first = list(rule.evaluate(ctx))
    second = list(rule.evaluate(ctx))
    assert len(first) == 1
    assert first[0].fingerprint == second[0].fingerprint


def test_toy_rule_is_silent_on_bounded_agent() -> None:
    rule = _ToyRule()
    fragment = IRFragment(
        file="a.py",
        agents=(
            Agent(span=_span(), name=None, has_step_bound=True, step_bound_source="for-range"),
        ),
    )
    ctx = RuleContext(_fragment=fragment, _config=default_config())
    assert list(rule.evaluate(ctx)) == []


def test_toy_frontend_satisfies_frontend_protocol() -> None:
    assert isinstance(_ToyFrontend(), Frontend)


def test_toy_frontend_lowers_to_repo_relative_path(tmp_path: Path) -> None:
    frontend = _ToyFrontend()
    (tmp_path / "sub").mkdir()
    file_path = tmp_path / "sub" / "x.toy"
    file_path.write_text("", encoding="utf-8")
    fragment = frontend.lower(file_path, root=tmp_path)
    assert fragment.file == "sub/x.toy"
