from __future__ import annotations

import pytest

from agent_reliability.core.model import (
    Agent,
    Diagnostic,
    DiagnosticLevel,
    IRFragment,
    RetryBound,
    RetryPolicy,
    SourceSpan,
    TimeoutPolicy,
    ToolCall,
)


def _span() -> SourceSpan:
    return SourceSpan(file="a.py", start_line=1, start_col=0, end_line=1, end_col=1)


class TestRetryPolicy:
    def test_bounded_requires_max_attempts(self) -> None:
        with pytest.raises(ValueError, match="max_attempts"):
            RetryPolicy(span=_span(), bound=RetryBound.BOUNDED, source="tenacity")

    def test_unbounded_rejects_max_attempts(self) -> None:
        with pytest.raises(ValueError, match="max_attempts"):
            RetryPolicy(
                span=_span(), bound=RetryBound.UNBOUNDED, source="manual-loop", max_attempts=3
            )

    def test_unknown_rejects_max_attempts(self) -> None:
        with pytest.raises(ValueError, match="max_attempts"):
            RetryPolicy(span=_span(), bound=RetryBound.UNKNOWN, source="unknown", max_attempts=3)

    def test_bounded_with_max_attempts_is_valid(self) -> None:
        policy = RetryPolicy(
            span=_span(), bound=RetryBound.BOUNDED, source="tenacity", max_attempts=3
        )
        assert policy.max_attempts == 3

    def test_unbounded_is_first_class(self) -> None:
        policy = RetryPolicy(span=_span(), bound=RetryBound.UNBOUNDED, source="tenacity")
        assert policy.bound is RetryBound.UNBOUNDED
        assert policy.max_attempts is None

    def test_unknown_is_first_class_and_distinct_from_unbounded(self) -> None:
        policy = RetryPolicy(span=_span(), bound=RetryBound.UNKNOWN, source="unknown")
        assert policy.bound is not RetryBound.UNBOUNDED
        assert policy.bound is RetryBound.UNKNOWN


class TestTimeoutPolicy:
    def test_absent_timeout(self) -> None:
        t = TimeoutPolicy(span=_span(), present=False)
        assert t.present is False
        assert t.seconds is None

    def test_present_but_not_statically_known(self) -> None:
        # e.g. `timeout=some_variable` — present, but we can't tell what it evaluates to.
        t = TimeoutPolicy(span=_span(), present=True, seconds=None)
        assert t.present is True
        assert t.seconds is None

    def test_present_with_literal_value(self) -> None:
        t = TimeoutPolicy(span=_span(), present=True, seconds=30.0)
        assert t.seconds == 30.0


class TestToolCall:
    def test_call_with_no_timeout_evidence_looked_for(self) -> None:
        call = ToolCall(span=_span(), callee="requests.post")
        assert call.timeout is None

    def test_call_with_timeout_evidence(self) -> None:
        call = ToolCall(
            span=_span(), callee="requests.post", timeout=TimeoutPolicy(span=_span(), present=False)
        )
        assert call.timeout is not None
        assert call.timeout.present is False


class TestAgent:
    def test_bounded_agent_requires_no_source(self) -> None:
        agent = Agent(span=_span(), name="order_agent", has_step_bound=False)
        assert agent.step_bound_source is None

    def test_agent_with_step_bound_and_source(self) -> None:
        agent = Agent(
            span=_span(), name="order_agent", has_step_bound=True, step_bound_source="for-range"
        )
        assert agent.has_step_bound is True
        assert agent.step_bound_source == "for-range"

    def test_step_bound_source_without_bound_is_invalid(self) -> None:
        with pytest.raises(ValueError, match="step_bound_source"):
            Agent(
                span=_span(),
                name="order_agent",
                has_step_bound=False,
                step_bound_source="for-range",
            )

    def test_anonymous_agent(self) -> None:
        agent = Agent(span=_span(), name=None, has_step_bound=False)
        assert agent.name is None


class TestIRFragment:
    def test_empty_fragment_defaults(self) -> None:
        fragment = IRFragment(file="a.py")
        assert fragment.agents == ()
        assert fragment.tool_calls == ()
        assert fragment.retry_policies == ()
        assert fragment.diagnostics == ()

    def test_fragment_with_content(self) -> None:
        agent = Agent(span=_span(), name=None, has_step_bound=False)
        diag = Diagnostic(level=DiagnosticLevel.WARNING, message="hit node cap", file="a.py")
        fragment = IRFragment(file="a.py", agents=(agent,), diagnostics=(diag,))
        assert fragment.agents == (agent,)
        assert fragment.diagnostics[0].level is DiagnosticLevel.WARNING
