from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import agent_reliability.lint.frontend.scan as scan_module
from agent_reliability.core.model.config import default_config, parse_config
from agent_reliability.lint.frontend.limits import SCAN_LIMIT_PREFIX, ScanLimits
from agent_reliability.lint.frontend.scan import SCAN_LEVEL_FILE, scan_repository


def test_scans_all_python_files(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "b.py").write_text("y = 2\n")
    (tmp_path / "c.txt").write_text("not python\n")

    fragments = scan_repository(tmp_path)

    files = {f.file for f in fragments}
    assert files == {"a.py", "b.py"}


def test_empty_repository_returns_no_fragments(tmp_path: Path) -> None:
    assert scan_repository(tmp_path) == ()


def test_config_diagnostics_surface_at_scan_level(tmp_path: Path) -> None:
    (tmp_path / ".agent-reliability.yaml").write_text("exclude: []\negress: allow\n")
    (tmp_path / "a.py").write_text("x = 1\n")

    config = parse_config((tmp_path / ".agent-reliability.yaml").read_text())
    fragments = scan_repository(tmp_path, config=config)

    scan_level = [f for f in fragments if f.file == SCAN_LEVEL_FILE]
    assert len(scan_level) == 1
    assert any("egress" in d.message for d in scan_level[0].diagnostics)


def test_wall_clock_budget_truncates_scan(tmp_path: Path, monkeypatch) -> None:
    for i in range(5):
        (tmp_path / f"f{i}.py").write_text("x = 1\n")

    # Force the wall-clock check to look exceeded from the very first file.
    monkeypatch.setattr(scan_module.time, "monotonic", Mock(side_effect=[0.0, 100.0, 100.0, 100.0]))

    fragments = scan_repository(tmp_path, limits=ScanLimits(wall_clock_budget_seconds=1.0))

    scan_level = [f for f in fragments if f.file == SCAN_LEVEL_FILE]
    assert len(scan_level) == 1
    assert any(
        d.message.startswith(SCAN_LIMIT_PREFIX) and "whole-scan" in d.message
        for d in scan_level[0].diagnostics
    )
    # At most the files processed before truncation were lowered; the scan did not hang or
    # crash, and it reported the truncation honestly rather than silently returning early.
    non_scan_level_fragments = [f for f in fragments if f.file != SCAN_LEVEL_FILE]
    assert len(non_scan_level_fragments) < 5


def test_uses_default_config_when_none_given(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    fragments = scan_repository(tmp_path, config=None)
    assert {f.file for f in fragments} == {"a.py"}
    assert fragments == scan_repository(tmp_path, config=default_config())
