from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import agent_reliability.lint.frontend.python_frontend as pf_module
from agent_reliability.lint.frontend.limits import SCAN_LIMIT_PREFIX, ScanLimits
from agent_reliability.lint.frontend.python_frontend import PythonFrontend


class TestSupports:
    def test_supports_py_files(self, tmp_path: Path) -> None:
        assert PythonFrontend().supports(tmp_path / "a.py") is True

    def test_does_not_support_other_extensions(self, tmp_path: Path) -> None:
        assert PythonFrontend().supports(tmp_path / "a.json") is False
        assert PythonFrontend().supports(tmp_path / "a.txt") is False


class TestSizeLimit:
    def test_oversized_file_is_skipped_with_scan_limit_diagnostic(self, tmp_path: Path) -> None:
        f = tmp_path / "big.py"
        f.write_text("x = 1\n" * 100)
        frontend = PythonFrontend(limits=ScanLimits(max_file_size_bytes=10))

        fragment = frontend.lower(f, root=tmp_path)

        assert fragment.agents == ()
        assert fragment.tool_calls == ()
        assert fragment.retry_policies == ()
        assert len(fragment.diagnostics) == 1
        assert fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)

    def test_file_under_limit_is_processed_normally(self, tmp_path: Path) -> None:
        f = tmp_path / "small.py"
        f.write_text("x = 1\n")
        frontend = PythonFrontend(limits=ScanLimits(max_file_size_bytes=1000))
        fragment = frontend.lower(f, root=tmp_path)
        assert fragment.diagnostics == ()


class TestNodeLimit:
    def test_file_over_node_limit_is_skipped(self, tmp_path: Path) -> None:
        f = tmp_path / "many_statements.py"
        f.write_text("\n".join(f"x{i} = {i}" for i in range(200)))
        frontend = PythonFrontend(limits=ScanLimits(max_ast_nodes=5))

        fragment = frontend.lower(f, root=tmp_path)

        assert fragment.agents == ()
        assert len(fragment.diagnostics) == 1
        assert fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)
        assert "node" in fragment.diagnostics[0].message


class TestPerFileTimeBudget:
    def test_zero_budget_aborts_before_lowering(self, tmp_path: Path) -> None:
        f = tmp_path / "a.py"
        f.write_text("while True:\n    client.step()\n")
        frontend = PythonFrontend(limits=ScanLimits(per_file_time_budget_seconds=0.0))

        fragment = frontend.lower(f, root=tmp_path)

        assert fragment.agents == ()
        assert len(fragment.diagnostics) == 1
        assert fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)
        assert "time budget" in fragment.diagnostics[0].message

    def test_budget_exceeded_only_after_lowering_keeps_partial_results(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        f = tmp_path / "a.py"
        f.write_text("while True:\n    client.step()\n")
        frontend = PythonFrontend(limits=ScanLimits(per_file_time_budget_seconds=0.05))

        # Three time.monotonic() calls happen in lower(): start, the post-parse check, and the
        # post-lowering check. Simulate time passing only between the second and third so the
        # post-parse check stays under budget but the post-lowering check trips the (softer)
        # "results may be incomplete" warning while still returning the lowered IR.
        fake_clock = Mock(side_effect=[0.0, 0.0, 0.1])
        monkeypatch.setattr(pf_module.time, "monotonic", fake_clock)

        fragment = frontend.lower(f, root=tmp_path)

        assert len(fragment.agents) == 1  # lowering still ran and produced results
        assert len(fragment.diagnostics) == 1
        assert fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)
        assert "may be incomplete" in fragment.diagnostics[0].message


class TestUnreadableFile:
    def test_unicode_decode_error_is_caught(self, tmp_path: Path) -> None:
        f = tmp_path / "bad_encoding.py"
        f.write_bytes(b"\xff\xfe\x00\x01invalid utf-8")
        frontend = PythonFrontend()
        fragment = frontend.lower(f, root=tmp_path)
        assert fragment.agents == ()
        assert len(fragment.diagnostics) == 1


class TestStepBoundHeuristic:
    """A compound-condition `if` test (`ast.BoolOp` wrapping a `Compare`) was briefly recognized
    as a visible step bound, to fix a confirmed false positive against real HarnessKit code
    (scripts/review-independence/run-json-atomic.js's retryOnContention()) -- but a second,
    independent review caught that this was a real false-negative regression: an unrelated
    comparison anywhere in a compound condition (e.g. `if client.is_broken() or
    SOME_UNRELATED_FLAG == 1: raise`) would then also read as bounded, even though it has nothing
    to do with bounding iterations. Reverted -- see loops.py's `_test_contains_bound_comparison`
    for the full rationale. `raise`-as-exit for a DIRECT (non-compound) comparison is kept; it
    carries no equivalent false-negative risk.
    """

    def test_compound_condition_is_a_known_accepted_false_positive_again(
        self, tmp_path: Path
    ) -> None:
        f = tmp_path / "a.py"
        f.write_text(
            "def retry_on_contention(fn, deadline):\n"
            "    while True:\n"
            "        try:\n"
            "            return fn()\n"
            "        except Exception as e:\n"
            "            if not is_contended(e) or time.time() >= deadline:\n"
            "                raise\n"
            "            sleep(0.05)\n"
        )
        fragment = PythonFrontend().lower(f, root=tmp_path)

        assert len(fragment.agents) == 1
        assert fragment.agents[0].has_step_bound is False

    def test_direct_comparison_with_raise_exit_is_still_a_visible_bound(
        self, tmp_path: Path
    ) -> None:
        f = tmp_path / "a.py"
        f.write_text(
            "def run_agent(client, max_steps):\n"
            "    steps = 0\n"
            "    while True:\n"
            "        client.step()\n"
            "        steps += 1\n"
            "        if steps >= max_steps:\n"
            "            raise StopIteration()\n"
        )
        fragment = PythonFrontend().lower(f, root=tmp_path)

        assert len(fragment.agents) == 1
        assert fragment.agents[0].has_step_bound is True
        assert fragment.agents[0].step_bound_source == "counter-check"

    def test_compound_condition_with_no_comparison_is_still_unbounded(self, tmp_path: Path) -> None:
        # A compound condition with no relational comparison anywhere is correctly still
        # unbounded.
        f = tmp_path / "a.py"
        f.write_text(
            "def run_agent(client, flag_a, flag_b):\n"
            "    while True:\n"
            "        client.step()\n"
            "        if flag_a or flag_b:\n"
            "            log('flags set')\n"
        )
        fragment = PythonFrontend().lower(f, root=tmp_path)

        assert len(fragment.agents) == 1
        assert fragment.agents[0].has_step_bound is False


class TestEndToEnd:
    def test_lowers_a_realistic_agent_file(self, tmp_path: Path) -> None:
        f = tmp_path / "agent.py"
        f.write_text(
            "import requests\n"
            "from tenacity import retry, stop_after_attempt\n\n"
            "@retry(stop=stop_after_attempt(3))\n"
            "def charge(order_id):\n"
            "    return requests.post('https://x.invalid', timeout=30)\n\n"
            "def run_agent(client):\n"
            "    while True:\n"
            "        client.step()\n"
        )
        frontend = PythonFrontend()
        fragment = frontend.lower(f, root=tmp_path)

        assert fragment.file == "agent.py"
        assert len(fragment.agents) == 1
        assert fragment.agents[0].has_step_bound is False
        assert len(fragment.retry_policies) == 1
        assert fragment.retry_policies[0].max_attempts == 3
        callees = {c.callee for c in fragment.tool_calls}
        assert "requests.post" in callees
        assert fragment.diagnostics == ()
