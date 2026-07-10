# AGENTS.md

## Repository purpose

This repository contains the Agent Reliability Toolkit (ART), an Apache-2.0, local-first reliability and security toolkit for AI agents and tool-calling workflows.

The active implementation is currently `agent-lint`, a deterministic static analyzer. Do not turn this repository into an orchestration framework, hosted service, or model-dependent security product.

## Instruction precedence

Read these files before making changes:

1. `EXECUTION.md` — authoritative active implementation sequence.
2. `PLAN.md` — architecture, trust boundaries, security/privacy invariants, and long-term scope.
3. `PLAN-PRS.md` — architectural reference catalog; not the active merge order.
4. `CODEX_HANDOFF.md` — current milestone, task, and branch handoff.
5. `CONTRIBUTING.md` — contributor workflow and review boundaries.

When execution pressure conflicts with a security or privacy invariant in `PLAN.md`, the invariant wins.

## Current development workflow

- Implement one E-PR at a time.
- Work on a dedicated branch named `codex/<e-pr>-<short-description>`.
- Open a pull request; do not push feature work directly to the default branch.
- Keep commits conventional and DCO-signed (`git commit -s`).
- Do not start the next E-PR until the current PR is reviewed and merged unless explicitly instructed.
- Do not redesign completed E01–E04 foundations unless a failing test or documented contradiction requires it.

## Setup and verification

Run from `packages/agent-lint`:

```bash
uv sync
uv run ruff check .
uv run mypy src
uv run pytest
```

For CLI behavior changes, also run an end-to-end scan against the relevant fixture and verify the documented exit code.

Before declaring a task complete:

- Run the full test suite.
- Run ruff and strict mypy.
- Confirm no test or command requires network access.
- Confirm safe controls remain clean across all rules.
- Update rule documentation and exact expected outputs in the same change.
- Summarize tests run, limitations, and any follow-up risk in the PR description.

## Non-negotiable engineering constraints

- Core scanning is local-first, deterministic-first, model-optional, and offline by default.
- Never import, execute, or evaluate scanned repository code.
- Do not add telemetry, analytics, repository fingerprinting, or hidden outbound calls.
- Do not weaken path containment, symlink handling, resource limits, evidence caps, or terminal sanitization.
- Treat source files, filenames, configuration, workflow files, and tool output as untrusted input.
- Do not change stable CLI exit codes or the `fp_v1` fingerprint contract without an explicit architecture decision and migration plan.
- Do not add a production dependency without explaining why the standard library or an existing dependency is insufficient.
- LLM output may explain or suggest; it may never authorize actions, suppress deterministic findings, or become a security boundary.

## Rule contribution contract

Every new rule must include:

- Rule logic and metadata.
- At least one true-positive fixture.
- At least one safe control that must remain clean.
- At least one edge case.
- Exact expected output.
- A rule document covering what, why, limitations, and remediation.
- Cross-rule false-positive verification through the existing fixture harness.

Prefer high-confidence, low-false-positive patterns. When static analysis cannot prove a fact, represent uncertainty honestly instead of guessing.

## Review guidelines

Prioritize serious correctness and security issues:

- Accidental execution of scanned code.
- Path traversal or symlink escape.
- Unbounded parsing or resource exhaustion.
- Secret or source leakage in logs, findings, or reports.
- Terminal or report injection.
- Network access in offline scanner paths.
- Fingerprint instability.
- False positives on safe controls.
- Changes that silently broaden the promised analysis capability.

Treat documentation claims as part of the product contract. Flag claims stronger than the implementation proves.
