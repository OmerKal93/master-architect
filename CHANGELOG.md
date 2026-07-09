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
