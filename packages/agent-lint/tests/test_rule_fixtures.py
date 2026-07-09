"""Runs the rule fixture harness (``tools/art_rule_test.py``) as a pytest test, so CI gates on
the same checks a contributor gets from running the harness standalone."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from art_rule_test import check_all_rule_fixtures, collect_cases  # noqa: E402


def test_rule_fixture_corpus_is_not_empty() -> None:
    assert len(collect_cases()) >= 6


def test_all_rule_fixtures_pass_the_harness() -> None:
    failures = check_all_rule_fixtures()
    assert failures == [], "\n".join(f.message for f in failures)
