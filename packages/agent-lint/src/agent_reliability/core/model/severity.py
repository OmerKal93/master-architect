"""Severity, confidence, and category scales.

These are decision models, not arbitrary numerical risk scores (see ``PLAN.md`` section 8:
"Do not use arbitrary numerical risk scores without a clear decision model"). Both enums are
deliberately small and closed — adding a value is an explicit, documented change, not a tuning
knob.
"""

from __future__ import annotations

from enum import Enum


class Severity(str, Enum):
    """How bad it is if the finding represents a real problem.

    - CRITICAL: can cause irreversible external damage (double charge, data deletion, secret
      egress).
    - HIGH: can cause outage, runaway cost, or unbounded behavior.
    - MEDIUM: weakens recovery or auditability without being immediately dangerous.
    - LOW: hygiene.
    - INFO: informational detection notes, not a defect (e.g. "framework version not tested").
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Confidence(str, Enum):
    """How sure the rule is that the pattern it matched is really present and really a problem.

    - HIGH: the pattern is provably present (e.g. a literal, unconditional ``while True``).
    - MEDIUM: the pattern is present, but a safety mechanism could plausibly exist elsewhere
      that static analysis cannot see.
    - LOW: heuristic match (e.g. a function name suggesting a side effect).
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(str, Enum):
    """What kind of reliability/security concern a rule addresses."""

    LOOP_SAFETY = "loop-safety"
    RETRY_SAFETY = "retry-safety"
    SIDE_EFFECTS = "side-effects"
    TIMEOUTS = "timeouts"
    CONTEXT_HYGIENE = "context-hygiene"
    PERMISSIONS = "permissions"
    DATA_EXPOSURE = "data-exposure"
    AUDITABILITY = "auditability"
    CONCURRENCY = "concurrency"
    RECOVERY = "recovery"
