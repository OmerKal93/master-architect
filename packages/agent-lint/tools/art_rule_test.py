"""``art-rule-test``: the rule fixture harness (``EXECUTION.md`` E04).

For every rule directory's fixtures under the repo-root ``fixtures/rules/<RULE_ID>/``, this
harness verifies two things:

1. **Exact expected output.** Every fixture file's actual findings (from *its own* rule) match
   the corresponding entry in that rule directory's ``expected.json`` exactly (by rule id,
   severity, confidence, category, and count).
2. **The cross-rule false-positive net.** *Every* registered rule is run against *every*
   fixture file whose expected finding count is zero (i.e. every safe/edge control across the
   whole fixture corpus, not just the owning rule's own fixtures) — no rule may fire on any
   safe control anywhere. With only AR001 registered today this is trivially satisfied; the
   check is written to hold as more rules land in later PRs without needing to change.

Runnable two ways:

- ``python tools/art_rule_test.py`` — a standalone contributor-facing check with a clear
  pass/fail summary and a non-zero exit code on failure.
- ``tests/test_rule_fixtures.py`` imports ``check_all_rule_fixtures()`` directly as a pytest
  test, so the same harness gates CI.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from agent_reliability.core.contracts import RuleContext
from agent_reliability.core.model.config import default_config
from agent_reliability.core.model.finding import Finding
from agent_reliability.lint.frontend.python_frontend import PythonFrontend
from agent_reliability.lint.frontend.ts_js_frontend import TsJsFrontend
from agent_reliability.lint.rules import ALL_RULES

# Frontend selection mirrors scan.py's own `next(fe for fe in frontends if fe.supports(path))`
# pattern -- the fixture harness must exercise the SAME frontend a real scan would pick for a
# given fixture file's extension, not just PythonFrontend, now that TS/JS fixtures exist too.
_FIXTURE_FRONTENDS = (PythonFrontend(), TsJsFrontend())

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_RULES_ROOT = REPO_ROOT / "fixtures" / "rules"


@dataclass(frozen=True)
class RuleFixtureCase:
    rule_id: str
    relative_fixture_path: str
    fixture_file: Path
    fixture_root: Path
    expected: list[dict[str, str]]


@dataclass(frozen=True)
class HarnessFailure:
    case: RuleFixtureCase
    message: str


def discover_rule_dirs() -> list[Path]:
    if not FIXTURES_RULES_ROOT.is_dir():
        return []
    return sorted(p for p in FIXTURES_RULES_ROOT.iterdir() if p.is_dir())


def _load_expected(rule_dir: Path) -> dict[str, list[dict[str, str]]]:
    expected_path = rule_dir / "expected.json"
    if not expected_path.is_file():
        raise FileNotFoundError(f"missing expected.json for rule fixtures: {rule_dir}")
    data: dict[str, list[dict[str, str]]] = json.loads(expected_path.read_text(encoding="utf-8"))
    return data


def collect_cases() -> list[RuleFixtureCase]:
    cases: list[RuleFixtureCase] = []
    for rule_dir in discover_rule_dirs():
        rule_id = rule_dir.name
        expected = _load_expected(rule_dir)
        for relative_path, expected_findings in sorted(expected.items()):
            fixture_file = rule_dir / relative_path
            if not fixture_file.is_file():
                raise FileNotFoundError(
                    f"expected.json references a missing fixture: {rule_dir}/{relative_path}"
                )
            cases.append(
                RuleFixtureCase(
                    rule_id=rule_id,
                    relative_fixture_path=relative_path,
                    fixture_file=fixture_file,
                    fixture_root=rule_dir,
                    expected=expected_findings,
                )
            )
    return cases


def _project_finding(finding: Finding) -> dict[str, str]:
    return {
        "rule_id": finding.rule_id,
        "severity": finding.severity.value,
        "confidence": finding.confidence.value,
        "category": finding.category.value,
    }


def _findings_for_file(fixture_file: Path, *, root: Path) -> list[dict[str, str]]:
    """Lower ``fixture_file`` and run every registered rule against it (the cross-rule net)."""
    frontend = next((fe for fe in _FIXTURE_FRONTENDS if fe.supports(fixture_file)), None)
    if frontend is None:
        raise ValueError(f"no frontend supports fixture file: {fixture_file}")
    fragment = frontend.lower(fixture_file, root=root)
    ctx = RuleContext(_fragment=fragment, _config=default_config())

    findings: list[Finding] = []
    for rule in ALL_RULES:
        findings.extend(rule.evaluate(ctx))

    return [_project_finding(f) for f in findings]


def check_all_rule_fixtures() -> list[HarnessFailure]:
    """Run the full harness. Returns a list of failures (empty means everything passed)."""
    failures: list[HarnessFailure] = []

    for case in collect_cases():
        actual = _findings_for_file(case.fixture_file, root=case.fixture_root)
        expected_sorted = sorted(case.expected, key=lambda d: tuple(d.items()))
        actual_sorted = sorted(actual, key=lambda d: tuple(d.items()))

        if actual_sorted != expected_sorted:
            failures.append(
                HarnessFailure(
                    case=case,
                    message=(
                        f"{case.rule_id}/{case.relative_fixture_path}: "
                        f"expected {expected_sorted}, got {actual_sorted}"
                    ),
                )
            )

        # Cross-rule false-positive net: fixtures with zero expected findings must produce
        # zero findings from EVERY registered rule, not just the owning rule.
        if not case.expected and actual:
            failures.append(
                HarnessFailure(
                    case=case,
                    message=(
                        f"cross-rule FP net violated: {case.rule_id}/"
                        f"{case.relative_fixture_path} is a safe/edge control (expected no "
                        f"findings from any rule) but got {actual_sorted}"
                    ),
                )
            )

    return failures


def main() -> int:
    cases = collect_cases()
    failures = check_all_rule_fixtures()

    if failures:
        print(f"FAILED: {len(failures)} of {len(cases)} fixture case(s)", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure.message}", file=sys.stderr)
        return 1

    print(f"OK: {len(cases)} fixture case(s) across {len(discover_rule_dirs())} rule(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
