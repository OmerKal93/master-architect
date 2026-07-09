"""Consumes ``fixtures/malicious/`` — the T1/T2/T4/T13 hostile-input corpus.

Every case here must produce a graceful diagnostic, never an unhandled exception and never a
hang. This is the acceptance-criteria test for E03 (EXECUTION.md): "full malicious suite green
on 3 OSes... scans of pathological fixtures terminate within budget with scan-limit
diagnostics."
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from agent_reliability.lint.frontend.limits import SCAN_LIMIT_PREFIX
from agent_reliability.lint.frontend.python_frontend import PythonFrontend
from agent_reliability.lint.frontend.scan import scan_repository

MALICIOUS_FIXTURES_ROOT = Path(__file__).resolve().parents[5] / "fixtures" / "malicious"


@pytest.fixture(scope="module", autouse=True)
def _ensure_fixtures_exist() -> None:
    assert MALICIOUS_FIXTURES_ROOT.is_dir(), (
        f"expected malicious fixture corpus at {MALICIOUS_FIXTURES_ROOT}"
    )


class TestDeepNesting:
    """T2: pathological code (deeply nested expressions)."""

    def test_does_not_crash_or_hang(self) -> None:
        f = MALICIOUS_FIXTURES_ROOT / "deep_nesting.py"
        assert f.is_file()

        start = time.monotonic()
        fragment = PythonFrontend().lower(f, root=MALICIOUS_FIXTURES_ROOT)
        elapsed = time.monotonic() - start

        assert elapsed < 10.0, "deeply nested input must not hang the scan"
        # CPython's own parser rejects extreme nesting before we ever see a tree; either way,
        # the frontend must report a diagnostic rather than raising, and it must be
        # categorized as a resource-limit rejection, not an ordinary parse-error typo.
        assert len(fragment.diagnostics) == 1
        assert fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)
        assert fragment.agents == ()


class TestHugeFile:
    """T2/T25: DoS via oversized input."""

    def test_is_skipped_via_size_cap(self) -> None:
        f = MALICIOUS_FIXTURES_ROOT / "huge_file.py"
        assert f.is_file()
        assert f.stat().st_size > 2 * 1024 * 1024

        start = time.monotonic()
        fragment = PythonFrontend().lower(f, root=MALICIOUS_FIXTURES_ROOT)
        elapsed = time.monotonic() - start

        assert elapsed < 2.0, "the size cap must reject the file before ever reading it"
        assert len(fragment.diagnostics) == 1
        assert fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)


class TestHostileFilenames:
    """T13: malicious/unusual filenames must not crash discovery or lowering."""

    def test_all_hostile_filenames_are_handled(self) -> None:
        root = MALICIOUS_FIXTURES_ROOT / "hostile_filenames"
        assert root.is_dir()
        assert len(list(root.glob("*.py"))) >= 4

        fragments = scan_repository(root)

        assert len(fragments) >= 4
        for fragment in fragments:
            assert fragment.diagnostics == () or all(
                d.file is not None or d.message for d in fragment.diagnostics
            )


class TestSymlinkEscape:
    """T4: symlink escape must never be read."""

    def test_escaped_content_never_appears_in_scan_results(self) -> None:
        scan_root = MALICIOUS_FIXTURES_ROOT / "symlink_escape" / "scan_root"
        assert scan_root.is_dir()

        fragments = scan_repository(scan_root)

        files = {f.file for f in fragments if f.file}
        assert "escape.py" not in files
        assert "normal.py" in files


class TestWholeMaliciousCorpus:
    """The combined stress test: scan the entire hostile-input directory at once."""

    def test_full_corpus_scan_completes_without_crashing(self) -> None:
        start = time.monotonic()
        fragments = scan_repository(MALICIOUS_FIXTURES_ROOT)
        elapsed = time.monotonic() - start

        assert elapsed < 30.0
        # At minimum, the ordinary safe files nested inside the corpus (e.g.
        # symlink_escape/scan_root/normal.py) must still be found and scanned normally --
        # hostility elsewhere in the tree must not prevent legitimate files from being scanned.
        files = {f.file for f in fragments if f.file}
        assert any(f.endswith("normal.py") for f in files)
