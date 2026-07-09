from __future__ import annotations

from agent_reliability.lint.frontend.gitignore import GitignoreMatcher


def test_empty_matcher_ignores_nothing() -> None:
    matcher = GitignoreMatcher.empty()
    assert matcher.is_ignored("a.py", is_dir=False) is False


def test_simple_basename_pattern() -> None:
    matcher = GitignoreMatcher.from_text("*.pyc\n")
    assert matcher.is_ignored("a.pyc", is_dir=False) is True
    assert matcher.is_ignored("sub/a.pyc", is_dir=False) is True
    assert matcher.is_ignored("a.py", is_dir=False) is False


def test_directory_only_pattern() -> None:
    matcher = GitignoreMatcher.from_text("build/\n")
    assert matcher.is_ignored("build", is_dir=True) is True
    assert matcher.is_ignored("build", is_dir=False) is False


def test_anchored_pattern() -> None:
    matcher = GitignoreMatcher.from_text("/only_at_root.py\n")
    assert matcher.is_ignored("only_at_root.py", is_dir=False) is True
    assert matcher.is_ignored("sub/only_at_root.py", is_dir=False) is False


def test_negation_overrides_earlier_match() -> None:
    matcher = GitignoreMatcher.from_text("*.py\n!keep.py\n")
    assert matcher.is_ignored("drop.py", is_dir=False) is True
    assert matcher.is_ignored("keep.py", is_dir=False) is False


def test_comments_and_blank_lines_are_ignored() -> None:
    matcher = GitignoreMatcher.from_text("# a comment\n\n*.pyc\n")
    assert matcher.is_ignored("a.pyc", is_dir=False) is True


def test_later_pattern_wins_over_earlier() -> None:
    # Standard gitignore semantics: patterns are applied in order, last match wins.
    matcher = GitignoreMatcher.from_text("!important.log\n*.log\n")
    assert matcher.is_ignored("important.log", is_dir=False) is True


def test_nested_path_pattern() -> None:
    matcher = GitignoreMatcher.from_text("vendor/\n")
    assert matcher.is_ignored("vendor", is_dir=True) is True
