from __future__ import annotations

import json

import pytest

from agent_reliability.core.model import (
    Category,
    Confidence,
    Finding,
    Severity,
    SourceSpan,
    cap_evidence,
    compute_fingerprint,
    derive_finding_id,
)
from agent_reliability.core.model.finding import MAX_EVIDENCE_LENGTH
from agent_reliability.core.model.serialize import finding_to_dict


def _span() -> SourceSpan:
    return SourceSpan(file="agent/loop.py", start_line=10, start_col=0, end_line=12, end_col=4)


def _finding(**overrides: object) -> Finding:
    fingerprint = compute_fingerprint(
        rule_id="AR001",
        rule_major_version=1,
        normalized_path="agent/loop.py",
        structural_hash="shape",
    )
    defaults: dict[str, object] = dict(
        rule_id="AR001",
        rule_version=1,
        title="Agent loop has no maximum step count",
        description="This loop drives repeated tool calls with no visible bound.",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        category=Category.LOOP_SAFETY,
        span=_span(),
        evidence="while True:",
        why_it_matters="Unbounded loops can run indefinitely and burn API budget.",
        remediation="Add a step counter or a framework-level recursion limit.",
        fingerprint=fingerprint,
        finding_id=derive_finding_id(fingerprint),
    )
    defaults.update(overrides)
    return Finding(**defaults)  # type: ignore[arg-type]


def test_construct_minimal_finding() -> None:
    finding = _finding()
    assert finding.rule_id == "AR001"
    assert finding.framework is None
    assert finding.additional_spans == ()
    assert finding.references == ()


def test_finding_is_frozen() -> None:
    finding = _finding()
    with pytest.raises(AttributeError):
        finding.title = "changed"  # type: ignore[misc]


def test_rejects_empty_rule_id() -> None:
    with pytest.raises(ValueError, match="rule_id"):
        _finding(rule_id="")


def test_rejects_zero_rule_version() -> None:
    with pytest.raises(ValueError, match="rule_version"):
        _finding(rule_version=0)


def test_evidence_is_capped_at_construction() -> None:
    huge_evidence = "x" * 10_000
    finding = _finding(evidence=huge_evidence)
    assert len(finding.evidence) <= MAX_EVIDENCE_LENGTH
    assert finding.evidence.endswith("[truncated]")


def test_cap_evidence_leaves_short_text_untouched() -> None:
    assert cap_evidence("short") == "short"


def test_cap_evidence_truncates_long_text() -> None:
    capped = cap_evidence("x" * 10_000)
    assert len(capped) == MAX_EVIDENCE_LENGTH


def test_derive_finding_id_is_deterministic_from_fingerprint() -> None:
    fp = compute_fingerprint(
        rule_id="AR001", rule_major_version=1, normalized_path="a.py", structural_hash="h"
    )
    assert derive_finding_id(fp) == derive_finding_id(fp)
    assert derive_finding_id(fp).endswith(fp)


class TestJSONRoundTrip:
    def test_serializes_to_json_safe_dict(self) -> None:
        finding = _finding()
        data = finding_to_dict(finding)
        # json.dumps must not raise — proves every value is JSON-safe (no enums, no dataclasses
        # leaking through).
        text = json.dumps(data)
        round_tripped = json.loads(text)
        assert round_tripped["rule_id"] == "AR001"
        assert round_tripped["severity"] == "high"
        assert round_tripped["confidence"] == "high"
        assert round_tripped["category"] == "loop-safety"
        assert round_tripped["span"]["file"] == "agent/loop.py"

    def test_validates_against_published_schema(self, validate_finding_dict) -> None:  # type: ignore[no-untyped-def]
        finding = _finding()
        validate_finding_dict(finding_to_dict(finding))

    def test_finding_with_additional_spans_and_references_validates(
        self,
        validate_finding_dict,  # type: ignore[no-untyped-def]
    ) -> None:
        finding = _finding(
            framework="langgraph",
            additional_spans=(
                SourceSpan(file="agent/tools.py", start_line=1, start_col=0, end_line=1, end_col=1),
            ),
            references=("https://example.invalid/docs/AR001",),
        )
        validate_finding_dict(finding_to_dict(finding))
