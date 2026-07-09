from __future__ import annotations

from agent_reliability.core.model import Category, Confidence, Finding, Severity, SourceSpan
from agent_reliability.core.model.ir import Diagnostic, DiagnosticLevel
from agent_reliability.lint.reporting.text import render_text


def _finding(*, file: str = "a.py", line: int = 1, severity: Severity = Severity.HIGH) -> Finding:
    span = SourceSpan(file=file, start_line=line, start_col=0, end_line=line, end_col=1)
    return Finding(
        rule_id="AR001",
        rule_version=1,
        title="Agent loop has no maximum step count",
        description="desc",
        severity=severity,
        confidence=Confidence.HIGH,
        category=Category.LOOP_SAFETY,
        span=span,
        evidence="while True: ...",
        why_it_matters="why",
        remediation="fix it",
        fingerprint=f"fp_v1:{'0' * 64}",
        finding_id="finding:test",
    )


def test_no_findings_no_diagnostics() -> None:
    output = render_text([], [])
    assert output == "No findings."


def test_single_finding_shows_all_fields() -> None:
    output = render_text([_finding()], [])
    assert "[HIGH] AR001 a.py:1" in output
    assert "Agent loop has no maximum step count" in output
    assert "evidence: while True: ..." in output
    assert "why: why" in output
    assert "fix:  fix it" in output
    assert "1 finding." in output


def test_plural_finding_count() -> None:
    output = render_text([_finding(), _finding(line=2)], [])
    assert "2 findings." in output


def test_findings_sorted_by_severity_then_file_then_line() -> None:
    low = _finding(file="a.py", line=1, severity=Severity.LOW)
    critical = _finding(file="b.py", line=1, severity=Severity.CRITICAL)
    output = render_text([low, critical], [])
    assert output.index("[CRITICAL]") < output.index("[LOW]")


def test_warning_diagnostics_are_shown() -> None:
    diag = Diagnostic(level=DiagnosticLevel.WARNING, message="hit a limit", file="big.py")
    output = render_text([], [diag])
    assert "1 diagnostic:" in output
    assert "[warning] hit a limit (big.py)" in output


def test_info_diagnostics_are_not_shown() -> None:
    diag = Diagnostic(level=DiagnosticLevel.INFO, message="skipped symlink", file="x.py")
    output = render_text([], [diag])
    assert "diagnostic" not in output


def test_plural_diagnostic_count() -> None:
    diags = [
        Diagnostic(level=DiagnosticLevel.WARNING, message="a"),
        Diagnostic(level=DiagnosticLevel.ERROR, message="b"),
    ]
    output = render_text([], diags)
    assert "2 diagnostics:" in output


def test_diagnostic_without_file_omits_location() -> None:
    diag = Diagnostic(level=DiagnosticLevel.WARNING, message="scan-wide note")
    output = render_text([], [diag])
    assert "scan-wide note" in output
    assert "()" not in output
