"""``run_scan``: ties the frontend scan, rule evaluation, and diagnostics together.

This is deliberately minimal — the full rule engine "batteries" from ``PLAN.md`` section 13
(dedupe/merge, severity overrides, suppression matching, baseline classification) are explicitly
deferred (see ``EXECUTION.md`` E04 non-goals: "more rules", "explain", "suppressions",
"baselines" all land later). What exists here is exactly enough to make ``agent-lint scan``
real: discover and lower files, run every registered rule against every file's IR, and report
findings plus diagnostics honestly.
"""

from __future__ import annotations

from pathlib import Path

from agent_reliability.core.contracts import RuleContext
from agent_reliability.core.model.config import Config
from agent_reliability.core.model.finding import Finding
from agent_reliability.core.model.ir import Diagnostic
from agent_reliability.lint.frontend import scan_repository
from agent_reliability.lint.frontend.scan import SCAN_LEVEL_FILE
from agent_reliability.lint.rules import ALL_RULES


def run_scan(root: Path, *, config: Config) -> tuple[list[Finding], list[Diagnostic]]:
    """Discover, lower, and evaluate every rule against every file under ``root``.

    Returns ``(findings, diagnostics)`` — diagnostics include both scan-level notes (config
    warnings, whole-scan truncation) and per-file notes (parse failures, resource-limit skips),
    collected from every ``IRFragment`` the scan produced.
    """
    fragments = scan_repository(root, config=config)

    findings: list[Finding] = []
    diagnostics: list[Diagnostic] = []

    for fragment in fragments:
        diagnostics.extend(fragment.diagnostics)
        if fragment.file == SCAN_LEVEL_FILE:
            continue

        ctx = RuleContext(_fragment=fragment, _config=config)
        for rule in ALL_RULES:
            findings.extend(rule.evaluate(ctx))

    return findings, diagnostics
