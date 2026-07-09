"""Safe file discovery: turning a directory tree into a list of files to scan.

This module is where PLAN.md threats T1 (malicious repository content), T4 (symlink/path
traversal), and part of T25 (DoS from huge repositories) are mitigated:

- Symlinks are never followed, for files or directories (T4). A symlinked file is skipped with
  a diagnostic rather than silently read — it is not resolved and opened.
- Every yielded path is resolved and checked to remain strictly under the scan root (T4,
  defense in depth beyond "don't follow symlinks", covering exotic filesystem cases like
  Windows junctions).
- Common VCS/cache/dependency directories are never descended into by default (bounds T25).
- Nothing here ever imports or executes file contents — this module only touches file *names*
  and *metadata* (``os.walk``, ``Path.stat``, ``Path.is_symlink``), never contents.
"""

from __future__ import annotations

import fnmatch
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from agent_reliability.core.model.config import Config
from agent_reliability.core.model.ir import Diagnostic, DiagnosticLevel
from agent_reliability.lint.frontend.gitignore import GitignoreMatcher
from agent_reliability.lint.frontend.limits import DEFAULT_EXCLUDED_DIR_NAMES


@dataclass(frozen=True, slots=True)
class DiscoveredFile:
    absolute_path: Path
    relative_posix_path: str


def to_relative_posix(path: Path, *, root: Path) -> str:
    """Normalize ``path`` to a repo-relative, POSIX-style string, as ``SourceSpan`` requires."""
    return path.relative_to(root).as_posix()


def _is_contained(path: Path, *, resolved_root: Path) -> bool:
    """True if ``path``, once resolved, is strictly under ``resolved_root``.

    This is the defense-in-depth containment check (T4): even though symlinks are never
    followed by the walk itself, this catches any path that would otherwise escape the root
    (e.g. via unusual filesystem constructs) before it is ever opened.
    """
    try:
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError):
        # RuntimeError: infinite symlink loop. OSError: permission/IO error resolving the path.
        # Either way, we cannot prove containment, so we treat it as not contained.
        return False
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return False
    return True


def _matches_exclude_globs(relative_posix_path: str, *, exclude: tuple[str, ...]) -> bool:
    for pattern in exclude:
        candidate = pattern[:-1] if pattern.endswith("/") else pattern
        if fnmatch.fnmatch(relative_posix_path, candidate):
            return True
        if fnmatch.fnmatch(relative_posix_path, f"{candidate}/*"):
            return True
        # Also match by basename, mirroring gitignore-style unanchored patterns for simple
        # names like "*.generated.py" or "vendor".
        if "/" not in pattern and fnmatch.fnmatch(Path(relative_posix_path).name, candidate):
            return True
    return False


def discover_files(
    root: Path,
    *,
    config: Config,
    diagnostics: list[Diagnostic] | None = None,
) -> Iterator[DiscoveredFile]:
    """Yield every safely-discoverable file under ``root``.

    Symlinked files and directories are skipped (with a diagnostic). Files that fail the
    containment check are skipped (with a diagnostic). Directories in
    ``limits.DEFAULT_EXCLUDED_DIR_NAMES``, hidden directories (except the root itself), and
    anything matching ``.gitignore`` or ``config.exclude`` are never descended into or yielded.

    This function does not open or read any file — it only inspects names and metadata.
    """
    collected_diagnostics = diagnostics if diagnostics is not None else []
    resolved_root = root.resolve(strict=False)

    gitignore_path = root / ".gitignore"
    matcher = GitignoreMatcher.empty()
    if gitignore_path.is_file() and not gitignore_path.is_symlink():
        try:
            matcher = GitignoreMatcher.from_text(gitignore_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            collected_diagnostics.append(
                Diagnostic(
                    level=DiagnosticLevel.WARNING,
                    message="could not read .gitignore; proceeding without it",
                )
            )

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current_dir = Path(dirpath)

        # Prune subdirectories in place so os.walk never descends into them.
        kept_dirnames = []
        for name in dirnames:
            child = current_dir / name
            if name in DEFAULT_EXCLUDED_DIR_NAMES:
                continue
            if name.startswith("."):
                continue
            if child.is_symlink():
                collected_diagnostics.append(
                    Diagnostic(
                        level=DiagnosticLevel.INFO,
                        message="skipped symlinked directory (symlinks are never followed)",
                        file=_safe_relative(child, root=root),
                    )
                )
                continue
            relative = to_relative_posix(child, root=root)
            if matcher.is_ignored(relative, is_dir=True):
                continue
            if _matches_exclude_globs(relative, exclude=config.exclude):
                continue
            kept_dirnames.append(name)
        dirnames[:] = kept_dirnames

        for name in filenames:
            if name.startswith("."):
                # Hidden files (.gitignore, .env, ...) are not scanned by default, mirroring
                # the hidden-directory default above -- consistent with common tooling
                # conventions and keeping config/dotfiles out of scan results unless a future
                # frontend explicitly opts into them.
                continue
            file_path = current_dir / name
            if file_path.is_symlink():
                collected_diagnostics.append(
                    Diagnostic(
                        level=DiagnosticLevel.INFO,
                        message="skipped symlinked file (symlinks are never followed)",
                        file=_safe_relative(file_path, root=root),
                    )
                )
                continue
            if not _is_contained(file_path, resolved_root=resolved_root):
                collected_diagnostics.append(
                    Diagnostic(
                        level=DiagnosticLevel.WARNING,
                        message="skipped file that resolves outside the scan root",
                        file=_safe_relative(file_path, root=root),
                    )
                )
                continue

            relative = to_relative_posix(file_path, root=root)
            if matcher.is_ignored(relative, is_dir=False):
                continue
            if _matches_exclude_globs(relative, exclude=config.exclude):
                continue

            yield DiscoveredFile(absolute_path=file_path, relative_posix_path=relative)


def _safe_relative(path: Path, *, root: Path) -> str:
    """Best-effort relative-path rendering for diagnostics about paths we've decided not to
    trust fully (e.g. symlinks) — falls back to the path's name if relative_to fails."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name
