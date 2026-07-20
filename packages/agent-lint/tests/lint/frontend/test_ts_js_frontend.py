from __future__ import annotations

import subprocess
from pathlib import Path

from agent_reliability.lint.frontend.limits import SCAN_LIMIT_PREFIX, ScanLimits
from agent_reliability.lint.frontend.ts_js_frontend import TsJsFrontend


class TestSupports:
    def test_supports_ts_and_js_files(self, tmp_path: Path) -> None:
        assert TsJsFrontend().supports(tmp_path / "a.ts") is True
        assert TsJsFrontend().supports(tmp_path / "a.js") is True

    def test_does_not_support_declaration_files_or_other_extensions(self, tmp_path: Path) -> None:
        assert TsJsFrontend().supports(tmp_path / "a.d.ts") is False
        assert TsJsFrontend().supports(tmp_path / "a.py") is False
        assert TsJsFrontend().supports(tmp_path / "a.json") is False


class TestWorkerReuse:
    """Regression tests for F6 (docs/ts-js-frontend-harnesskit-dogfood.md): a fresh Node process
    per file was measured at ~290ms/file, dominated by startup + `require('typescript')`, enough
    to make a full-repo scan hit the whole-scan wall-clock budget from spawn overhead alone. The
    fix reuses one persistent `node parse_one_file.mjs --serve` process across every file scanned
    by the same TsJsFrontend instance -- these tests assert that reuse actually happens (only one
    Popen call across multiple lower() calls) rather than just trusting the implementation.
    """

    def test_one_process_is_reused_across_multiple_files(self, tmp_path: Path, monkeypatch) -> None:
        real_popen = subprocess.Popen
        popen_calls: list[list[str]] = []

        def counting_popen(cmd, *args, **kwargs):
            popen_calls.append(cmd)
            return real_popen(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "Popen", counting_popen)

        frontend = TsJsFrontend()
        for i in range(5):
            f = tmp_path / f"a{i}.js"
            f.write_text(f"function run{i}() {{ while (true) {{ doWork({i}); }} }}\n")
            fragment = frontend.lower(f, root=tmp_path)
            assert fragment.diagnostics == ()
            assert len(fragment.agents) == 1

        assert len(popen_calls) == 1
        assert popen_calls[0][2] == "--serve"

    def test_two_frontend_instances_use_two_workers(self, tmp_path: Path, monkeypatch) -> None:
        # Reuse is per-instance, not a hidden global: a fresh TsJsFrontend must not silently
        # share (or leak) another instance's worker process.
        real_popen = subprocess.Popen
        popen_calls: list[list[str]] = []

        def counting_popen(cmd, *args, **kwargs):
            popen_calls.append(cmd)
            return real_popen(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "Popen", counting_popen)

        f = tmp_path / "a.js"
        f.write_text("function run() { while (true) { doWork(); } }\n")
        TsJsFrontend().lower(f, root=tmp_path)
        TsJsFrontend().lower(f, root=tmp_path)

        assert len(popen_calls) == 2


class TestToolchainFailuresAreScanLimitConditions:
    """Regression tests for a bug caught by independent review: a missing/broken Node
    toolchain used to produce an un-prefixed diagnostic, which the CLI's exit-code contract
    (cli.py) treats as an ordinary parse warning rather than a partial scan -- so `agent-lint
    scan` silently reported exit 0 ("clean scan, no findings") on a repo full of unscanned,
    potentially-unsafe TS/JS files whenever the `typescript` npm dependency wasn't installed.
    These diagnostics must carry SCAN_LIMIT_PREFIX so cli.py maps them to exit 4 instead.
    """

    def test_node_executable_not_found_is_a_scan_limit_diagnostic(self, tmp_path: Path) -> None:
        f = tmp_path / "a.js"
        f.write_text("while (true) { doWork(); }\n")
        frontend = TsJsFrontend(node_executable="definitely-not-a-real-node-binary-xyz")

        fragment = frontend.lower(f, root=tmp_path)

        assert fragment.agents == ()
        assert len(fragment.diagnostics) == 1
        assert fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)

    def test_parser_process_nonzero_exit_is_a_scan_limit_diagnostic(self, tmp_path: Path) -> None:
        # Mirrors what happens for real when the `typescript` npm package is not installed:
        # the Node subprocess exits non-zero with no JSON on stdout.
        broken_script = tmp_path / "broken_parser.mjs"
        broken_script.write_text(
            "process.stderr.write('Cannot find package typescript'); process.exit(1);\n"
        )
        f = tmp_path / "a.js"
        f.write_text("while (true) { doWork(); }\n")
        frontend = TsJsFrontend(script_path=broken_script)

        fragment = frontend.lower(f, root=tmp_path)

        assert fragment.agents == ()
        assert len(fragment.diagnostics) == 1
        assert fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)

    def test_malformed_json_output_is_a_scan_limit_diagnostic(self, tmp_path: Path) -> None:
        broken_script = tmp_path / "broken_parser.mjs"
        broken_script.write_text("process.stdout.write('not json');\n")
        f = tmp_path / "a.js"
        f.write_text("while (true) { doWork(); }\n")
        frontend = TsJsFrontend(script_path=broken_script)

        fragment = frontend.lower(f, root=tmp_path)

        assert fragment.agents == ()
        assert len(fragment.diagnostics) == 1
        assert fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)

    def test_ordinary_syntax_error_is_not_a_scan_limit_diagnostic(self, tmp_path: Path) -> None:
        # Parity check: an ordinary per-file syntax error is NOT a toolchain/resource-limit
        # failure (mirrors ast_utils.py's own "could not parse as Python" -- not scan-limit
        # prefixed -- for an ordinary Python SyntaxError). Only genuinely broken tooling should
        # count toward exit 4.
        f = tmp_path / "a.js"
        f.write_text("this is not valid javascript $$$ {{{\n")
        frontend = TsJsFrontend()

        fragment = frontend.lower(f, root=tmp_path)

        assert fragment.agents == ()
        assert len(fragment.diagnostics) == 1
        assert not fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)
        assert "could not parse" in fragment.diagnostics[0].message


