"""The micro-IR: only the entities the first rules need.

These are the same types described in the complete intermediate representation in ``PLAN.md``
section 11 — this is not a simplified stand-in that gets rewritten later, it is the first,
smallest instantiation of that IR. New entity types (``Workflow``, ``Node``, ``Edge``,
``SideEffect``, ``ApprovalGate``, ``Checkpoint``, ...) are added only when a real rule needs
them (see ``EXECUTION.md``, "Evolution seam" on each E-PR) — there is no speculative type
inventory here.

``UNKNOWN``-shaped values are first-class throughout: static analysis frequently cannot prove a
negative (e.g. "this loop has no bound"), and the IR represents "we don't know" distinctly from
"we know it's absent" so that rules can calibrate confidence honestly instead of guessing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_reliability.core.model.span import SourceSpan


class RetryBound(str, Enum):
    """What static analysis could determine about a retry construct's upper bound."""

    UNKNOWN = "unknown"
    """A retry construct exists but its bound could not be statically determined."""

    UNBOUNDED = "unbounded"
    """Provably no upper bound (e.g. ``stop=None``, a ``while True`` retry loop)."""

    BOUNDED = "bounded"
    """A literal, finite upper bound was found (see ``RetryPolicy.max_attempts``)."""


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """A retry construct: a decorator, wrapper, or loop that re-attempts an action on failure."""

    span: SourceSpan
    bound: RetryBound
    source: str
    """Evidence provenance, e.g. ``"tenacity"``, ``"stamina"``, ``"manual-loop"``."""
    structural_hash: str
    """A hash of this construct's shape, excluding source positions — computed by the frontend
    at lowering time (e.g. ``agent_reliability.lint.frontend.ast_utils.structural_hash``) from
    the AST node this entity was derived from. This is what lets rules compute stable ``fp_v1``
    fingerprints (``agent_reliability.core.model.fingerprint``) without needing raw AST access
    themselves — the frontend is the only place that ever touches the AST."""
    max_attempts: int | None = None
    """Set only when ``bound is RetryBound.BOUNDED``."""

    def __post_init__(self) -> None:
        if self.bound is RetryBound.BOUNDED and self.max_attempts is None:
            raise ValueError("RetryPolicy with bound=BOUNDED must set max_attempts")
        if self.bound is not RetryBound.BOUNDED and self.max_attempts is not None:
            raise ValueError("RetryPolicy.max_attempts is only meaningful when bound=BOUNDED")


@dataclass(frozen=True, slots=True)
class TimeoutPolicy:
    """What static analysis found about a timeout on a call site."""

    span: SourceSpan
    present: bool
    seconds: float | None = None
    """Set only when a literal timeout value was found; a non-literal timeout (e.g. a variable
    or config lookup) is ``present=True`` with ``seconds=None`` — present but not statically
    known, which is a distinct, weaker form of evidence than an absent timeout."""
    explicit_none: bool = False
    """``True`` only when the timeout keyword's literal value is ``None`` (e.g. ``timeout=None``).
    For ``requests``/``httpx``, an explicit ``None`` disables the timeout entirely — the call is
    exactly as unbounded as if the keyword were never passed, so this is distinct evidence from
    ``present=True, seconds=None`` (timeout present but bound to a variable/config lookup, which
    is potentially a real bound this analysis just can't read statically). AR003 (E05) treats
    ``explicit_none=True`` the same as ``present=False``."""


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A call site that looks like an external/tool/API call (HTTP client, SDK method, ...)."""

    span: SourceSpan
    callee: str
    """Best-effort dotted name of what's being called, e.g. ``"requests.post"``."""
    structural_hash: str
    """See ``RetryPolicy.structural_hash`` — same purpose, computed from this call site's AST
    node by the frontend."""
    timeout: TimeoutPolicy | None = None
    """``None`` means no timeout evidence was even looked for at this call site (distinct from
    ``TimeoutPolicy(present=False)``, which means it *was* checked and found absent)."""


@dataclass(frozen=True, slots=True)
class Agent:
    """An identified agentic loop: a loop construct that drives repeated tool/LLM calls."""

    span: SourceSpan
    name: str | None
    has_step_bound: bool
    """True if a counter, recursion limit, or range bound was statically found constraining the
    loop's iteration count."""
    structural_hash: str
    """See ``RetryPolicy.structural_hash`` — same purpose, computed from this loop's/function's
    AST node by the frontend."""
    step_bound_source: str | None = None
    """Evidence provenance when ``has_step_bound`` is True, e.g. ``"for-range"``,
    ``"counter-check"``, ``"recursion_limit"``."""

    def __post_init__(self) -> None:
        if not self.has_step_bound and self.step_bound_source is not None:
            raise ValueError("Agent.step_bound_source requires has_step_bound=True")


class DiagnosticLevel(str, Enum):
    """Severity of a scan-process diagnostic (distinct from a rule Finding's Severity)."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """A note about the scan process itself: a skipped file, a resource limit hit, an unknown
    config key, an untested framework version. Not a rule finding."""

    level: DiagnosticLevel
    message: str
    file: str | None = None


@dataclass(frozen=True, slots=True)
class IRFragment:
    """Everything a ``Frontend`` produced for one input file."""

    file: str
    agents: tuple[Agent, ...] = ()
    tool_calls: tuple[ToolCall, ...] = ()
    retry_policies: tuple[RetryPolicy, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
