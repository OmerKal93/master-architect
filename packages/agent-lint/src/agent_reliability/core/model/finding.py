"""The finding model.

Field shapes here are the permanent, final-shaped subset of the complete schema in ``PLAN.md``
section 11 — this PR (E02) instantiates only what the first rules (E04+) need. New fields are
added as later PRs need them (suppression tracking, baseline status, auto-fix, dataflow paths);
existing fields are never renamed, so nothing built on this model is thrown away.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_reliability.core.model.severity import Category, Confidence, Severity
from agent_reliability.core.model.span import SourceSpan

# Evidence is a redacted excerpt shown to explain a finding, not the full matched source — it
# is length-capped at construction time so a pathological input (a megabyte-long literal) can
# never make its way into a report. See PLAN.md threat T2/T25.
MAX_EVIDENCE_LENGTH = 400
_TRUNCATION_SUFFIX = "… [truncated]"


def cap_evidence(text: str) -> str:
    """Truncate ``text`` to ``MAX_EVIDENCE_LENGTH``, appending a visible truncation marker."""
    if len(text) <= MAX_EVIDENCE_LENGTH:
        return text
    keep = MAX_EVIDENCE_LENGTH - len(_TRUNCATION_SUFFIX)
    return text[:keep] + _TRUNCATION_SUFFIX


def derive_finding_id(fingerprint: str) -> str:
    """Derive a Finding's own stable identity from its baseline-matching fingerprint.

    The two are allowed to diverge in the future (e.g. once duplicate-finding merging exists —
    see ``PLAN.md`` section 13 — a merged finding could have one ``finding_id`` but represent
    evidence from more than one fingerprint); today they are a direct 1:1 derivation.
    """
    return f"finding:{fingerprint}"


@dataclass(frozen=True, slots=True)
class Finding:
    """A single, deterministic result from running one rule against one file.

    ``fingerprint`` is the baseline/suppression matching key (see
    ``agent_reliability.core.model.fingerprint``); ``finding_id`` is this finding instance's own
    stable identity, derived from the fingerprint. They are allowed to diverge in the future
    (e.g. if two rules can legitimately produce the "same" fingerprint via merging — see
    ``PLAN.md`` section 13, "duplicate merging" — a feature not yet implemented in this PR).
    """

    rule_id: str
    rule_version: int
    title: str
    description: str
    severity: Severity
    confidence: Confidence
    category: Category
    span: SourceSpan
    evidence: str
    why_it_matters: str
    remediation: str
    fingerprint: str
    finding_id: str
    framework: str | None = None
    additional_spans: tuple[SourceSpan, ...] = field(default_factory=tuple)
    references: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if len(self.evidence) > MAX_EVIDENCE_LENGTH:
            object.__setattr__(self, "evidence", cap_evidence(self.evidence))
        if not self.rule_id:
            raise ValueError("Finding.rule_id must not be empty")
        if self.rule_version < 1:
            raise ValueError(f"Finding.rule_version must be >= 1, got {self.rule_version}")
