"""The domain model: findings, the micro-IR, and minimal config.

Public names are re-exported here so callers can write
``from agent_reliability.core.model import Finding, Severity`` instead of reaching into
submodules directly. Submodule paths (``agent_reliability.core.model.finding``, etc.) are also
stable and may be imported directly.
"""

from __future__ import annotations

from agent_reliability.core.model.config import (
    Config,
    RulesConfig,
    default_config,
    load_config_for_root,
)
from agent_reliability.core.model.finding import (
    MAX_EVIDENCE_LENGTH,
    Finding,
    cap_evidence,
    derive_finding_id,
)
from agent_reliability.core.model.fingerprint import (
    FINGERPRINT_ALGORITHM_VERSION,
    compute_fingerprint,
)
from agent_reliability.core.model.ir import (
    Agent,
    Diagnostic,
    DiagnosticLevel,
    IRFragment,
    RetryBound,
    RetryPolicy,
    TimeoutPolicy,
    ToolCall,
)
from agent_reliability.core.model.severity import Category, Confidence, Severity
from agent_reliability.core.model.span import SourceSpan

__all__ = [
    "MAX_EVIDENCE_LENGTH",
    "FINGERPRINT_ALGORITHM_VERSION",
    "Agent",
    "Category",
    "Config",
    "Confidence",
    "Diagnostic",
    "DiagnosticLevel",
    "Finding",
    "IRFragment",
    "RetryBound",
    "RetryPolicy",
    "RulesConfig",
    "Severity",
    "SourceSpan",
    "TimeoutPolicy",
    "ToolCall",
    "cap_evidence",
    "compute_fingerprint",
    "default_config",
    "derive_finding_id",
    "load_config_for_root",
]
