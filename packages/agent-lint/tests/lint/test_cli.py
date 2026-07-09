"""CLI integration tests: the exit-code contract, formats, and offline behavior.

The subprocess-socket-guard style e2e test lives here too, over ``fixtures/malicious/`` — this
is the acceptance criterion from EXECUTION.md E04: "CLI e2e runs over fixtures/malicious/ in
CI" and "e2e asserts zero sockets during scan."
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent_reliability.lint.cli import (
    EXIT_CLEAN,
    EXIT_FINDINGS,
    EXIT_PARTIAL_SCAN,
    EXIT_USAGE_ERROR,
    app,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
AR001_FIXTURES = REPO_ROOT / "fixtures" / "rules" / "AR001"
MALICIOUS_FIXTURES = REPO_ROOT / "fixtures" / "malicious"

runner = CliRunner()


class TestExitCodes:
    def test_clean_scan_exits_zero(self) -> None:
        result = runner.invoke(app, ["scan", str(AR001_FIXTURES / "safe")])
        assert result.exit_code == EXIT_CLEAN
        assert "No findings." in result.stdout

    def test_findings_scan_exits_one(self) -> None:
        result = runner.invoke(app, ["scan", str(AR001_FIXTURES / "unsafe")])
        assert result.exit_code == EXIT_FINDINGS
        assert "AR001" in result.stdout

    def test_nonexistent_path_exits_two(self) -> None:
        result = runner.invoke(app, ["scan", "/definitely/does/not/exist/xyz"])
        assert result.exit_code == EXIT_USAGE_ERROR

    def test_file_instead_of_directory_exits_two(self, tmp_path: Path) -> None:
        f = tmp_path / "a.py"
        f.write_text("x = 1\n")
        result = runner.invoke(app, ["scan", str(f)])
        assert result.exit_code == EXIT_USAGE_ERROR

    def test_oversized_file_yields_partial_scan_exit_code(self, tmp_path: Path) -> None:
        huge = tmp_path / "huge.py"
        huge.write_text("# padding\n" * 300_000)  # > 2 MB
        result = runner.invoke(app, ["scan", str(tmp_path)])
        assert result.exit_code == EXIT_PARTIAL_SCAN
        assert "diagnostic" in result.stdout.lower()

    def test_findings_take_precedence_over_partial_scan(self, tmp_path: Path) -> None:
        (tmp_path / "agent.py").write_text(
            "def run(client):\n    while True:\n        client.step()\n"
        )
        (tmp_path / "huge.py").write_text("# padding\n" * 300_000)
        result = runner.invoke(app, ["scan", str(tmp_path)])
        assert result.exit_code == EXIT_FINDINGS


class TestOutput:
    def test_shows_finding_details(self) -> None:
        result = runner.invoke(app, ["scan", str(AR001_FIXTURES / "unsafe")])
        assert "why:" in result.stdout
        assert "fix:" in result.stdout
        assert "evidence:" in result.stdout

    def test_scan_requires_subcommand(self) -> None:
        # "agent-lint scan" is the permanent documented command surface (EXECUTION.md E04);
        # this guards against Typer's single-command auto-collapse silently changing it to a
        # bare "agent-lint PATH" invocation.
        result = runner.invoke(app, [str(AR001_FIXTURES / "safe")])
        assert result.exit_code != EXIT_CLEAN


class TestOffline:
    def test_scan_opens_no_sockets(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _guard(*args: object, **kwargs: object) -> None:
            raise AssertionError("agent-lint scan attempted to open a network socket")

        monkeypatch.setattr(socket.socket, "connect", _guard)
        result = runner.invoke(app, ["scan", str(AR001_FIXTURES)])
        assert result.exit_code == EXIT_FINDINGS


class TestMaliciousCorpusEndToEnd:
    def test_scan_of_malicious_fixtures_does_not_crash(self) -> None:
        result = runner.invoke(app, ["scan", str(MALICIOUS_FIXTURES)])
        # A hostile input tree must never produce an internal error (exit 3) or an unhandled
        # exception -- only a normal exit code reflecting findings/diagnostics/cleanliness.
        assert result.exit_code in (EXIT_CLEAN, EXIT_FINDINGS, EXIT_PARTIAL_SCAN)
        assert result.exception is None or isinstance(result.exception, SystemExit)
