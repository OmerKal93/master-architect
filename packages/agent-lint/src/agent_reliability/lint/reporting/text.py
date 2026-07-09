"""The text reporter: human-readable ``agent-lint scan`` output.

This is not yet the append-only, versioned output contract that JSON/SARIF will be (those land
in E06 with a published schema) — the exact wording of text output may still change. What is
fixed from this PR onward is the CLI's exit-code contract (``agent_reliability.lint.cli``), not
this rendering.
"""

from __future__ import annotations

from agent_reliability.core.model.finding import Finding
from agent_reliability.core.model.ir import Diagnostic, DiagnosticLevel

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def render_text(findings: list[Finding], diagnostics: list[Diagnostic]) -> str:
    """Render findings and diagnostics as human-readable text."""
    lines: list[str] = []

    ordered_findings = sorted(
        findings,
        key=lambda f: (_SEVERITY_ORDER.get(f.severity.value, 99), f.span.file, f.span.start_line),
    )

    if not ordered_findings:
        lines.append("No findings.")
    else:
        for finding in ordered_findings:
            lines.append(
                f"[{finding.severity.value.upper()}] {finding.rule_id} "
                f"{finding.span.file}:{finding.span.start_line}"
            )
            lines.append(f"  {finding.title}")
            lines.append(f"  evidence: {finding.evidence}")
            lines.append(f"  why: {finding.why_it_matters}")
            lines.append(f"  fix:  {finding.remediation}")
            lines.append("")
        noun = "finding" if len(ordered_findings) == 1 else "findings"
        lines.append(f"{len(ordered_findings)} {noun}.")

    reportable = [d for d in diagnostics if d.level is not DiagnosticLevel.INFO]
    if reportable:
        lines.append("")
        noun = "diagnostic" if len(reportable) == 1 else "diagnostics"
        lines.append(f"{len(reportable)} {noun}:")
        for diagnostic in reportable:
            location = f" ({diagnostic.file})" if diagnostic.file else ""
            lines.append(f"  [{diagnostic.level.value}] {diagnostic.message}{location}")

    return "\n".join(lines)
