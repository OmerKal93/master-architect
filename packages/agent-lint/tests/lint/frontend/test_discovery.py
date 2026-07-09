from __future__ import annotations

from pathlib import Path

import pytest

from agent_reliability.core.model.config import default_config, parse_config
from agent_reliability.core.model.ir import Diagnostic
from agent_reliability.lint.frontend.discovery import discover_files, to_relative_posix


def _names(root: Path, *, config=None) -> set[str]:  # type: ignore[no-untyped-def]
    diagnostics: list[Diagnostic] = []
    found = discover_files(root, config=config or default_config(), diagnostics=diagnostics)
    return {f.relative_posix_path for f in found}


def test_discovers_plain_files(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("y = 2\n")
    assert _names(tmp_path) == {"a.py", "sub/b.py"}


def test_skips_default_excluded_directories(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    for d in [".git", "__pycache__", ".venv", "node_modules"]:
        (tmp_path / d).mkdir()
        (tmp_path / d / "should_not_appear.py").write_text("x = 1\n")
    assert _names(tmp_path) == {"a.py"}


def test_skips_hidden_directories(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "b.py").write_text("x = 1\n")
    assert _names(tmp_path) == {"a.py"}


class TestSymlinkSafety:
    def test_symlinked_file_is_skipped(self, tmp_path: Path) -> None:
        outside = tmp_path.parent / "outside_target.py"
        outside.write_text("SECRET = 1\n")
        root = tmp_path / "root"
        root.mkdir()
        (root / "normal.py").write_text("x = 1\n")
        (root / "escape.py").symlink_to(outside)

        diagnostics: list[Diagnostic] = []
        found = {
            f.relative_posix_path
            for f in discover_files(root, config=default_config(), diagnostics=diagnostics)
        }
        assert found == {"normal.py"}
        assert any("symlink" in d.message.lower() for d in diagnostics)

    def test_symlinked_directory_is_not_descended_into(self, tmp_path: Path) -> None:
        outside_dir = tmp_path.parent / "outside_dir"
        outside_dir.mkdir()
        (outside_dir / "secret.py").write_text("SECRET = 1\n")
        root = tmp_path / "root"
        root.mkdir()
        (root / "link_to_outside").symlink_to(outside_dir, target_is_directory=True)

        assert _names(root) == set()

    @pytest.mark.skipif(
        __import__("sys").platform == "win32",
        reason="fixture uses a real fixture repo symlink, exercised on POSIX runners in CI",
    )
    def test_repo_symlink_escape_fixture(self) -> None:
        repo_root = Path(__file__).resolve().parents[5]
        scan_root = repo_root / "fixtures" / "malicious" / "symlink_escape" / "scan_root"
        assert scan_root.is_dir(), "expected fixture directory to exist"

        diagnostics: list[Diagnostic] = []
        found = {
            f.relative_posix_path
            for f in discover_files(scan_root, config=default_config(), diagnostics=diagnostics)
        }
        assert found == {"normal.py"}
        assert any("symlink" in d.message.lower() for d in diagnostics)


class TestGitignore:
    def test_respects_gitignore_patterns(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text("vendor/\n*.generated.py\n")
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "a.generated.py").write_text("x = 1\n")
        (tmp_path / "vendor").mkdir()
        (tmp_path / "vendor" / "b.py").write_text("x = 1\n")
        assert _names(tmp_path) == {"a.py"}

    def test_gitignore_negation(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text("*.py\n!keep.py\n")
        (tmp_path / "drop.py").write_text("x = 1\n")
        (tmp_path / "keep.py").write_text("x = 1\n")
        assert _names(tmp_path) == {"keep.py"}


class TestConfigExclude:
    def test_respects_config_exclude(self, tmp_path: Path) -> None:
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "b.generated.py").write_text("x = 1\n")
        config = parse_config("exclude: ['*.generated.py']\n")
        assert _names(tmp_path, config=config) == {"a.py"}


class TestContainment:
    def test_to_relative_posix_normalizes(self, tmp_path: Path) -> None:
        (tmp_path / "sub").mkdir()
        f = tmp_path / "sub" / "a.py"
        f.write_text("x = 1\n")
        assert to_relative_posix(f, root=tmp_path) == "sub/a.py"

    def test_discovered_files_never_escape_root(self, tmp_path: Path) -> None:
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "b.py").write_text("x = 1\n")
        found = list(discover_files(tmp_path, config=default_config(), diagnostics=[]))
        resolved_root = tmp_path.resolve()
        for f in found:
            f.absolute_path.resolve().relative_to(resolved_root)  # raises ValueError if escaped
