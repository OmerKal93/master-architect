from __future__ import annotations

import pytest

from agent_reliability.core.model import SourceSpan


def test_valid_span() -> None:
    span = SourceSpan(file="a/b.py", start_line=1, start_col=0, end_line=1, end_col=10)
    assert span.file == "a/b.py"


@pytest.mark.parametrize(
    "file",
    [
        "/absolute/path.py",
        "C:/windows/path.py",
        "a\\b\\c.py",
    ],
)
def test_rejects_non_repo_relative_paths(file: str) -> None:
    with pytest.raises(ValueError, match="repo-relative|POSIX-normalized"):
        SourceSpan(file=file, start_line=1, start_col=0, end_line=1, end_col=1)


def test_rejects_invalid_line_range() -> None:
    with pytest.raises(ValueError, match="invalid line range"):
        SourceSpan(file="a.py", start_line=5, start_col=0, end_line=2, end_col=0)


def test_rejects_zero_start_line() -> None:
    with pytest.raises(ValueError):
        SourceSpan(file="a.py", start_line=0, start_col=0, end_line=1, end_col=0)


def test_span_is_frozen_and_hashable() -> None:
    span = SourceSpan(file="a.py", start_line=1, start_col=0, end_line=1, end_col=1)
    with pytest.raises(AttributeError):
        span.file = "b.py"  # type: ignore[misc]
    assert hash(span) == hash(
        SourceSpan(file="a.py", start_line=1, start_col=0, end_line=1, end_col=1)
    )
