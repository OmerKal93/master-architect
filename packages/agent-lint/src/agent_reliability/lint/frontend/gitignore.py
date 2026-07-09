"""A minimal ``.gitignore`` pattern matcher.

This supports the common subset of gitignore syntax — blank lines, ``#`` comments, ``!``
negation, directory-only patterns ending in ``/``, and glob wildcards — matched against the
repo-relative path from a single root-level ``.gitignore`` file. It is **not** a complete
implementation of git's ignore semantics: nested ``.gitignore`` files, ``**`` double-wildcard
edge cases, and escape-sequence handling are not supported. This is a documented, honest
limitation (consistent with the project's stance on not overclaiming static analysis
capabilities) rather than a bug to silently work around.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True, slots=True)
class _Pattern:
    regex: re.Pattern[str]
    negation: bool
    dir_only: bool
    anchored: bool  # contains a "/" other than a single trailing one -> match from root


def _compile_pattern(raw_line: str) -> _Pattern | None:
    line = raw_line.rstrip("\n")
    if not line or line.startswith("#"):
        return None

    negation = line.startswith("!")
    if negation:
        line = line[1:]
    if not line:
        return None

    dir_only = line.endswith("/")
    if dir_only:
        line = line[:-1]
    if not line:
        return None

    # A pattern is "anchored" (matched from the root) if it contains a "/" anywhere except as
    # the very last character (already stripped above for dir_only).
    anchored = "/" in line
    if line.startswith("/"):
        line = line[1:]
        anchored = True

    return _Pattern(
        regex=re.compile(fnmatch.translate(line)),
        negation=negation,
        dir_only=dir_only,
        anchored=anchored,
    )


class GitignoreMatcher:
    """Matches repo-relative POSIX paths against a set of gitignore patterns."""

    def __init__(self, patterns: list[_Pattern]) -> None:
        self._patterns = patterns

    @classmethod
    def from_text(cls, text: str) -> GitignoreMatcher:
        patterns = [p for p in (_compile_pattern(line) for line in text.splitlines()) if p]
        return cls(patterns)

    @classmethod
    def empty(cls) -> GitignoreMatcher:
        return cls([])

    def is_ignored(self, relative_posix_path: str, *, is_dir: bool) -> bool:
        path = PurePosixPath(relative_posix_path)
        ignored = False
        for pattern in self._patterns:
            if pattern.dir_only and not is_dir:
                continue
            if pattern.anchored:
                matched = bool(pattern.regex.match(relative_posix_path))
            else:
                # Unanchored patterns match the basename at any depth.
                matched = bool(pattern.regex.match(path.name)) or bool(
                    pattern.regex.match(relative_posix_path)
                )
            if matched:
                ignored = not pattern.negation
        return ignored