class TestRealParsing:
    def test_unbounded_while_true_loop_is_detected(self, tmp_path: Path) -> None:
        f = tmp_path / "a.js"
        f.write_text("function run() { while (true) { doWork(); } }\n")
        fragment = TsJsFrontend().lower(f, root=tmp_path)

        assert fragment.diagnostics == ()
        assert len(fragment.agents) == 1
        assert fragment.agents[0].has_step_bound is False

    def test_infinite_for_retry_loop_is_detected_as_unbounded(self, tmp_path: Path) -> None:
        # Regression test for a bug caught by independent review: detectRetryPolicies() in
        # parse_one_file.mjs only recognized while(true) as an unconditional loop for AR014,
        # unlike AR001's own detector in the same file, which already treats for(;;) as the same
        # concept -- an unbounded for(;;)-retry loop produced zero AR014 findings.
        f = tmp_path / "a.js"
        f.write_text(
            "function uploadWithRetry(client, path) {\n"
            "  for (;;) {\n"
            "    try {\n"
            "      client.upload(path);\n"
            "      break;\n"
            "    } catch (err) {\n"
            "      continue;\n"
            "    }\n"
            "  }\n"
            "}\n"
        )
        fragment = TsJsFrontend().lower(f, root=tmp_path)

        assert fragment.diagnostics == ()
        assert len(fragment.retry_policies) == 1
        assert fragment.retry_policies[0].bound.value == "unbounded"

    def test_compound_condition_with_throw_exit_is_a_visible_bound(self, tmp_path: Path) -> None:
        # Regression test for a false positive caught by independent dogfood review against real
        # HarnessKit code: scripts/review-independence/run-json-atomic.js's retryOnContention()
        # -- a compound `||` condition wrapping a comparison, exiting via `throw`, was not
        # recognized as a visible step bound. See parse_one_file.mjs's testContainsBoundComparison.
        f = tmp_path / "a.js"
        f.write_text(
            "function retryOnContention(fn, deadline) {\n"
            "  for (;;) {\n"
            "    try {\n"
            "      return fn();\n"
            "    } catch (e) {\n"
            "      if (!isContendedLockError(e) || Date.now() >= deadline) throw e;\n"
            "      sleepSync(50);\n"
            "    }\n"
            "  }\n"
            "}\n"
        )
        fragment = TsJsFrontend().lower(f, root=tmp_path)

        assert len(fragment.agents) == 1
        assert fragment.agents[0].has_step_bound is True
        assert fragment.agents[0].step_bound_source == "counter-check"

    def test_compound_condition_with_no_comparison_is_still_unbounded(self, tmp_path: Path) -> None:
        # A compound condition with no relational comparison anywhere is correctly still
        # unbounded -- the widened heuristic must not start treating every `if` as a bound.
        f = tmp_path / "a.js"
        f.write_text(
            "function runAgent(client, flagA, flagB) {\n"
            "  while (true) {\n"
            "    client.step();\n"
            "    if (flagA || flagB) { log('flags set'); }\n"
            "  }\n"
            "}\n"
        )
        fragment = TsJsFrontend().lower(f, root=tmp_path)

        assert len(fragment.agents) == 1
        assert fragment.agents[0].has_step_bound is False

    def test_oversized_file_is_skipped_with_scan_limit_diagnostic(self, tmp_path: Path) -> None:
        f = tmp_path / "big.js"
        f.write_text("var x = 1;\n" * 100)
        frontend = TsJsFrontend(limits=ScanLimits(max_file_size_bytes=10))

        fragment = frontend.lower(f, root=tmp_path)

        assert fragment.agents == ()
        assert len(fragment.diagnostics) == 1
        assert fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)
