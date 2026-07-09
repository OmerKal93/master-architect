"""Placeholder test proving the dev harness works end to end (E01).

This is intentionally trivial: its job is to make ``uv sync && uv run pytest`` succeed on a
clean clone, on every OS in the CI matrix, before any real functionality exists.
"""

import agent_reliability
import agent_reliability.core
import agent_reliability.lint


def test_version_is_a_string() -> None:
    assert isinstance(agent_reliability.__version__, str)
    assert agent_reliability.__version__


def test_subpackages_import_cleanly() -> None:
    # Import success is the assertion: both subpackages must exist and be importable with no
    # side effects (no file I/O, no network) at import time.
    assert agent_reliability.core is not None
    assert agent_reliability.lint is not None
