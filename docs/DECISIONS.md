# Decisions log

A lightweight, append-only log of implementation decisions too small to warrant a full ADR.
Formal ADR files (`docs/adr/NNN-*.md`, MADR format) begin with the public RFC process at launch
(`PLAN.md` §38.7); until then, decisions land here, newest first.

## 2026 — PyPI distribution name: `agent-lint`

**Decision:** the first distribution is published as `agent-lint` on PyPI.

**Context:** `EXECUTION.md` E01 required verifying name availability before building on it, with
`art-lint` as the documented fallback.

**Check performed:** `curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/agent-lint/json`
returned `404` (package does not exist), confirming the name is available as of this check.
GitHub org/repo naming was not independently re-verified in this pass — the repository already
exists at `OmerKal93/master-architect`; a dedicated `agent-reliability-toolkit`-style org/repo
rename is out of scope for E01 and can be revisited before the public launch (E12) without code
changes, since the PyPI name and the repo name are independent.

**Fallback:** not needed. If `agent-lint` becomes unavailable before the first publish (name
squatting, race with another project), fall back to `art-lint` — the internal
`agent_reliability.*` import namespace is unaffected either way.

**Revisit trigger:** before the first real `twine upload` / trusted-publishing run (not yet
performed — see `EXECUTION.md` E04, which builds the package but does not publish it without
separate, explicit authorization).

## 2026 — Package layout: single distribution, src layout, no uv workspace yet

**Decision:** the `agent-lint` distribution lives at `packages/agent-lint/` with a `src/`
layout (`packages/agent-lint/src/agent_reliability/{core,lint}/`). There is no root-level uv
workspace `pyproject.toml` — contributors `cd packages/agent-lint` before running `uv sync`.

**Context:** `EXECUTION.md` E01 deliberately defers the uv workspace / monorepo package split
(gate: `PLAN.md` §37 "Package split") since there is only one distribution today. A workspace
manifest with one member is speculative infrastructure with no second consumer.

**Evolution seam:** when the package-split gate opens (e.g. ReplaySafe needs a runtime-neutral
core), `agent_reliability/core/` moves to `packages/agent-core/src/agent_reliability/core/`
with its own `pyproject.toml`, and a root `pyproject.toml` workspace member list is added at
that point — a directory move plus one new file, not a rewrite.

**Revisit trigger:** the package-split gate (`PLAN.md` §37).
