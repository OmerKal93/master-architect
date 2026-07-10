# Codex Development Handoff

## Current state

The repository has completed execution-wave E01–E04 and reached the v0.1.0 implementation milestone.

Implemented commits:

- E01 — repository bootstrap and package skeleton.
- E02 — final-shaped finding model, micro-IR, configuration, and Rule/Frontend contracts.
- E03 — safe parse-only Python frontend with hostile-input and resource-limit tests.
- E04 — working CLI and AR001, including wheel-build and clean-environment smoke verification.

The current implementation head before this handoff was:

```text
e8ca1ed8a282467e6504f36021d4cf715e0854b7
```

PyPI trusted publishing is prepared but not activated. Do not publish, create a release tag, or perform external irreversible actions without explicit human approval.

## Active task

Implement **EXECUTION.md E05 — Rules AR003 and AR014**.

Work on a dedicated branch, preferably:

```text
codex/e05-ar003-ar014
```

Open a pull request against the repository's active base branch. Do not push feature work directly to the base branch.

## Required scope

### AR003 — Tool or external call without timeout

Detect high-confidence, statically visible calls where a timeout is absent and there is no enclosing `TimeoutPolicy` evidence.

Initial supported call shapes should be conservative and reviewable, covering only patterns justified by fixtures and current SDK documentation, such as:

- `requests`
- `httpx`
- `urllib3`
- OpenAI SDK calls already recognizable by the current frontend
- Anthropic SDK calls already recognizable by the current frontend

Avoid broad name-only matching that creates false positives.

### AR014 — Retry policy without an upper bound

Detect high-confidence patterns such as:

- tenacity retry configuration without a stopping condition
- explicit `stop=None`
- `max_retries=None`
- recognized unbounded manual retry loops

Do not introduce side-effect classification. That belongs to E09/E13.

## Required artifacts per rule

Each rule must include:

- rule implementation
- metadata
- documentation with what, why, remediation, and known limits
- at least one true-positive fixture
- at least one safe-control fixture
- at least one edge-case fixture
- exact expected finding output
- integration with the existing cross-rule false-positive fixture harness

## Acceptance criteria

- AR003 and AR014 fire on their seeded unsafe fixtures.
- Both remain silent on all safe-control fixtures across the repository.
- AR001 behavior and output remain unchanged.
- No scanned code is imported or executed.
- No new production dependency is added unless explicitly approved.
- No network access or telemetry is introduced.
- Finding fingerprints, field names, and CLI exit-code semantics remain stable.
- Documentation accurately states unsupported cases and uncertainty.
- The complete test suite passes on supported Python versions.

## Local commands

Run from `packages/agent-lint`:

```bash
uv sync
uv run ruff check .
uv run mypy src
uv run pytest
uv run agent-lint scan ../../fixtures/rules/AR001/unsafe
```

Also run the rule fixture harness and any new E05-specific smoke commands introduced by the implementation.

## Security invariants

Do not weaken these constraints:

- analysis is parse-only
- scanned repositories are untrusted
- symlinks are not followed by default
- discovered paths remain inside the selected root
- resource limits remain enforced
- terminal evidence remains escape-stripped
- offline execution remains the default
- rules receive no I/O capability

If E05 appears to require changing a security boundary, stop and propose an ADR instead of silently changing it.

## Pull request requirements

The pull request must include:

- concise implementation summary
- explicit non-goals
- fixture and false-positive strategy
- commands run and results
- security/privacy impact
- known limitations
- no unrelated refactoring
- DCO sign-off on commits where supported

Request a focused review for false positives, scanner safety, and regression of AR001.