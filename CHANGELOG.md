# Changelog

All notable changes to this project are documented in this file. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this file is hand-written until
release cadence justifies automation (see `EXECUTION.md`, deferred: full release machinery).

## [Unreleased]

## [0.1.0] - 2026-07-09

The first installable proof: `pip install agent-lint`, then `agent-lint scan .` finds a real
unbounded agent loop, entirely offline. Implements `EXECUTION.md` E01–E04.

### Added

- Repository bootstrap: license (Apache-2.0), community docs (SECURITY, CONTRIBUTING,
  CODE_OF_CONDUCT), CI workflow, and the `agent-lint` package skeleton
  (`agent_reliability.core` + `agent_reliability.lint` namespace). (E01)
- The permanent domain model and engine contracts: `SourceSpan`, `Finding`, `Severity`,
  `Confidence`, `Category`, the `fp_v1` fingerprint algorithm, the micro-IR (`Agent`,
  `RetryPolicy`, `ToolCall`, `TimeoutPolicy`), the minimal `.agent-reliability.yaml` config
  loader, and the `Rule`/`RuleContext`/`Frontend` contracts every rule and frontend will
  implement. Published subset schema at `docs/schemas/finding-v1.json`. (E02)
- The safe Python frontend (`agent_reliability.lint.frontend`): resource-limited, symlink-safe
  file discovery with a minimal `.gitignore` matcher; safe AST parsing that never imports or
  executes scanned code and never hangs or crashes on hostile input (deeply nested expressions,
  oversized files, malicious filenames, symlink escapes); and heuristic lowering of agentic
  loops, tool-call sites, and retry patterns (tenacity, stamina, manual loops) into the micro-IR.
  See `docs/architecture/what-the-analyzer-sees.md` for the honest capability statement, and
  `fixtures/malicious/` / `fixtures/frontends/` for the hostile-input and golden-IR fixture
  corpora. (E03)
- The `agent-lint scan [PATH]` CLI with a stable exit-code contract (0 clean / 1 findings /
  2 usage error / 3 internal error / 4 partial scan) and terminal-escape-safe text output.
  **AR001 — Agent loop has no maximum step count**, the first rule: see
  `packages/agent-lint/src/agent_reliability/lint/rules/ar001/docs.md` for what it detects and
  its documented limits. The rule fixture harness (`tools/art_rule_test.py`) that will gate
  every future rule, with its first fixtures at `fixtures/rules/AR001/`. See
  `docs/quickstart.md` for the full walkthrough. (E04)

### Known limitations

- Only one rule (AR001) exists; more land in `EXECUTION.md` E05 onward.
- Only text output; JSON and SARIF land in E06.
- No suppressions, baselines, or `explain` yet; land in E07/E13.
- No framework awareness (LangGraph, MCP, n8n) yet; LangGraph recognition lands in E08.
