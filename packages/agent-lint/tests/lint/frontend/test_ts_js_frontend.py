from __future__ import annotations

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
        broken_script.write_text("process.stderr.write('Cannot find package typescript'); process.exit(1);\n")
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

    def test_oversized_file_is_skipped_with_scan_limit_diagnostic(self, tmp_path: Path) -> None:
        f = tmp_path / "big.js"
        f.write_text("var x = 1;\n" * 100)
        frontend = TsJsFrontend(limits=ScanLimits(max_file_size_bytes=10))

        fragment = frontend.lower(f, root=tmp_path)

        assert fragment.agents == ()
        assert len(fragment.diagnostics) == 1
        assert fragment.diagnostics[0].message.startswith(SCAN_LIMIT_PREFIX)
