"""JSON round-trip serialization for ``Finding``.

This is the internal serialization used by tests (and, from E06 onward, the ``--format json``
CLI reporter) to prove the finding model is a stable, JSON-safe data shape. The dict shape
produced here is validated in tests against ``docs/schemas/finding-v1.json`` — the published
subset schema. Fields are added to both the model and the schema together; existing fields are
never renamed (see ``PLAN.md`` section 13).
"""

from __future__ import annotations

from typing import Any

from agent_reliability.core.model.finding import Finding
from agent_reliability.core.model.span import SourceSpan


def _span_to_dict(span: SourceSpan) -> dict[str, Any]:
    return {
        "file": span.file,
        "start_line": span.start_line,
        "start_col": span.start_col,
        "end_line": span.end_line,
        "end_col": span.end_col,
    }


def finding_to_dict(finding: Finding) -> dict[str, Any]:
    """Serialize a ``Finding`` to a plain, JSON-safe ``dict``."""
    return {
        "rule_id": finding.rule_id,
        "rule_version": finding.rule_version,
        "title": finding.title,
        "description": finding.description,
        "severity": finding.severity.value,
        "confidence": finding.confidence.value,
        "category": finding.category.value,
        "framework": finding.framework,
        "span": _span_to_dict(finding.span),
        "additional_spans": [_span_to_dict(s) for s in finding.additional_spans],
        "evidence": finding.evidence,
        "why_it_matters": finding.why_it_matters,
        "remediation": finding.remediation,
        "references": list(finding.references),
        "fingerprint": finding.fingerprint,
        "finding_id": finding.finding_id,
    }
