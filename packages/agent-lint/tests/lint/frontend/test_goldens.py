"""Golden-file tests: every fixture under ``fixtures/frontends/`` lowers to its pinned
``.expected.json`` shape. This is the frontend's equivalent of the rule-fixture harness that
lands in E04 — it pins the recognition heuristics documented in ``loops.py``, ``calls.py``, and
``retries.py`` so a future change to those heuristics is a visible, reviewed diff, not a silent
behavior change.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_reliability.lint.frontend.python_frontend import PythonFrontend

from .golden_utils import fragment_to_golden

FRONTENDS_FIXTURES_ROOT = Path(__file__).resolve().parents[5] / "fixtures" / "frontends"


def _collect_cases() -> list[Path]:
    return sorted(FRONTENDS_FIXTURES_ROOT.rglob("*.py"))


CASES = _collect_cases()


def _case_id(path: Path) -> str:
    return path.relative_to(FRONTENDS_FIXTURES_ROOT).as_posix()


@pytest.mark.parametrize("fixture_path", CASES, ids=_case_id)
def test_fixture_matches_golden(fixture_path: Path) -> None:
    golden_path = fixture_path.with_suffix(".expected.json")
    assert golden_path.is_file(), f"missing golden file for {fixture_path}: {golden_path}"

    frontend = PythonFrontend()
    fragment = frontend.lower(fixture_path, root=FRONTENDS_FIXTURES_ROOT)
    actual = fragment_to_golden(fragment)
    expected = json.loads(golden_path.read_text(encoding="utf-8"))

    assert actual == expected


def test_fixture_corpus_is_not_empty() -> None:
    # Guards against a refactor accidentally pointing FRONTENDS_FIXTURES_ROOT at an empty
    # directory and every parametrized case silently vanishing.
    assert len(CASES) >= 15


def test_every_fixture_has_a_golden_file() -> None:
    orphans = [p for p in CASES if not p.with_suffix(".expected.json").is_file()]
    assert orphans == [], f"fixtures missing golden files: {orphans}"
