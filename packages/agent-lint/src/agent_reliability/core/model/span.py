"""Source location — the one place file paths appear in the domain model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """A location in a scanned file.

    ``file`` is always repo-relative and POSIX-normalized (forward slashes, no leading ``./``
    or drive letters), regardless of host OS — this is what keeps fingerprints and reports
    portable across machines. Frontends are responsible for normalizing paths before
    constructing a span; nothing downstream re-derives it from an absolute path.
    """

    file: str
    start_line: int
    start_col: int
    end_line: int
    end_col: int

    def __post_init__(self) -> None:
        if self.file.startswith("/") or ":" in self.file.split("/", 1)[0]:
            raise ValueError(f"SourceSpan.file must be repo-relative, got: {self.file!r}")
        if "\\" in self.file:
            raise ValueError(f"SourceSpan.file must be POSIX-normalized, got: {self.file!r}")
        if self.start_line < 1 or self.end_line < self.start_line:
            raise ValueError(
                f"SourceSpan has invalid line range: "
                f"start_line={self.start_line}, end_line={self.end_line}"
            )
