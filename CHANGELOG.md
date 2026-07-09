# Changelog

All notable changes to this project are documented in this file. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this file is hand-written until
release cadence justifies automation (see `EXECUTION.md`, deferred: full release machinery).

## [Unreleased]

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
