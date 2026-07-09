# Agent Reliability Toolkit — Architectural PR Catalog

Companion to [`PLAN.md`](PLAN.md) §31. **95 PRs (PR-001 … PR-095)** across Milestones A–N.

**What this document is:** the complete architectural decomposition of the system — proof that
every component in the Master Architecture Roadmap has been thought through to reviewable-PR
granularity, in *architectural dependency order*, as a reference implementation decomposition.

**What this document is not:** the committed merge order. **[`EXECUTION.md`](EXECUTION.md)
controls the active implementation sequence** (the first execution wave, E01–E14, and the
releases v0.1.0 → v0.5.x). Later catalog PRs are **subject to gate-driven resequencing**: after
validation (PLAN.md §37), they may be reordered, merged, split, or deferred. A PR may start
earlier than its catalog position if its `Depends on` PRs are merged. Release-boundary PRs are
marked **⛳ RELEASE** (architecture-era version numbers; committed-wave versions live in
`EXECUTION.md`).

## Mapping: committed execution wave → catalog coverage

| E-PR (EXECUTION.md) | Architectural catalog coverage |
|---|---|
| E01 — Minimal OSS bootstrap | selected parts of PR-001, PR-002 |
| E02 — Contracts + finding model + micro-IR | minimal subset of PR-005, PR-007 |
| E03 — Safe Python frontend | selected parts of PR-008 |
| E04 — CLI + AR001 → v0.1.0 | PR-009 |
| E05 — AR003 + AR014 | PR-012 |
| E06 — JSON + SARIF + schemas | PR-013 |
| E07 — Explain/docs/suppressions → v0.2.0 | selected parts of PR-015, PR-021 |
| E08 — LangGraph recognition | selected parts of PR-025, PR-026, PR-027 (lowering only) |
| E09 — Minimal classifier + LG rules → v0.3.0 | selected parts of PR-016 (subset), PR-027, PR-028 |
| E10 — Malicious-repo + offline hardening | selected parts of PR-006 (redaction subset), PR-010 (guard half), PR-022 |
| E11 — GitHub Action | selected parts of PR-033, PR-034 (reduced), PR-035 |
| E12 — Public launch → v0.4.0 | selected parts of PR-004 (docs scaffold), PR-023 (examples), community docs |
| E13 — Adoption features + AR002/AR011 → v0.5.x | selected parts of PR-014, PR-015 (completion), PR-016 (expansion), PR-017, PR-032 |
| E14 — Evidence review + next-wave decision | no code equivalent — gate review (PLAN.md §37) |

Catalog PRs *partially* covered by the wave (e.g. PR-016's full classification engine, PR-022's
multiprocessing performance work, PR-024's plugin loading) retain their remaining scope here and
proceed per their milestone's gate status.

Every PR entry carries the 25 fields required by the specification (§11.1), in this fixed layout:

- Header line: **ID — Title**, then *Area · Complexity (S/M/L) · Contributor-friendly (yes/no) ·
  Publishable artifact*.
- **Value** (user-visible), **Scope** (exact), **Non-goals**, **Files/packages**,
  **Public APIs** (introduced/changed), **Data models**, **New deps**, **Security**,
  **Privacy/egress**, **Tests**, **Docs**, **Acceptance criteria**,
  **Release / Migration / Rollback**, **Depends on → Enables**, **Demo**, **Done when**.

Global invariants for **every** PR (not repeated below): main stays green and releasable; no
half-wired abstractions; changelog fragment (towncrier) included; Conventional Commit title;
docs updated or `docs-exempt` justified; no network access introduced outside the Egress Broker;
rollback = `git revert` unless stated otherwise (all schema changes below state their own).

---

## Milestone A — Repository and governance foundation

> **Status: Committed via the execution wave.** `EXECUTION.md` (E01–E14) resequences and narrows this milestone; the entries below are the full architecture-era decomposition and the reference design for the remaining scope. Full governance artifacts are behind the governance-expansion gate (PLAN.md §37).

### PR-001 — Repository bootstrap: license, governance, and community docs
*Area: repo/governance · Complexity: S · Contributor-friendly: no · Artifact: none*
- **Value:** The project exists as a credible, contributable open-source repository.
- **Scope:** LICENSE (Apache-2.0), NOTICE, README (thesis + status + roadmap pointer),
  SECURITY.md (disclosure contact, 90-day coordinated policy, GH security advisories),
  CONTRIBUTING.md (DCO sign-off, workflow, review policy), CODE_OF_CONDUCT.md (Contributor
  Covenant 2.1), GOVERNANCE.md (maintainer model + ladder), issue templates (bug/rule-FP/
  rule-proposal/security-redirect), PR template (with mandatory sections: scope, non-goals,
  security impact, tests, docs, migration), `.editorconfig`, `.gitignore`. **Verify PyPI/npm/org
  name availability** (`agent-lint`, `replaysafe`, `agent-chaos`, `agent-contract`) and record
  outcome + fallbacks in `docs/adr/000-naming.md` (PLAN.md §34 item 11).
- **Non-goals:** No code, no CI, no packaging.
- **Files/packages:** repo root, `.github/`, `docs/adr/000-naming.md`.
- **Public APIs:** none. · **Data models:** none. · **New deps:** none.
- **Security:** Disclosure process live from day one; PR template forces security-impact notes.
- **Privacy/egress:** README states local-first/no-telemetry commitments explicitly.
- **Tests:** none (no code); CI comes in PR-002.
- **Docs:** Everything in scope *is* docs.
- **Acceptance criteria:** All files present; names verified or fallbacks recorded; templates
  render on GitHub.
- **Release / Migration / Rollback:** No release; no migration; revert-safe.
- **Depends on:** — → **Enables:** all.
- **Demo:** Repo landing page reads as a real project; opening an issue shows the templates.
- **Done when:** Merged to main; branch protection + CODEOWNERS enabled.

### PR-002 — uv workspace, package skeletons, and CI pipeline
*Area: repo/build · Complexity: M · Contributor-friendly: no · Artifact: none (installable dev packages)*
- **Value:** `uv sync && pytest` works for every contributor on Linux/macOS/Windows; CI enforces it.
- **Scope:** Root `pyproject.toml` (uv workspace); `packages/agent-core` and `packages/agent-lint`
  minimal-but-installable (version module, `__all__ = []`, one placeholder test each — removed by
  PR-005/009); ruff + mypy config; pre-commit; GitHub Actions CI: lint/type/test matrix
  (3 OS × Python 3.10–3.13), path-filtered; commit-lint (Conventional Commits); pip-audit +
  lockfile-drift job.
- **Non-goals:** No domain code; no publishing; no other packages yet (created when first needed).
- **Files/packages:** `pyproject.toml`, `uv.lock`, `packages/agent-core/`, `packages/agent-lint/`,
  `.github/workflows/ci.yml`, `.pre-commit-config.yaml`.
- **Public APIs:** none (placeholder modules documented as such). · **Data models:** none.
- **New deps:** dev-only: ruff, mypy, pytest, pre-commit.
- **Security:** Dependency policy starts enforced (hashes in lockfile, pip-audit gate);
  third-party actions SHA-pinned from the first workflow.
- **Privacy/egress:** CI performs no calls beyond GitHub/PyPI infrastructure needs.
- **Tests:** Placeholder unit tests prove the harness; CI matrix green is the test.
- **Docs:** CONTRIBUTING gains "dev setup" section (uv, pre-commit, running tests).
- **Acceptance criteria:** Fresh clone → `uv sync` → `pytest` green on all matrix cells;
  a bad commit message fails CI.
- **Release / Migration / Rollback:** none / none / revert-safe.
- **Depends on:** PR-001 → **Enables:** PR-003…095 (all code PRs).
- **Demo:** CI badge green on the matrix.
- **Done when:** Matrix green; required-checks configured on main.

### PR-003 — Release machinery and changelog discipline
*Area: repo/release · Complexity: S · Contributor-friendly: no · Artifact: none (dry-run wheels)*
- **Value:** Every later PR can ship a changelog fragment; releases are mechanical from day one.
- **Scope:** towncrier config + fragment check in CI; release guide (`docs/release.md`): lockstep
  version bump script (`tools/release.py`), tag → build → **PyPI trusted publishing (OIDC)**
  workflow in dry-run mode (build + twine check, no upload until v0.1.0); versioning &
  compatibility policy doc (pre-1.0 rules from PLAN.md §28).
- **Non-goals:** No actual PyPI upload; no docs-site publishing.
- **Files/packages:** `tools/release.py`, `.github/workflows/release.yml`, `docs/release.md`,
  towncrier config in root pyproject.
- **Public APIs:** none. · **Data models:** none. · **New deps:** dev-only: towncrier, build, twine.
- **Security:** Trusted publishing configured (no long-lived tokens exist, ever).
- **Privacy/egress:** Release workflow contacts PyPI only, on tags only.
- **Tests:** CI job builds sdists/wheels and validates metadata on every PR.
- **Docs:** Release guide; versioning policy.
- **Acceptance criteria:** PR without a fragment fails CI (unless labeled); dry-run release
  workflow produces valid artifacts from a test tag.
- **Release / Migration / Rollback:** none / none / revert-safe.
- **Depends on:** PR-002 → **Enables:** PR-011 (v0.1.0) and every release PR.
- **Demo:** `tools/release.py --dry-run 0.0.1` shows the full mechanical release path.
- **Done when:** Fragment gate active; dry-run artifacts validated.

### PR-004 — Fixture library scaffold, docs site, and founding ADRs
*Area: repo/docs/fixtures · Complexity: M · Contributor-friendly: partially (fixture additions) · Artifact: none*
- **Value:** The security-sensitive fixture library and the docs/ADR system exist before any
  engine code, so every later PR has somewhere to put proof.
- **Scope:** `fixtures/` layout (`rules/`, `frontends/`, `malicious/`, `repos/`) + fixture README
  (naming, safety rules: fixtures are data, never imported by tests as code); seed
  `fixtures/malicious/` with initial T-cases (symlink escape, terminal-escape filename,
  pathological nesting) as inert files; mkdocs-material scaffold with architecture stub; ADR
  template (MADR) + founding ADRs: 001 monorepo, 002 license, 003 python-first, 004 AST
  strategy, 005 IR, 007 local-first, 008 no-telemetry, 009 egress broker, 011 SQLite-first
  (content from PLAN.md §29).
- **Non-goals:** No fixture *consumers* yet; no docs deployment; remaining ADRs land with their
  milestones.
- **Files/packages:** `fixtures/`, `docs/`, `mkdocs.yml`, `docs/adr/`.
- **Public APIs:** none. · **Data models:** fixture manifest convention (`fixture.yaml`: purpose,
  threat refs, expected-findings pointer). · **New deps:** dev-only: mkdocs-material.
- **Security:** Malicious fixtures are quarantined by convention (path-prefixed, CI never
  executes fixture content — enforced from PR-008 onward); documented handling rules.
- **Privacy/egress:** Docs build is local/CI-only; no analytics in the mkdocs config.
- **Tests:** CI job builds the docs site; fixture-manifest schema check.
- **Docs:** ADRs + architecture stub + fixture guide.
- **Acceptance criteria:** `mkdocs build --strict` green; founding ADRs merged; fixture layout
  documented and seeded.
- **Release / Migration / Rollback:** none / none / revert-safe.
- **Depends on:** PR-002 → **Enables:** PR-005+ (every PR citing ADRs/fixtures).
- **Demo:** Locally served docs site shows architecture + ADR index.
- **Done when:** Milestone A exit criteria met (PLAN.md §30 row A).

---

## Milestone B — Core domain and CLI walking skeleton → ⛳ v0.1.0

> **Status: Committed via the execution wave.** `EXECUTION.md` (E01–E14) resequences and narrows this milestone; the entries below are the full architecture-era decomposition and the reference design for the remaining scope. The Egress Broker object (PR-010) is deferred to the model-advisor gate; the no-network socket guard stands in (EXECUTION.md E10).

### PR-005 — agent-core domain model and finding schema
*Area: agent-core · Complexity: L · Contributor-friendly: no · Artifact: agent-reliability-core (at PR-011)*
- **Value:** The stable vocabulary every tool speaks: IR entities, findings, severities, IDs.
- **Scope:** All IR types from PLAN.md §11 (SourceSpan, Program, Agent, Workflow, Node, Edge,
  Tool, ToolCall, SideEffect, RetryPolicy, TimeoutPolicy, ApprovalGate, Checkpoint,
  RiskClassification, Invariant) with `UNKNOWN` semantics; Finding/Rule/Suppression/Baseline/Fix
  types; severity+confidence enums; category enum; deterministic EntityId + fingerprint `fp_v1`;
  JSON serialization + published JSON Schema (`docs/schemas/finding-v1.json`).
- **Non-goals:** No rule engine (PR-007), no frontends (PR-008), no reporters beyond JSON
  round-trip.
- **Files/packages:** `packages/agent-core/src/agent_reliability/core/model/`, `docs/schemas/`.
- **Public APIs:** `agent_reliability.core.model.*` (plugin-facing from v0.3; documented as
  pre-stable). · **Data models:** all of the above (this PR *is* the data model).
- **New deps:** none (stdlib dataclasses; ADR-005 records the choice).
- **Security:** Evidence fields carry length caps at the type level; paths normalized
  repo-relative at construction (T4 groundwork).
- **Privacy/egress:** none.
- **Tests:** Round-trip property tests (hypothesis); fingerprint stability tests (formatting
  perturbations don't change `fp_v1`); schema validation of serialized examples; ID determinism.
- **Docs:** Domain-model reference page; schema published.
- **Acceptance criteria:** Schema validates all fixtures; mypy strict green; 85% coverage.
- **Release / Migration / Rollback:** none yet / schema is v1 from birth / revert-safe.
- **Depends on:** PR-002, PR-004 → **Enables:** PR-006…010 and every engine PR.
- **Demo:** Doctest-style example builds a Finding and validates it against the published schema.
- **Done when:** Acceptance green; ADR-005 cross-referenced.

### PR-006 — Config loader, error taxonomy, and redaction pipeline
*Area: agent-core · Complexity: M · Contributor-friendly: no · Artifact: (with core)*
- **Value:** Safe-by-default configuration and the redaction layer everything else must use.
- **Scope:** Config loading with PLAN.md §9 precedence (CLI > env > user > project > defaults);
  **TB7 enforcement**: scanned-repo config cannot set egress/plugins/telemetry keys (ignored +
  warning diagnostic); `yaml.safe_load` only; error taxonomy (`ArtError` tree + documented CLI
  exit-code mapping); redaction pipeline (pattern + entropy secret detectors, pluggable provider
  hook, applied to evidence/trace/log sinks); default network config `mode: deny`.
- **Non-goals:** No egress broker (PR-010); no trace store (Milestone F-era).
- **Files/packages:** `agent_reliability/core/{config,errors,redact}/`.
- **Public APIs:** `load_config()`, `ArtError` hierarchy, `Redactor` protocol + default.
- **Data models:** Config schema (published JSON Schema) with `network`, `privacy`, `rules`,
  `baseline`, `suppressions` sections.
- **New deps:** pyyaml **[runtime dep #1 — recorded in dependency policy]**.
- **Security:** T5 mitigations (privilege-restricted repo config) + T6 groundwork (redaction
  before any sink); hostile-config fixtures added.
- **Privacy/egress:** Defaults are `deny`/`offline`; tests assert defaults.
- **Tests:** Precedence matrix tests; hostile-config fixtures; redaction corpus (AWS keys, JWTs,
  high-entropy strings, .env formats); idempotence property test (redact∘redact = redact).
- **Docs:** Configuration reference; privacy & egress page (initial).
- **Acceptance criteria:** Repo-scoped config demonstrably cannot enable egress; redaction corpus
  fully caught; exit codes documented.
- **Release / Migration / Rollback:** none / config schema v1 / revert-safe.
- **Depends on:** PR-005 → **Enables:** PR-007…010.
- **Demo:** `python -m agent_reliability.core.config check .agent-reliability.yaml` explains the
  effective config and which keys were ignored and why.
- **Done when:** Acceptance green; security tests in CI.

### PR-007 — Rule engine, plugin contracts, and finding pipeline
*Area: agent-core · Complexity: L · Contributor-friendly: no · Artifact: (with core)*
- **Value:** The deterministic engine that turns IR into deduplicated, suppressible findings.
- **Scope:** `Rule`/`RuleContext` contracts (read-only IR views, no-I/O by construction);
  `ArtPlugin` protocol + `PluginMeta` + `CORE_API_VERSION` (loading itself lands in PR-024);
  engine execution (deterministic ordering, per-rule error isolation → `RuleError` diagnostics);
  finding pipeline: dedupe/merge by fingerprint, severity overrides from config, suppression
  matching (parsing of `# art: ignore[...]` comments), baseline classification hook (baseline
  file I/O lands PR-014); text + JSON reporters with terminal-escape stripping (T12 baseline).
- **Non-goals:** No rules yet (PR-009); no SARIF (PR-013); no entry-point loading (PR-024).
- **Files/packages:** `agent_reliability/core/{engine,plugins,reporting}/`.
- **Public APIs:** `Rule`, `RuleContext`, `ArtPlugin`, `run_rules()`, `Reporter` protocol.
- **Data models:** none new (consumes PR-005).
- **New deps:** none.
- **Security:** RuleContext exposes no filesystem/exec/network capability (T26 by-construction);
  CI grep-test forbids `exec/eval/subprocess/import` usage inside rule modules (armed now, used
  by every rule PR).
- **Privacy/egress:** none.
- **Tests:** Engine determinism (shuffled registration → identical output); isolation (raising
  rule → diagnostic, scan continues); dedupe/merge cases; suppression comment parser corpus;
  escape-stripping tests.
- **Docs:** Engine architecture page; rule lifecycle diagram.
- **Acceptance criteria:** A toy rule registered twice produces one merged finding; a crashing
  rule cannot fail the process; reporters escape hostile strings.
- **Release / Migration / Rollback:** none / none / revert-safe.
- **Depends on:** PR-005, PR-006 → **Enables:** PR-008, PR-009, PR-024.
- **Demo:** Unit-test transcript: toy IR + toy rule → text report.
- **Done when:** Acceptance green; grep-guard job active.

### PR-008 — Python AST frontend with safety limits
*Area: agent-lint frontend · Complexity: L · Contributor-friendly: no · Artifact: (with agent-lint)*
- **Value:** Source code becomes IR — safely, on hostile input, without ever executing it.
- **Scope:** File discovery (gitignore + excludes, symlinks not followed, path-prefix
  containment — T4); resource limits (2 MB/file, AST node cap, per-file timeout, wall-clock
  budget → `scan-limit` diagnostics + exit 4 — T2/T25); `ast.parse`-only pipeline; lowering
  subset needed by Milestone B/C first rules: module/function structure, loop constructs
  (`while True`, recursion candidates), call sites with kwarg extraction, retry-pattern lowering
  (tenacity/stamina decorators, manual retry loops) into `RetryPolicy`, LLM/tool-loop heuristics
  into `Agent` (documented recognition rules).
- **Non-goals:** No side-effect classification (PR-016); no dataflow (PR-020); no LangGraph
  (Milestone D).
- **Files/packages:** `packages/agent-lint/src/agent_reliability/lint/frontend/`.
- **Public APIs:** `Frontend` protocol implementation `PythonFrontend`.
- **Data models:** none new.
- **New deps:** none (stdlib ast — ADR-004).
- **Security:** T1/T2/T4/T13 mitigations implemented and fixture-tested (malicious fixtures from
  PR-004 now consumed in CI); no code object is ever created from scanned content.
- **Privacy/egress:** none.
- **Tests:** Golden expected-IR files for the frontend corpus; malicious/pathological fixtures
  (deep nesting, symlink escapes, hostile filenames) → correct diagnostics, no hang (timeout
  asserted); Windows path tests.
- **Docs:** "What the analyzer sees" page (honest capability statement, PLAN.md §15-style).
- **Acceptance criteria:** Full malicious-fixture suite green; 10s budget on the seed corpus;
  goldens stable across OSes.
- **Release / Migration / Rollback:** none / none / revert-safe.
- **Depends on:** PR-005, PR-007 → **Enables:** PR-009, PR-012+.
- **Demo:** `python -m agent_reliability.lint.frontend dump fixtures/frontends/loops/` prints IR.
- **Done when:** Acceptance green; T-case rows T1/T2/T4/T13 reference these tests.

### PR-009 — agent-lint CLI walking skeleton with AR001 (first real finding)
*Area: agent-lint · Complexity: M · Contributor-friendly: no · Artifact: agent-lint (at PR-011)*
- **Value:** **The product exists:** `agent-lint scan .` finds a real unbounded agent loop.
- **Scope:** Typer CLI: `scan` (text/json via PR-007 reporters), exit-code contract (0/1/2/3/4);
  **AR001** rule (loop-without-step-bound; detection per PLAN.md §14 table) with full rule module
  layout (rule.py, docs.md, fixtures TP/safe/edge, expected.json); the `art-rule-test` harness
  that runs every rule against every fixture with cross-rule FP checking (PLAN.md §13); quickstart
  doc.
- **Non-goals:** No SARIF/baseline/suppress UX (Milestone C); no `explain` (PR-021).
- **Files/packages:** `packages/agent-lint/src/.../cli.py`, `rules/ar001/`,
  `tools/art-rule-test`, `fixtures/rules/AR001/`.
- **Public APIs:** CLI commands + exit codes (a public contract from now on).
- **Data models:** none new.
- **New deps:** typer **[runtime dep #2]**.
- **Security:** CLI output passes redaction + escape stripping; scan of `fixtures/malicious/`
  exercised in CI e2e.
- **Privacy/egress:** e2e test asserts zero network (socket guard) during scan.
- **Tests:** Rule harness (TP/safe/edge + goldens); CLI integration tests (exit codes, formats);
  first false-negative regression file created (empty, with README explaining its purpose).
- **Docs:** Quickstart; AR001 catalog page (generated path proven manually until PR-021 automates).
- **Acceptance criteria:** `agent-lint scan fixtures/rules/AR001/unsafe` → 1 finding, exit 1;
  `.../safe` → 0 findings, exit 0; JSON validates against finding schema.
- **Release / Migration / Rollback:** none yet / none / revert-safe.
- **Depends on:** PR-007, PR-008 → **Enables:** PR-010…023.
- **Demo:** Terminal recording in README: scan → finding with span, why-it-matters, remediation.
- **Done when:** Milestone B's defining artifact works end-to-end offline.

### PR-010 — Egress Broker (deny-all) and offline enforcement
*Area: agent-core/security · Complexity: M · Contributor-friendly: no · Artifact: (with core)*
- **Value:** "Local-first" becomes a *tested invariant*, not a promise: nothing can reach the
  network except through a broker that currently denies everything.
- **Scope:** `EgressBroker` per PLAN.md §9 (destination allowlist, purpose enum, approval modes,
  size/timeout bounds, audit records to a local JSONL — SQLite store arrives with the trace
  layer); default deny; `art doctor --assert-offline`; **CI socket-guard job**: entire test suite
  + CLI e2e run with sockets blocked; import-linter contract: only the broker module may import
  socket/http libraries. *(Narrow infrastructure PR — justified: it is the enforcement mechanism
  for §3.1/3.4 and is consumed immediately by the CI jobs of every subsequent PR; the advisor
  consumes the allow-path in Milestone M.)*
- **Non-goals:** No providers/adapters (Milestone M); no allowlist UX beyond config parsing.
- **Files/packages:** `agent_reliability/core/egress/`, `.github/workflows/ci.yml` (offline job).
- **Public APIs:** `EgressBroker`, `EgressPurpose`, `EgressDenied`.
- **Data models:** Egress audit record (metadata-only, PLAN.md §9).
- **New deps:** dev-only: import-linter, pytest-socket (or equivalent guard).
- **Security:** T19 groundwork; TB3 established; audit-record redaction verified.
- **Privacy/egress:** This PR *is* the egress policy: deny by default, everywhere.
- **Tests:** Broker denial matrix (no allowlist → deny; wrong purpose → deny; oversize → deny);
  audit-record content tests (no payload bodies); offline CI job over the whole suite;
  import-linter contract test.
- **Docs:** Privacy & egress page completed for current scope.
- **Acceptance criteria:** Offline job green across the whole repo; any direct socket use in any
  package fails CI.
- **Release / Migration / Rollback:** none / none / revert-safe (but the CI jobs stay).
- **Depends on:** PR-006 → **Enables:** PR-011 (release claims), Milestone M.
- **Demo:** `art doctor --assert-offline` output; a deliberately-added `requests` import failing CI.
- **Done when:** Offline enforcement is a required check on main.

### PR-011 — ⛳ RELEASE v0.1.0 — walking skeleton
*Area: release · Complexity: S · Contributor-friendly: no · Artifact: **PyPI: agent-reliability-core, agent-lint (v0.1.0)***
- **Value:** Installable proof of the approach: `pip install agent-lint` → real finding, offline.
- **Scope:** Version bump to 0.1.0; changelog assembly; first real PyPI publish via trusted
  publishing; GitHub release with artifacts; README install instructions switch from source to
  pip; post-release smoke workflow (`pip install agent-lint==0.1.0` in a clean container → scan
  fixture → expected finding).
- **Non-goals:** No feature changes.
- **Files/packages:** version files, changelog, release workflow enablement.
- **Public APIs:** none changed — this release *freezes* the exit-code contract at v0.1.
- **Data models:** finding schema v1 published as released.
- **New deps:** none.
- **Security:** Release provenance from CI only; artifacts built in the release workflow.
- **Privacy/egress:** Release notes restate local-first/no-telemetry.
- **Tests:** Post-release smoke job; all gates from PLAN.md §28 release checklist.
- **Docs:** Changelog; versioned quickstart.
- **Acceptance criteria:** Clean-machine install produces the AR001 demo finding offline.
- **Release / Migration / Rollback:** v0.1.0 / none / **yank from PyPI + patch release** is the
  documented rollback for all release PRs (recorded in release guide).
- **Depends on:** PR-003, PR-009, PR-010 → **Enables:** Milestone C.
- **Demo:** The README quickstart, executed verbatim on a clean machine.
- **Done when:** v0.1.0 live on PyPI; smoke green; Milestone B exit criteria met.

---

## Milestone C — Static analyzer MVP → ⛳ v0.2.0

> **Status: Committed via the execution wave.** `EXECUTION.md` (E01–E14) resequences and narrows this milestone; the entries below are the full architecture-era decomposition and the reference design for the remaining scope. The wave ships 7 of these rules (AR001/002/003/011/014 + LG set) plus SARIF, suppressions, baselines, and hardening; remaining rule depth is decided at the E14 evidence review.

### PR-012 — Rules AR014 (unbounded retry) and AR003 (missing timeout)
*Area: agent-lint rules · Complexity: M · Contributor-friendly: yes · Artifact: (with v0.2.0)*
- **Value:** The two highest-frequency, highest-confidence defects after AR001 are caught.
- **Scope:** AR014 (tenacity `stop` absent/None, `max_retries=None`, unbounded manual retry
  loops) and AR003 (HTTP/SDK/tool call sites lacking `timeout` and enclosing TimeoutPolicy);
  matures retry/timeout lowering in the frontend (known-library table: requests, httpx, urllib3,
  openai/anthropic SDK call shapes **[verify SDK surface at implementation]**).
- **Non-goals:** No side-effect awareness (AR002 waits for PR-016/017).
- **Files/packages:** `rules/ar003/`, `rules/ar014/`, frontend lowering additions, fixtures.
- **Public APIs:** none. · **Data models:** none. · **New deps:** none.
- **Security:** Rule-module grep-guard applies; fixtures inert.
- **Privacy/egress:** none.
- **Tests:** Full rule-harness sets for both (≥1 TP, ≥1 safe control, ≥1 edge each — the §26
  contract, enforced by CI mapping check from here on); FP net rerun.
- **Docs:** Catalog pages incl. per-rule "known limits" sections.
- **Acceptance criteria:** Harness green; both rules fire on the unsafe example repo seeds and
  stay silent on safe controls repo-wide.
- **Release / Migration / Rollback:** in v0.2.0 / none / revert-safe.
- **Depends on:** PR-009 → **Enables:** PR-017 (AR011 reuses failure-mode tables).
- **Demo:** Scan of a tenacity-decorated `requests.post` shows both findings with remediations.
- **Done when:** Acceptance green.

### PR-013 — SARIF reporter and stable fingerprints
*Area: agent-lint output · Complexity: M · Contributor-friendly: no · Artifact: (with v0.2.0)*
- **Value:** Findings flow into GitHub code scanning and any SARIF viewer, with churn-free IDs.
- **Scope:** SARIF 2.1.0 reporter (`--format sarif`): rules metadata, results, locations,
  `partialFingerprints["art/v1"]` (fp_v1 from PR-005), help URIs; SARIF-string sanitization
  (T11); schema validation in CI for every emitted report.
- **Non-goals:** No SARIF upload workflow (Milestone E); no fingerprint algorithm changes.
- **Files/packages:** `agent_reliability/core/reporting/sarif.py` + tests.
- **Public APIs:** `--format sarif`. · **Data models:** SARIF mapping documented as a contract.
- **New deps:** none (hand-rolled writer + schema validation dev-dep).
- **Security:** T11 injection corpus (script tags, markdown, control chars) rendered inert.
- **Privacy/egress:** SARIF carries spans + capped evidence, never full file bodies (T6/TB10).
- **Tests:** Schema validation; golden SARIF files; injection corpus; fingerprint stability
  across reformatting (property test reused from PR-005 at reporter level).
- **Docs:** SARIF integration page; fingerprint stability guarantees (PLAN.md §13).
- **Acceptance criteria:** Emitted SARIF validates against the official 2.1.0 schema for the
  entire fixture corpus.
- **Release / Migration / Rollback:** in v0.2.0 / fingerprint algo versioned `art/v1` / revert-safe.
- **Depends on:** PR-009 → **Enables:** PR-014, PR-033.
- **Demo:** Fixture SARIF loaded in VS Code SARIF viewer showing annotated findings.
- **Done when:** Acceptance green.

### PR-014 — Baselines and severity gating
*Area: agent-lint · Complexity: M · Contributor-friendly: no · Artifact: (with v0.2.0)*
- **Value:** Brownfield repos adopt agent-lint without fixing history first.
- **Scope:** `baseline create` (writes `art-baseline.json`: schema_version, tool versions,
  fingerprint set); scan-time classification `new/existing`; `--fail-on <class>:<severity>`
  (e.g. `new:high`); criticals-not-baselined default with explicit override
  (`baseline.allow_critical`); `baseline migrate` stub wired to fingerprint version (real
  migrations when an algo change ever happens).
- **Non-goals:** No suppression UX (PR-015); no Action integration (Milestone E).
- **Files/packages:** `agent_reliability/lint/baseline.py`, CLI additions.
- **Public APIs:** `baseline create|migrate`, `--fail-on`, baseline file format v1.
- **Data models:** Baseline schema v1 (published).
- **New deps:** none.
- **Security:** Baseline file from scanned repo is data-only (json.loads, schema-validated —
  T5/T10 posture).
- **Privacy/egress:** Baseline stores fingerprints only — no code, no paths beyond repo-relative.
- **Tests:** Create→rescan→all-existing; new-finding classification; fail-on matrix;
  hostile baseline file (oversized, wrong schema) → clean error.
- **Docs:** Adoption guide ("first day on a legacy repo").
- **Acceptance criteria:** Legacy-repo fixture: baseline → clean CI → seeded new defect → exit 1.
- **Release / Migration / Rollback:** in v0.2.0 / baseline schema v1 / revert-safe.
- **Depends on:** PR-013 → **Enables:** PR-034.
- **Demo:** Two-commit walkthrough in docs, executed as an integration test.
- **Done when:** Acceptance green.

### PR-015 — Suppressions with justification and expiry
*Area: agent-lint · Complexity: M · Contributor-friendly: no · Artifact: (with v0.2.0)*
- **Value:** False positives are silenced accountably, not permanently.
- **Scope:** Full suppression semantics (PLAN.md §13): inline `# art: ignore[AR###]
  reason=… expires=…`, project-file scope globs, mandatory-justification (empty reason → `low`
  finding `ART-META-001`), default expiry (180 d) with reactivation, `suppressions report`
  command (age, owner via git blame optional flag).
- **Non-goals:** No org-policy packs (post-v1); no auto-suppression.
- **Files/packages:** suppression module (extends PR-007 parser), CLI additions.
- **Public APIs:** suppression syntax (documented contract), `suppressions report`.
- **Data models:** Suppression entries in project config schema.
- **New deps:** none.
- **Security:** Suppression abuse is self-surfacing (meta-finding + report — T5 residual
  mitigation, spec §14 Q18).
- **Privacy/egress:** none.
- **Tests:** Syntax corpus; expiry reactivation (clock injection); meta-finding on missing
  reason; report golden.
- **Docs:** Suppression policy page.
- **Acceptance criteria:** Expired suppression reactivates at original severity with note;
  unjustified suppression yields meta-finding.
- **Release / Migration / Rollback:** in v0.2.0 / none / revert-safe.
- **Depends on:** PR-007, PR-014 → **Enables:** PR-070 (IDE insertion).
- **Demo:** Suppress → report lists it → expiry passes → finding returns.
- **Done when:** Acceptance green.

### PR-016 — Side-effect classification engine
*Area: agent-lint analysis · Complexity: L · Contributor-friendly: partially (SDK table entries) · Artifact: (with v0.2.0)*
- **Value:** The analyzer knows *which* calls move money, delete data, or write externally —
  the prerequisite for every idempotency/approval rule.
- **Scope:** Layered classifier per PLAN.md Appendix A5: explicit annotations
  (`# art: effect=financial`, decorator kwargs, contract files when present) → known-SDK table
  (stripe, boto3 destructive ops, smtplib/sendgrid, twilio, subprocess, shutil.rmtree, SQL
  execute patterns — initial curated table with per-entry evidence requirements) → name/callsite
  heuristics (low confidence); produces `SideEffect` + `RiskClassification` IR with provenance;
  idempotency-evidence detection (replaysafe usage, idempotency-key kwargs/headers).
- **Non-goals:** No advisor-based classification (Milestone M); no cross-file propagation
  (PR-020 adds intra-file only).
- **Files/packages:** `agent_reliability/lint/classify/`, SDK table as reviewable data file.
- **Public APIs:** annotation syntax (documented); `Enricher` implementation.
- **Data models:** SDK-table format (YAML, schema-validated).
- **New deps:** none.
- **Security:** Table entries require citation (docs URL) in review — prevents FP-inducing
  guesswork (R1).
- **Privacy/egress:** none.
- **Tests:** Classifier corpus per layer; provenance/confidence assertions; annotation parsing;
  table schema validation.
- **Docs:** Classification model page (normative, incl. honest-limits section).
- **Acceptance criteria:** Unsafe example repo's seeded effects all classified with correct
  class + provenance; no classification on the pure-computation corpus.
- **Release / Migration / Rollback:** in v0.2.0 / table format v1 / revert-safe.
- **Depends on:** PR-008 → **Enables:** PR-017, PR-018, PR-019, PR-051.
- **Demo:** IR dump of the order agent shows `charge_customer → financial (source=sdk-table)`.
- **Done when:** Acceptance green.

### PR-017 — Retry-safety rules AR002 and AR011
*Area: agent-lint rules · Complexity: L · Contributor-friendly: yes (with PR-016 landed) · Artifact: (with v0.2.0)*
- **Value:** The toolkit's signature detections: retries that can double-execute side effects.
- **Scope:** AR002 (RetryPolicy wrapping non-idempotent SideEffect without idempotency evidence,
  severity critical/confidence medium) and AR011 (retry wrapping calls with
  timeout/connection-reset failure modes and no verify step before re-execution); dataflow-free
  implementation over IR intersection (call-graph containment within function scope + one level
  of direct call resolution).
- **Non-goals:** Cross-module call graphs; AR012 (needs runtime semantics, Milestone G).
- **Files/packages:** `rules/ar002/`, `rules/ar011/`, fixtures.
- **Public APIs:** none. · **Data models:** none. · **New deps:** none.
- **Security:** standard rule guards.
- **Privacy/egress:** none.
- **Tests:** Harness sets incl. the canonical "tenacity around stripe.Charge.create" TP and
  "same with idempotency_key" safe control; FN regression seeds from real-world postmortems
  (curated into fixtures).
- **Docs:** Catalog pages; "retry safety" concept doc linking to ReplaySafe as remediation.
- **Acceptance criteria:** Harness green; order-agent seed caught; safe (keyed) variant silent.
- **Release / Migration / Rollback:** in v0.2.0 / none / revert-safe.
- **Depends on:** PR-012, PR-016 → **Enables:** PR-044 (docs cross-link), PR-051.
- **Demo:** The README hero screenshot: AR002 on a payment retry.
- **Done when:** Acceptance green.

### PR-018 — Rules AR004, AR010, AR015 (idempotency, audit id, compensation)
*Area: agent-lint rules · Complexity: M · Contributor-friendly: yes · Artifact: (with v0.2.0)*
- **Value:** Side-effect hygiene coverage: keys, audit ids, and compensation paths.
- **Scope:** AR004 (write+ SideEffect without key evidence), AR010 (external write without
  correlation/audit id in scope — logging-call + kwarg heuristics, medium/medium), AR015
  (destructive SideEffect with no compensate/verify registration or transaction context).
- **Non-goals:** Runtime enforcement (that's ReplaySafe).
- **Files/packages:** `rules/ar004/`, `rules/ar010/`, `rules/ar015/`, fixtures.
- **Public APIs/Data models/New deps:** none.
- **Security/Privacy:** standard rule guards; none.
- **Tests:** Harness sets ×3; FP net rerun (these rules are FP-prone — extra safe controls
  required: internal writes, test code detection via path conventions).
- **Docs:** Catalog pages ×3.
- **Acceptance criteria:** Harness green; documented FP posture (what is deliberately not
  flagged) per rule.
- **Release / Migration / Rollback:** in v0.2.0 / none / revert-safe.
- **Depends on:** PR-016 → **Enables:** —.
- **Demo:** Scan output on order agent showing the three findings with distinct remediations.
- **Done when:** Acceptance green.

### PR-019 — Rules AR005 and AR013 (approval gates, swallowed failures)
*Area: agent-lint rules · Complexity: M · Contributor-friendly: yes · Artifact: (with v0.2.0)*
- **Value:** High-risk actions must face a human; failures must not vanish.
- **Scope:** AR005 (financial/destructive SideEffect not dominated by an ApprovalGate in IR path;
  generic detection: approval-callback/`input()`-style/replaysafe-approval patterns — LangGraph
  interrupts arrive in Milestone D); AR013 (broad `except` around tool calls that neither
  re-raises, logs, nor records status).
- **Non-goals:** Framework-specific gate detection (PR-028).
- **Files/packages:** `rules/ar005/`, `rules/ar013/`, ApprovalGate lowering additions to frontend.
- **Public APIs/Data models/New deps:** none.
- **Security/Privacy:** standard; none.
- **Tests:** Harness sets; dominance-analysis unit tests (gate on some paths but not others →
  finding cites the ungated path).
- **Docs:** Catalog pages; approval-gates concept doc.
- **Acceptance criteria:** Harness green incl. partial-path edge cases.
- **Release / Migration / Rollback:** in v0.2.0 / none / revert-safe.
- **Depends on:** PR-016 → **Enables:** PR-028 (LG sharpening).
- **Demo:** Ungated `delete_customer_data` flagged; gated variant silent.
- **Done when:** Acceptance green.

### PR-020 — Rules AR007 and AR009 (context bounds, sensitive dataflow)
*Area: agent-lint rules · Complexity: L · Contributor-friendly: no (dataflow util) · Artifact: (with v0.2.0)*
- **Value:** Context-hygiene and data-exposure coverage; introduces the reusable intra-file
  explicit-dataflow utility.
- **Scope:** Minimal intra-file, explicit-flow dataflow util (assignments, calls, attribute
  chains — no aliasing/implicit flows, documented); AR007 (tool return → message/state append
  without bound: slice/truncate/summarize between); AR009 (secret-source patterns — env access
  with credential-ish names, secret-manager SDK reads, credential attribute names — flowing to
  tool return or model-bound message append; critical/medium).
- **Non-goals:** Inter-procedural or cross-file flow (post-v1); taint framework generality.
- **Files/packages:** `agent_reliability/lint/dataflow.py`, `rules/ar007/`, `rules/ar009/`.
- **Public APIs:** dataflow util is `_internal` (explicitly not plugin API yet).
- **Data models/New deps:** none.
- **Security:** AR009 findings redact matched values in evidence (secret never printed — T6).
- **Privacy/egress:** none.
- **Tests:** Dataflow unit corpus; harness sets; evidence-redaction assertions.
- **Docs:** Catalog pages; dataflow limits documented (honest-capability list).
- **Acceptance criteria:** Harness green; planted canary secret in fixture never appears in any
  output format (ties into §26.9 canary e2e).
- **Release / Migration / Rollback:** in v0.2.0 / none / revert-safe.
- **Depends on:** PR-008, PR-016 → **Enables:** PR-076 (MCP sharpening), Milestone N tuning.
- **Demo:** `os.environ["STRIPE_KEY"]` returned from a tool → AR009 with redacted evidence.
- **Done when:** Acceptance green.

### PR-021 — `explain`, `rules list`, and the generated rule catalog
*Area: agent-lint UX/docs · Complexity: M · Contributor-friendly: yes · Artifact: (with v0.2.0)*
- **Value:** Every finding is educational, offline.
- **Scope:** `agent-lint explain AR###` (renders the rule's docs.md + limits + remediations in
  terminal, fully offline); `rules list [--format json]`; docs-site rule catalog generated from
  rule metadata + docs.md at build time (single source of truth); "writing custom rules" guide
  (the PR-009 harness as contributor entry point).
- **Non-goals:** No advisor hooks (Milestone M adds `--advise` alongside).
- **Files/packages:** CLI additions, `tools/gen_catalog.py`, docs pipeline.
- **Public APIs:** `explain`, `rules list` (+ JSON shape).
- **Data models:** rule-metadata JSON shape (published).
- **New deps:** none.
- **Security:** Rendered markdown is our own content; still escape-stripped by the terminal layer.
- **Privacy/egress:** explain is offline by construction (test-asserted).
- **Tests:** Golden explain output per rule; catalog generation drift check in CI (regenerate →
  no diff).
- **Docs:** The catalog itself + custom-rules guide.
- **Acceptance criteria:** Every shipped rule has a catalog page and explain output; drift check
  green.
- **Release / Migration / Rollback:** in v0.2.0 / none / revert-safe.
- **Depends on:** PR-012…020 (rules exist) → **Enables:** PR-070, external rule contributions.
- **Demo:** `agent-lint explain AR002` full output in docs.
- **Done when:** Acceptance green.

### PR-022 — Performance, DoS, and output-hardening pass
*Area: agent-lint hardening · Complexity: L · Contributor-friendly: no · Artifact: (with v0.2.0)*
- **Value:** The analyzer is fast and safe on hostile or huge repositories.
- **Scope:** Multiprocess scan (process pool, deterministic merge); benchmark suite
  (pytest-benchmark) + 10k-file synthetic repo fixture + CI budget job (advisory until Milestone
  N makes it a gate); complete T2/T11/T12/T13/T25 coverage: pathological fixtures (deep nesting,
  megabyte literals, zip-bomb-adjacent layouts), terminal-escape corpus, report-injection corpus,
  filename torture suite; memory cap monitoring with graceful `scan-limit` degradation.
- **Non-goals:** Distributed scanning; caching between runs **[post-v1 candidate]**.
- **Files/packages:** frontend/engine internals, `fixtures/repos/big-synthetic/` (generated by
  committed script, not committed as files), `fixtures/malicious/` completion.
- **Public APIs:** `--jobs N` flag.
- **Data models/New deps:** none.
- **Security:** This PR closes threat rows T2, T11, T12, T13, T25 for the lint path (PLAN.md §25
  table references these tests).
- **Privacy/egress:** none.
- **Tests:** All corpora above; determinism test (same scan, `--jobs 1` vs `--jobs 8` → identical
  output); benchmark baseline recorded.
- **Docs:** Performance page (budgets, tuning, monorepo advice); troubleshooting page seeded.
- **Acceptance criteria:** 10k-file scan under budget; every malicious fixture handled with a
  diagnostic, never a hang/crash; parallel determinism proven.
- **Release / Migration / Rollback:** in v0.2.0 / none / revert-safe.
- **Depends on:** PR-012…020 → **Enables:** PR-089 (gate-arming).
- **Demo:** `time agent-lint scan big-synthetic/ --jobs 8` in docs.
- **Done when:** Acceptance green.

### PR-023 — ⛳ RELEASE v0.2.0 — useful standalone agent-lint + canonical example
*Area: release/examples · Complexity: M · Contributor-friendly: no · Artifact: **PyPI v0.2.0***
- **Value:** The first release worth blogging about: a real linter for agent code.
- **Scope:** `examples/langgraph-order-agent/` **(plain-Python variant for now — LangGraph
  wiring completes in Milestone D)** with `unsafe/` (seeded with AR001/002/003/004/005/007/009/
  013/014 defects) and `safe/` variants; integration test asserting the documented findings
  exactly; release mechanics; announcement-ready README refresh with the hero demo.
- **Non-goals:** No new rules.
- **Files/packages:** `examples/`, release files.
- **Public APIs:** none changed; v0.2 output formats become compatibility-managed from here.
- **Data models:** none.
- **New deps:** none.
- **Security:** Example secrets are obvious fakes (`sk_test_FAKE…`), asserted by a lint in CI.
- **Privacy/egress:** Example runs offline (mock endpoints only).
- **Tests:** Example-repo integration test (unsafe → exact finding set; safe → clean);
  release-gate checklist.
- **Docs:** Example walkthrough; updated quickstart.
- **Acceptance criteria:** Milestone C exit criteria (PLAN.md §30 row C) all green.
- **Release / Migration / Rollback:** v0.2.0 / none / yank+patch.
- **Depends on:** PR-012…022 → **Enables:** Milestone D (example gains real LangGraph), E (Action
  demos against it), F (ReplaySafe fixes its defects).
- **Demo:** `make demo-lint` scans unsafe example and prints the full finding set.
- **Done when:** v0.2.0 live; smoke green.

---

## Milestone D — LangGraph plugin → ⛳ v0.3.0

> **Status: Committed via the execution wave.** `EXECUTION.md` (E01–E14) resequences and narrows this milestone; the entries below are the full architecture-era decomposition and the reference design for the remaining scope. The wave ships recognition + LG002/LG003/LG006 as internal modules; **plugin entry-point loading (PR-024) and the separate plugin distribution are gated** (plugin-loading gate, PLAN.md §37); remaining LG rules follow validation.

### PR-024 — Plugin loading, compatibility handshake, and isolation
> **Gated:** requires the plugin-loading gate (PLAN.md §37) — a proposed third-party adapter that must ship outside the main distribution, after the Frontend/Rule contracts survive ≥2 public releases.

*Area: agent-core plugins · Complexity: M · Contributor-friendly: no · Artifact: (with v0.3.0)*
- **Value:** Third-party and first-party plugins load safely and predictably.
- **Scope:** Entry-point discovery (`agent_reliability.plugins` group), explicit-enable config
  (installed ≠ silently active for third-party groups; first-party auto-enable list),
  `core_api_version_required` handshake with visible skip diagnostics, per-callback exception
  isolation (PluginError diagnostics), deterministic ordering; plugin author guide. *(Narrow
  infrastructure PR — justified: PR-025 consumes it in the same milestone; without it the
  LangGraph package cannot exist as a separate distribution.)*
- **Non-goals:** No sandboxing (ADR-006 records trust model); no plugin marketplace.
- **Files/packages:** `agent_reliability/core/plugins/loader.py`; docs.
- **Public APIs:** `ArtPlugin` becomes loadable; `CORE_API_VERSION` published; `--plugins`
  CLI listing.
- **Data models:** PluginMeta (finalized).
- **New deps:** none (importlib.metadata).
- **Security:** TB8 enforced: no auto-discovery from scanned repos (loader reads installed
  distributions only); scanned-repo config cannot add plugins (T5 test extended).
- **Privacy/egress:** none.
- **Tests:** Handshake accept/reject matrix; isolation (raising plugin callback → diagnostic);
  determinism; hostile-config plugin-injection attempt fails.
- **Docs:** Plugin author guide (protocol, versioning, testing, publishing).
- **Acceptance criteria:** A toy out-of-tree plugin wheel loads, contributes a rule, and is
  version-gated correctly.
- **Release / Migration / Rollback:** in v0.3.0 / none / revert-safe.
- **Depends on:** PR-007 → **Enables:** PR-025, PR-073, PR-078.
- **Demo:** Toy plugin in `examples/plugin-template/` (doubles as the contributor template).
- **Done when:** Acceptance green; ADR-006 merged.

### PR-025 — LangGraph detection and graph-topology frontend
*Area: langgraph plugin · Complexity: L · Contributor-friendly: no · Artifact: agent-lint-langgraph (at PR-031)*
- **Value:** agent-lint understands LangGraph applications structurally.
- **Scope:** New package `plugins/langgraph-python/`; detection per PLAN.md §15 (imports +
  construction shapes); lowering of literal `StateGraph`/`add_node`/`add_edge`/
  `add_conditional_edges`/`compile` into IR Workflow/Node/Edge; intra-module + direct-import
  name resolution; `UNKNOWN` degradation for dynamic construction (with `info` diagnostics
  naming the reason); declared version range + untested-version diagnostic; LG-rule fixture
  corpus started from real-world example graphs (rewritten as fixtures — verify licenses).
- **Non-goals:** Tools/checkpoints/interrupts lowering (PR-026/027); dynamic graphs (documented
  out of reach).
- **Files/packages:** `plugins/langgraph-python/` (full package skeleton + frontend).
- **Public APIs:** the plugin distribution itself.
- **Data models:** none new (fills IR).
- **New deps:** none at runtime (shape-matching, no langgraph import — ADR/§15); langgraph as
  *test* dependency for fixture validation.
- **Security:** Same parse-only guarantees (T1); plugin runs under PR-024 isolation.
- **Privacy/egress:** none.
- **Tests:** Expected-IR goldens for the corpus; dynamic-construction fixtures → UNKNOWN +
  diagnostics; detection precision corpus (non-LangGraph code that imports langchain → not
  misdetected).
- **Docs:** LangGraph plugin page: what is seen / what is not (normative honest-limits list).
- **Acceptance criteria:** Corpus goldens stable; zero misdetection on the negative corpus.
- **Release / Migration / Rollback:** in v0.3.0 / none / revert-safe.
- **Depends on:** PR-024 → **Enables:** PR-026…030.
- **Demo:** IR dump of the order-agent graph showing nodes/edges/routers.
- **Done when:** Acceptance green.

### PR-026 — LangGraph tools and @tool lowering
*Area: langgraph plugin · Complexity: M · Contributor-friendly: no · Artifact: (with v0.3.0)*
- **Value:** Tool definitions and bindings become IR Tools with schemas.
- **Scope:** `@tool` / `ToolNode` / `tools=[...]` lowering → `Tool` + `ToolCall` IR;
  docstring/annotation schema extraction; side-effect classifier (PR-016) now runs over
  tool bodies with LangGraph provenance; generic rules AR002/003/004/005/013 automatically gain
  LangGraph-aware evidence via merge (PR-007 dedupe).
- **Non-goals:** MCP tools (Milestone K); dynamic tool registries (UNKNOWN).
- **Files/packages:** plugin frontend additions; fixtures.
- **Public APIs/Data models/New deps:** none.
- **Security/Privacy:** standard; none.
- **Tests:** Golden IR for tool corpus; merged-finding tests (generic + framework evidence →
  one finding, framework evidence wins).
- **Docs:** plugin page section.
- **Acceptance criteria:** Order-agent tools appear in IR with correct classes; AR002 finding on
  the LangGraph variant carries graph-node evidence.
- **Release / Migration / Rollback:** in v0.3.0 / none / revert-safe.
- **Depends on:** PR-025 → **Enables:** PR-027…029.
- **Demo:** Same AR002 finding, now naming the graph node and tool binding.
- **Done when:** Acceptance green.

### PR-027 — Checkpointer, interrupt, and recursion-limit lowering + LG001/LG002
*Area: langgraph plugin rules · Complexity: M · Contributor-friendly: partially · Artifact: (with v0.3.0)*
- **Value:** Durability and boundedness of LangGraph apps become visible and enforced.
- **Scope:** Lowering: `compile(checkpointer=…)` (class matched: MemorySaver vs Sqlite/Postgres
  savers), `interrupt_before/after` + `interrupt()` → ApprovalGate IR, literal `recursion_limit`
  → Agent step-limit evidence (AR001 enrichment: silence when a limit exists); rules **LG001**
  (side-effect nodes + no checkpointer) and **LG002** (MemorySaver with financial/destructive
  tools).
- **Non-goals:** Actual durability verification (documented unreachable).
- **Files/packages:** plugin lowering + `rules/lg001/`, `rules/lg002/`.
- **Public APIs/Data models/New deps:** none.
- **Security/Privacy:** standard; none.
- **Tests:** Harness sets for LG001/LG002; AR001-enrichment regression (limit present → silent).
- **Docs:** Catalog pages; checkpointing concept doc.
- **Acceptance criteria:** Harness green; AR001 FP eliminated on recursion-limited fixtures.
- **Release / Migration / Rollback:** in v0.3.0 / none / revert-safe.
- **Depends on:** PR-025 → **Enables:** PR-028, PR-029.
- **Demo:** MemorySaver + charge tool → LG002 critical finding.
- **Done when:** Acceptance green.

### PR-028 — LG003 and LG006 (approval before high-risk tools, router termination)
*Area: langgraph plugin rules · Complexity: M · Contributor-friendly: yes · Artifact: (with v0.3.0)*
- **Value:** Human-gate coverage and loop-exit proofs with graph-level precision.
- **Scope:** **LG003** (no interrupt gate dominating a high-risk tool node; sharpens AR005 with
  path evidence) and **LG006** (conditional router whose path map has no reachable terminal —
  graph-reachability over IR; sharpens AR001).
- **Non-goals:** Runtime routing behavior (static reachability only, stated in docs).
- **Files/packages:** `rules/lg003/`, `rules/lg006/` + graph-reachability util in plugin.
- **Public APIs/Data models/New deps:** none.
- **Security/Privacy:** standard; none.
- **Tests:** Harness sets; reachability unit corpus (cycles, END constants, dynamic targets →
  UNKNOWN → silence with info note).
- **Docs:** Catalog pages.
- **Acceptance criteria:** Harness green incl. dynamic-router safe control (no FP).
- **Release / Migration / Rollback:** in v0.3.0 / none / revert-safe.
- **Depends on:** PR-027 → **Enables:** —.
- **Demo:** Router with no END path → LG006 with the cyclic path printed.
- **Done when:** Acceptance green.

### PR-029 — LG004, LG005, LG007 (context growth, effect-before-checkpoint, resume-unsafe tools)
*Area: langgraph plugin rules · Complexity: L · Contributor-friendly: partially · Artifact: (with v0.3.0)*
- **Value:** The resume-semantics rules — the most agent-specific detections in the toolkit.
- **Scope:** **LG004** (state `messages` append flows with no trim/summarize hook — sharpens
  AR007 using state-schema lowering), **LG005** (side-effect node ordered before checkpoint
  write on a resumable path — sharpens AR006), **LG007** (tool node without retry/timeout policy
  where graph resume re-executes it — sharpens AR011); state-schema lowering (TypedDict/
  pydantic class fields).
- **Non-goals:** Precise resume simulation (static ordering only).
- **Files/packages:** `rules/lg004..lg007/`, plugin lowering additions.
- **Public APIs/Data models/New deps:** none.
- **Security/Privacy:** standard; none.
- **Tests:** Harness sets ×3; order-agent LangGraph variant now shows the full designed finding
  set.
- **Docs:** Catalog pages; "resume semantics" concept doc (the intellectual heart of the plugin).
- **Acceptance criteria:** Harness green; concept doc reviewed as normative.
- **Release / Migration / Rollback:** in v0.3.0 / none / revert-safe.
- **Depends on:** PR-027 → **Enables:** PR-030.
- **Demo:** Charge-before-checkpoint fixture → LG005 with resume-path explanation.
- **Done when:** Acceptance green.

### PR-030 — LangGraph version-compatibility matrix and example completion
*Area: langgraph plugin CI/examples · Complexity: M · Contributor-friendly: no · Artifact: (with v0.3.0)*
- **Value:** R2 (LangGraph churn) is actively managed, not hoped away.
- **Scope:** CI matrix job: fixture corpus validated against min/max of the declared LangGraph
  range (langgraph as test-dep only); untested-newer-version diagnostic e2e test; upgrade
  playbook doc; `examples/langgraph-order-agent/` converted to real LangGraph (unsafe + safe),
  integration test updated to the full LG+AR finding set.
- **Non-goals:** Supporting versions outside the declared range.
- **Files/packages:** CI workflow, examples, docs.
- **Public APIs/Data models/New deps:** none (test-deps pinned).
- **Security/Privacy:** standard; none.
- **Tests:** The matrix itself; example integration test.
- **Docs:** Compatibility policy page (declared range, upgrade playbook).
- **Acceptance criteria:** Matrix green on range endpoints; example asserts exact finding set.
- **Release / Migration / Rollback:** in v0.3.0 / none / revert-safe.
- **Depends on:** PR-025…029 → **Enables:** PR-031.
- **Demo:** CI badge matrix; example scan output in docs.
- **Done when:** Milestone D exit criteria met.

### PR-031 — ⛳ RELEASE v0.3.0 — LangGraph-aware rules
*Area: release · Complexity: S · Contributor-friendly: no · Artifact: **PyPI: + agent-lint-langgraph (v0.3.0)***
- **Value:** The LangGraph community gets a purpose-built linter.
- **Scope:** Release mechanics for the train incl. the new plugin distribution; LangGraph
  quickstart; announcement notes.
- **Non-goals:** Feature changes.
- **Files/packages:** versions, changelog, docs.
- **Public APIs:** plugin API (`ArtPlugin`, IR) now declared *pre-stable for plugin authors*
  (compat policy applies).
- **Data models/New deps:** none.
- **Security/Privacy:** release checklist; none.
- **Tests:** Post-release smoke: clean install `agent-lint[langgraph]` → scan example → LG
  findings.
- **Docs:** changelog, quickstart.
- **Acceptance criteria:** Smoke green.
- **Release / Migration / Rollback:** v0.3.0 / none / yank+patch.
- **Depends on:** PR-030 → **Enables:** Milestone E.
- **Demo:** Quickstart executed verbatim.
- **Done when:** v0.3.0 live.

---

## Milestone E — CI integration → ⛳ v0.4.0

> **Status: Committed via the execution wave.** `EXECUTION.md` (E01–E14) resequences and narrows this milestone; the entries below are the full architecture-era decomposition and the reference design for the remaining scope. The wave ships the minimal Action (path/format/fail-on) in E11; baseline/changed-files inputs arrive with E13.

### PR-032 — Changed-files mode and monorepo scoping
*Area: agent-lint · Complexity: M · Contributor-friendly: no · Artifact: (with v0.4.0)*
- **Value:** PR-sized scans in seconds, honestly scoped.
- **Scope:** `--changed-files <paths|-` and `--working-directory`; cross-file-rule coverage
  notes in report footer when scope is narrowed (no silent narrowing — PLAN.md §20); scope
  resolution interacts correctly with baselines (fingerprints are path-stable).
- **Non-goals:** Git integration beyond reading a path list (the Action computes the diff).
- **Files/packages:** CLI/engine scoping.
- **Public APIs:** the two flags (contract).
- **Data models/New deps:** none.
- **Security/Privacy:** paths validated under root (T4); none.
- **Tests:** Scoped-scan correctness (finding present iff its file in scope); footer-note
  assertions; baseline interaction.
- **Docs:** CI integration page (generic part).
- **Acceptance criteria:** Scoped scan of 1 changed file on the 10k-repo fixture < 5 s.
- **Release / Migration / Rollback:** in v0.4.0 / none / revert-safe.
- **Depends on:** PR-022 → **Enables:** PR-033.
- **Demo:** Timed scoped scan in docs.
- **Done when:** Acceptance green.

### PR-033 — GitHub Action (composite): scan + SARIF upload
*Area: github-action · Complexity: M · Contributor-friendly: no · Artifact: **Action (marketplace at PR-036)***
- **Value:** Two YAML lines put agent-lint findings on every PR.
- **Scope:** `integrations/github-action/action.yml` (composite): pinned hashed install, scan,
  SARIF emit, upload via SHA-pinned `codeql-action/upload-sarif`; inputs `path`, `format`,
  `fail-on`, `config`, `working-directory`; forced `network: deny` + `fail_on_egress_attempt`
  regardless of repo config (TB7); self-test workflow running the action on `examples/`.
- **Non-goals:** Baseline/allow-deny inputs (PR-034); marketplace listing (PR-036).
- **Files/packages:** `integrations/github-action/`, self-test workflow.
- **Public APIs:** action inputs (contract from v0.4.0).
- **Data models:** none.
- **New deps:** none beyond pinned actions.
- **Security:** T21 posture (SHA pins, hashed installs, no third-party marketplace deps);
  minimal permissions documented (`security-events: write` only for upload).
- **Privacy/egress:** Forced-deny is *tested*: a repo config trying to enable egress is ignored
  in Action context.
- **Tests:** Self-test workflow (annotations appear, SARIF validates); forced-deny test;
  failure-threshold test.
- **Docs:** CI integration page (GitHub part) with copy-paste snippet.
- **Acceptance criteria:** Action run on example repo produces code-scanning alerts in this
  repo's Security tab.
- **Release / Migration / Rollback:** in v0.4.0 / none / revert-safe.
- **Depends on:** PR-013, PR-032 → **Enables:** PR-034, PR-035.
- **Demo:** Screenshot: PR annotation of AR002 finding from the self-test.
- **Done when:** Acceptance green.

### PR-034 — Action: baseline mode, rule allow/deny, annotation polish
*Area: github-action · Complexity: S · Contributor-friendly: yes · Artifact: (with v0.4.0)*
- **Value:** Brownfield CI adoption and org policy control in the Action.
- **Scope:** Inputs `baseline`, `rules-allow`, `rules-deny`, `changed-files: auto|all|<list>`
  (auto derives from PR diff via the pinned checkout context); annotation title/description
  polish (severity+confidence visible; help links).
- **Non-goals:** Suppression management from CI (local-only by design).
- **Files/packages:** action.yml, runner script.
- **Public APIs:** the new inputs.
- **Data models/New deps:** none.
- **Security/Privacy:** standard; diff computation uses only the local checkout.
- **Tests:** Self-test matrix over the new inputs; baseline e2e (seeded legacy repo).
- **Docs:** CI page updates; monorepo recipes.
- **Acceptance criteria:** Legacy-repo self-test: baseline suppresses old, catches new.
- **Release / Migration / Rollback:** in v0.4.0 / none / revert-safe.
- **Depends on:** PR-033, PR-014 → **Enables:** —.
- **Demo:** Matrix workflow snippet in docs.
- **Done when:** Acceptance green.

### PR-035 — CI log hygiene and generic-CI documentation
*Area: github-action/security · Complexity: S · Contributor-friendly: no · Artifact: (with v0.4.0)*
- **Value:** CI logs cannot leak what the scanner saw (T20 closed).
- **Scope:** `--quiet-logs` mode (SARIF-only detail; summaries in logs); redaction verified on
  the Action log path; canary e2e (planted fake secret in fixture never appears in workflow
  logs, annotations, or SARIF); generic-CI doc (GitLab/Buildkite recipes using the same CLI +
  exit codes).
- **Non-goals:** Packaging for other CI systems.
- **Files/packages:** CLI flag, action runner, docs, canary tests.
- **Public APIs:** `--quiet-logs`.
- **Data models/New deps:** none.
- **Security:** T20 test row satisfied.
- **Privacy/egress:** the point of the PR.
- **Tests:** Canary e2e in the self-test workflow (greps the actual run log artifact).
- **Docs:** CI page completed; security docs cross-reference.
- **Acceptance criteria:** Canary absent from every CI artifact of the self-test run.
- **Release / Migration / Rollback:** in v0.4.0 / none / revert-safe.
- **Depends on:** PR-033 → **Enables:** PR-036.
- **Demo:** Self-test log excerpt showing redacted summary.
- **Done when:** Acceptance green.

### PR-036 — ⛳ RELEASE v0.4.0 — GitHub Action on the marketplace
*Area: release · Complexity: S · Contributor-friendly: no · Artifact: **Marketplace action + PyPI v0.4.0***
- **Value:** Team-wide enforcement is now a documented, versioned product surface.
- **Scope:** Release train; action tagged `v1` major tag policy (tracking v0.4.x — action
  versioning documented); marketplace listing with SHA-pin guidance; announcement notes.
- **Non-goals:** Feature changes.
- **Files/packages:** versions, tags, marketplace metadata.
- **Public APIs:** action inputs frozen under compat policy.
- **Data models/New deps:** none.
- **Security:** Marketplace listing reviewed against T21 checklist.
- **Privacy/egress:** listing restates forced-deny in CI.
- **Tests:** Post-release: consume the *published* action from a scratch repo (manual runbook +
  scheduled canary workflow).
- **Docs:** changelog; CI quickstart.
- **Acceptance criteria:** Scratch-repo consumption works following only public docs.
- **Release / Migration / Rollback:** v0.4.0 / none / yank+patch, action tag rollback documented.
- **Depends on:** PR-033…035 → **Enables:** Milestone F announce cadence.
- **Demo:** Public scratch-repo run.
- **Done when:** v0.4.0 + action live.

---

## Milestone F — ReplaySafe MVP (SQLite) → ⛳ v0.5.0

> **Status: Planned architecture — implementation requires the ReplaySafe validation gate defined in PLAN.md §37 and EXECUTION.md.** Not automatically committed; may be resequenced, split, or merged when the gate opens.

### PR-037 — replaysafe package: domain, state machine, SQLite ledger
*Area: replaysafe · Complexity: L · Contributor-friendly: no · Artifact: replaysafe (at PR-045)*
- **Value:** The ground truth for side-effect execution exists: a durable, tamper-evident ledger.
- **Scope:** New package `packages/replaysafe/` (top-level import `replaysafe`, zero mandatory
  third-party deps); ActionRecord/ExecutionReceipt/AuditEvent models; status state machine with
  monotonic transitions (PLAN.md §16 diagram is normative); SQLite ledger (WAL,
  `synchronous=FULL` on intent/receipt writes, busy_timeout, 0600 perms); embedded migrations
  (`user_version`); hash-chained audit events + `verify-chain`; NFS/network-filesystem detection
  → warning.
- **Non-goals:** Decorator API (PR-038); claims/locks (PR-039); Postgres (Milestone G).
- **Files/packages:** `packages/replaysafe/src/replaysafe/{model,ledger,audit}/`.
- **Public APIs:** `Ledger` protocol + `SqliteLedger`; status enum (public contract).
- **Data models:** Ledger schema v1 (documented DDL); audit-event chain format.
- **New deps:** none (stdlib sqlite3).
- **Security:** T14 (chain, perms), T18 (0600/0700), T10 (no pickle — JSON-serialized payload
  fields only).
- **Privacy/egress:** Ledger stores arg *hashes* + optional serialized results per policy;
  redaction applied to any stored summaries; fully local.
- **Tests:** State-machine property tests (illegal transitions impossible); migration tests
  (v1 create + forward stub); chain tamper detection; WAL crash-recovery smoke (kill -9 around
  writes); permission-bit tests.
- **Docs:** Ledger design page; schema reference.
- **Acceptance criteria:** Property suite green; tampered row detected; kill -9 leaves a
  recoverable, consistent store.
- **Release / Migration / Rollback:** in v0.5.0 / ledger schema v1 + `replaysafe migrate`
  (no-op v1) / revert-safe pre-release.
- **Depends on:** PR-005 (spans/IDs), PR-006 (redaction) → **Enables:** PR-038…045.
- **Demo:** Python REPL transcript: insert intent, complete, verify chain.
- **Done when:** Acceptance green; ADR-012 merged.

### PR-038 — @action decorator, key derivation, and deduplication
*Area: replaysafe · Complexity: L · Contributor-friendly: no · Artifact: (with v0.5.0)*
- **Value:** The one-decorator promise, stated precisely: same key ⇒ ReplaySafe deduplicates confirmed executions and blocks ambiguous re-execution by default (see PLAN.md §16 claim precision — end-to-end at-most-once additionally requires service-side idempotency, verification, an outbox, compensation, or human resolution).
- **Scope:** `ReplaySafe` entry object; `@rs.action(key=…, effect=…)` and `rs.wrap(fn, …)`;
  key derivation/validation (namespacing `{action}:{key}`, size/charset rules, long-key hashing),
  `args_hash` computation (canonical JSON of bound arguments) + `KeyReuseError`; dedupe path
  (completed → return stored result; `CompletedNoResult` sentinel for non-serializable results,
  `result_omitted` receipts); `key=AUTO` mode with documented caveats; intent-before-effect
  write ordering (§16 normative).
- **Non-goals:** Retry/verify (PR-040); concurrency claims (PR-039 — this PR is single-process
  correct only and says so).
- **Files/packages:** `replaysafe/{api,keys}.py`.
- **Public APIs:** the decorator/wrap surface — **the** product API; reviewed against PLAN.md §16
  target shape.
- **Data models:** none new.
- **New deps:** none.
- **Security:** T15 (collision semantics implemented + tested).
- **Privacy/egress:** result storage policy (`store_results: hash|value|none`, default `hash`).
- **Tests:** Dedupe matrix (same key same args / same key diff args / diff key); serialization
  edge cases; property test: N sequential invocations, one execution; AUTO-mode caveat tests.
- **Docs:** Quickstart (decorate a function, see the ledger); API reference.
- **Acceptance criteria:** Duplicate invocation returns stored result without re-running effect
  (instrumented fixture proves single execution).
- **Release / Migration / Rollback:** in v0.5.0 / none / revert-safe.
- **Depends on:** PR-037 → **Enables:** PR-039…044.
- **Demo:** `charge_customer("o-1")` twice → one charge, one replayed result.
- **Done when:** Acceptance green.

### PR-039 — Claims, leases, and crash sweep (uncertain detection)
*Area: replaysafe · Complexity: L · Contributor-friendly: no · Artifact: (with v0.5.0)*
- **Value:** Concurrent workers and crashed processes cannot double-execute.
- **Scope:** Atomic claim acquisition (single-transaction INSERT-or-claim with lease worker-id +
  expiry); `ActionAlreadyClaimed` + `rs.await_result(key, timeout)`; lease renewal for
  long-running actions; **crash sweep**: expired-lease `started` rows → `uncertain` (on ledger
  open and via `replaysafe sweep`); fencing check at receipt write (stale lease → receipt
  rejected + audit event).
- **Non-goals:** Cross-node locks (Milestone G); verify semantics (PR-040).
- **Files/packages:** `replaysafe/claims.py`, ledger transaction helpers.
- **Public APIs:** `await_result`, `sweep`, claim errors.
- **Data models:** claim/lease columns (schema v1 already includes them — no migration).
- **New deps:** none.
- **Security:** T16 core mitigations land here.
- **Privacy/egress:** none.
- **Tests:** Multi-*process* claim storm (N=8 workers × M=100 duplicate keys ⇒ exactly M
  executions); lease-expiry races with barrier scripting; fencing rejection test; sweep
  correctness.
- **Docs:** Concurrency semantics page (honest single-node scope statement).
- **Acceptance criteria:** Storm test green on all OS runners; stale worker's receipt rejected.
- **Release / Migration / Rollback:** in v0.5.0 / none / revert-safe.
- **Depends on:** PR-038 → **Enables:** PR-040, PR-042, PR-049.
- **Demo:** Two terminal panes racing the same key; one executes, one awaits.
- **Done when:** Acceptance green.

### PR-040 — Retry policies, verify-before-retry, and uncertainty resolution
*Area: replaysafe · Complexity: L · Contributor-friendly: no · Artifact: (with v0.5.0)*
- **Value:** The heart of the safety claim: retries that cannot double-fire, uncertainty that
  cannot be silently ignored.
- **Scope:** `rs.policy(max_attempts, backoff, verify_before_retry)`; bounded re-arm
  (`failed → pending(attempt+1)`); `verify=` hook contract (`Verified(happened|not_happened|
  unknown)` with bounded verify retries); `on_uncertain: block|compensate|require_approval`
  (defaults per effect class: financial/destructive → block); ledger-unavailable behavior
  (fail-closed for effectful classes, configurable fail-open for `read` — §16 normative table
  rows implemented and tested one by one).
- **Non-goals:** Compensation execution (PR-041 wires the hook it calls).
- **Files/packages:** `replaysafe/{retry,verify}.py`.
- **Public APIs:** policy/verify surfaces.
- **Data models:** verify outcomes recorded as audit events.
- **New deps:** none.
- **Security:** The §16 failure-semantics table becomes an executable test matrix (each row =
  at least one test).
- **Privacy/egress:** verify hooks are user code; docs warn about their egress (out of ART's
  boundary, stated).
- **Tests:** Failure-table matrix tests; timeout-after-send → uncertain → verify(happened) →
  completed-no-rerun; verify-unavailable → stays uncertain + escalation event; ledger-outage
  fail-closed test.
- **Docs:** **ReplaySafe semantics doc (normative)** — state machine, failure table, verify
  contract; doc examples executed as tests.
- **Acceptance criteria:** Every row of the failure-semantics table has a green test citing it.
- **Release / Migration / Rollback:** in v0.5.0 / none / revert-safe.
- **Depends on:** PR-039 → **Enables:** PR-041, PR-042, chaos scenarios (H).
- **Demo:** Simulated lost-response charge: second call verifies instead of re-charging.
- **Done when:** Acceptance green; ADR-013 merged.

### PR-041 — Compensation hooks, approval hooks, and force-retry
*Area: replaysafe · Complexity: M · Contributor-friendly: no · Artifact: (with v0.5.0)*
- **Value:** Recovery paths for when prevention isn't enough — always audited.
- **Scope:** `compensate=` hook (bounded retries, `compensation_failed` escalation, `compensated`
  terminal state); `ApprovalProvider` protocol + CLI-prompt and callback providers + file-drop
  provider (headless); `rs.force_retry(key, actor, reason)` + CLI `replaysafe force-retry`
  (confirmation + audit); `on_uncertain: require_approval` end-to-end.
- **Non-goals:** Slack/webhook approval providers (post-v1; protocol admits them).
- **Files/packages:** `replaysafe/{compensate,approval}.py`, CLI part.
- **Public APIs:** hooks + providers + force_retry.
- **Data models:** approval/compensation audit events.
- **New deps:** none.
- **Security:** Force-retry requires actor+reason, is chain-audited (insider-misuse visibility);
  approval decisions attributable.
- **Privacy/egress:** none (providers local).
- **Tests:** Compensation success/failure/retry-exhaustion; approval flow tests (approve/deny/
  timeout→policy); force-retry audit assertions.
- **Docs:** Recovery guide (uncertain-state runbook for operators).
- **Acceptance criteria:** Uncertain financial action demonstrably cannot proceed without
  approval or verify; every override leaves a chain-verified audit trail.
- **Release / Migration / Rollback:** in v0.5.0 / none / revert-safe.
- **Depends on:** PR-040 → **Enables:** PR-043, chaos approval-timeout scenario.
- **Demo:** CLI approval prompt resolving an uncertain charge.
- **Done when:** Acceptance green.

### PR-042 — Crash-recovery and concurrency test harnesses
*Area: replaysafe testing · Complexity: L · Contributor-friendly: no · Artifact: none (test infra)*
- **Value:** The safety claims become continuously proven, not asserted. *(Infrastructure PR —
  justified: consumed immediately as release gates for v0.5.0 and reused by Milestone G backends
  and Milestone H chaos scenarios; narrow scope: test harnesses only.)*
- **Scope:** Child-process kill harness (SIGKILL at scripted points: pre-intent, post-intent
  pre-effect, post-effect pre-receipt, post-receipt) with deterministic scheduling hooks;
  barrier-scripted interleaving framework for claim/verify races; soak runner (configurable
  duration, used nightly); these become required release-gate jobs.
- **Non-goals:** Chaos scenario format (Milestone H builds on different, user-facing machinery).
- **Files/packages:** `packages/replaysafe/tests/harness/`, nightly workflow.
- **Public APIs:** none (internal test API).
- **Data models/New deps:** none.
- **Security:** T16 stress evidence; §26.6/26.7 implemented.
- **Privacy/egress:** none.
- **Tests:** The harness's own meta-tests (kill points actually fire where scripted).
- **Docs:** Testing-strategy page section (how we prove deduplication and
  no-ambiguous-re-execution under crash and concurrency).
- **Acceptance criteria:** All four kill points leave the documented state (`uncertain` where
  designed); interleaving suite green 500× in CI loop mode.
- **Release / Migration / Rollback:** gates v0.5.0 / none / revert-safe (but gates stay).
- **Depends on:** PR-039, PR-040 → **Enables:** PR-045 (release gate), PR-047/049 (reuse).
- **Demo:** CI job summary showing kill-matrix results.
- **Done when:** Gates required on main.

### PR-043 — replaysafe CLI and local trace-store linkage
*Area: replaysafe UX · Complexity: M · Contributor-friendly: partially · Artifact: (with v0.5.0)*
- **Value:** Operators can see and manage execution state without writing SQL.
- **Scope:** CLI: `replaysafe status|inspect <key>|list --status uncertain|sweep|force-retry|
  migrate|verify-chain`; the shared local trace store lands here (SQLite `.art/trace.db`,
  PLAN.md §19: IDs, retention config, `art trace prune|purge|verify-chain|export --format
  otlp-json|json`); ReplaySafe transitions emit trace events with `trace_id` correlation.
- **Non-goals:** OTLP network export (ADR-015); web UI (never, pre-v1).
- **Files/packages:** `replaysafe/cli.py`, `agent_reliability/core/trace/` (core-owned store).
- **Public APIs:** CLI commands; `TraceStore` (core, plugin-facing later).
- **Data models:** trace-store schema v1.
- **New deps:** none.
- **Security:** store perms; redaction-before-persist (T6); chain on audit events.
- **Privacy/egress:** §19 never-recorded list enforced by construction + tests (no source code,
  no env, no absolute paths).
- **Tests:** CLI goldens; retention/prune tests; OTLP-JSON export schema check; correlation
  round-trip (action → trace query).
- **Docs:** Trace & audit page; operator guide.
- **Acceptance criteria:** `replaysafe list --status uncertain` surfaces the kill-harness
  leftovers; export validates.
- **Release / Migration / Rollback:** in v0.5.0 / trace schema v1 / revert-safe.
- **Depends on:** PR-041 → **Enables:** PR-055 (invariants query trace), PR-087.
- **Demo:** Operator session: find uncertain action, inspect, approve, verify chain.
- **Done when:** Acceptance green.

### PR-044 — Framework adapters: LangGraph tools, plain functions, HTTP clients
*Area: replaysafe adapters · Complexity: M · Contributor-friendly: partially · Artifact: (with v0.5.0)*
- **Value:** ReplaySafe drops into existing codebases without restructuring.
- **Scope:** `rs.wrap_langgraph_tool(tool, key=…, effect=…)` (preserves tool schema/signature);
  `rs.wrap_http(client)` (httpx/requests transport wrapper injecting idempotency keys on
  configured routes + claiming around send); example: the order agent's unsafe charge fixed with
  ReplaySafe (the `safe/` variant now uses it — lint AR002 finding disappears, closing the loop);
  docs cross-linking lint findings → ReplaySafe remediations.
- **Non-goals:** MCP wrapper (PR-075); queue consumers (PR-050); n8n (PR-081).
- **Files/packages:** `replaysafe/adapters/`, examples update.
- **Public APIs:** adapter functions.
- **Data models:** none.
- **New deps:** none mandatory (httpx/requests as optional extras `replaysafe[http]`).
- **Security:** wrapped-tool schema fidelity tested (no silent behavior change beyond safety).
- **Privacy/egress:** adapters add no egress; they guard existing egress.
- **Tests:** Adapter unit tests with mock transports; example integration (duplicate webhook
  demo executes charge once); lint-finding-resolution test (AR002 gone in safe variant).
- **Docs:** Adapter guide; "fixing your findings" page.
- **Acceptance criteria:** Order-agent duplicate-delivery demo: one charge, receipts visible.
- **Release / Migration / Rollback:** in v0.5.0 / none / revert-safe.
- **Depends on:** PR-040 → **Enables:** PR-045, Milestone H scenarios.
- **Demo:** `make demo-replay` — duplicate webhook, single charge, ledger printout.
- **Done when:** Acceptance green.

### PR-045 — ⛳ RELEASE v0.5.0 — ReplaySafe SQLite runtime
*Area: release · Complexity: S · Contributor-friendly: no · Artifact: **PyPI: + replaysafe (v0.5.0)***
- **Value:** Retry-safety in an afternoon, installable.
- **Scope:** Release train; ReplaySafe quickstart + semantics doc finalized; kill-matrix and
  storm gates required; announcement notes.
- **Non-goals:** Feature changes.
- **Files/packages:** versions, changelog, docs.
- **Public APIs:** replaysafe API v0.5 under compat policy.
- **Data models:** ledger schema v1 + trace schema v1 released (migration commands live).
- **New deps:** none.
- **Security/Privacy:** release checklist; semantics doc's honesty review (no exactly-once
  language — grep-checked in CI, literally).
- **Tests:** Post-release smoke (clean install → decorator demo).
- **Docs:** changelog; quickstart.
- **Acceptance criteria:** Milestone F exit criteria met.
- **Release / Migration / Rollback:** v0.5.0 / schema v1 baseline / yank+patch.
- **Depends on:** PR-037…044 → **Enables:** Milestones G, H.
- **Demo:** Quickstart verbatim on clean machine.
- **Done when:** v0.5.0 live.

---

## Milestone G — ReplaySafe production adapters → v0.5.x

> **Status: Planned architecture — implementation requires the PostgreSQL/Redis validation gate defined in PLAN.md §37 and EXECUTION.md** (and Milestone F open). Not automatically committed.

### PR-046 — Ledger protocol extraction and backend parity suite
*Area: replaysafe · Complexity: M · Contributor-friendly: no · Artifact: none (test infra)*
- **Value:** Any backend must prove identical semantics before it can ship. *(Infrastructure PR —
  justified: PR-047 consumes it immediately; scope is a test suite + protocol tightening.)*
- **Scope:** Finalize `Ledger`/`LockProvider` protocols from the SQLite implementation
  (documented transaction contracts: what must be atomic); backend-agnostic parity suite: every
  state-machine, claim, sweep, failure-table, kill-matrix, and storm test parameterized over
  backends.
- **Non-goals:** Any new backend (next PR).
- **Files/packages:** `replaysafe/ledger/protocol.py`, parameterized test refactor.
- **Public APIs:** `Ledger` protocol (now the extension contract for third-party backends).
- **Data models:** none.
- **New deps:** none.
- **Security:** protocol documents the atomicity requirements a backend must meet (prevents
  subtly-broken third-party backends claiming compatibility — parity suite is public).
- **Privacy/egress:** none.
- **Tests:** SQLite passes the parameterized suite unchanged (pure refactor proof).
- **Docs:** Backend author guide.
- **Acceptance criteria:** Zero behavior diffs; suite runs via a single `LedgerFixture` seam.
- **Release / Migration / Rollback:** in v0.5.x / none / revert-safe.
- **Depends on:** PR-042, PR-045 → **Enables:** PR-047, PR-048.
- **Demo:** Suite run output listing backend=sqlite.
- **Done when:** Acceptance green.

### PR-047 — PostgreSQL ledger backend
*Area: replaysafe · Complexity: L · Contributor-friendly: no · Artifact: replaysafe[postgres] (v0.5.x)*
- **Value:** Multi-worker production deployments get a shared ledger.
- **Scope:** `PostgresLedger` (`SELECT … FOR UPDATE SKIP LOCKED` claims, advisory-free design);
  Alembic migrations; connection handling (psycopg3 **[confirm at implementation]**, pooling
  guidance not implementation); CI service container running the full parity suite + kill matrix
  + storm tests against Postgres; extras `replaysafe[postgres]`.
- **Non-goals:** Redis (PR-048); HA/failover orchestration (docs point at managed Postgres).
- **Files/packages:** `replaysafe/ledger/postgres.py`, `migrations/`, CI workflow.
- **Public APIs:** DSN-based construction (`ReplaySafe(ledger="postgresql://…")`).
- **Data models:** Postgres schema v1 (parallel to SQLite; documented DDL).
- **New deps:** optional extra: psycopg, alembic.
- **Security:** DSN secrets never logged (redaction test); TLS guidance in docs.
- **Privacy/egress:** Connects only to the user-configured DSN — this is user data
  infrastructure, not ART egress (documented distinction; broker governs *ART-initiated*
  external calls, not the user's own ledger).
- **Tests:** Full parity suite; migration up/down on populated store; concurrent-worker storm
  at higher N (16×500).
- **Docs:** Production deployment guide (sizing, backup, migration runbook).
- **Acceptance criteria:** Parity suite byte-identical semantics vs SQLite; storm green.
- **Release / Migration / Rollback:** v0.5.x / Alembic baseline / revert-safe pre-release;
  post-release rollback = documented downgrade migration.
- **Depends on:** PR-046 → **Enables:** PR-049, PR-050.
- **Demo:** Two hosts (containers) sharing one Postgres ledger, storm-tested.
- **Done when:** Acceptance green.

### PR-048 — Redis lock adapter (lease + fencing)
*Area: replaysafe · Complexity: M · Contributor-friendly: no · Artifact: replaysafe[redis] (v0.5.x)*
- **Value:** Faster claim arbitration for high-throughput multi-node deployments.
- **Scope:** `RedisLockProvider` (SET NX PX leases, fencing tokens validated at receipt write by
  the *ledger*, honest "advisory across nodes" documentation per ADR-014); composition rules
  (locks accelerate, ledger stays authoritative — a lost lock can never cause double-execution,
  only contention); CI service container tests.
- **Non-goals:** Redlock/multi-Redis (explicitly rejected in docs — single Redis or nothing);
  Redis as a ledger (never — no durability claim).
- **Files/packages:** `replaysafe/locks/redis.py`.
- **Public APIs:** `ReplaySafe(ledger=…, locks="redis://…")`.
- **Data models:** none (lock keys documented).
- **New deps:** optional extra: redis.
- **Security:** fencing-token rejection tested under contrived clock skew; DSN redaction.
- **Privacy/egress:** user infrastructure, as PR-047.
- **Tests:** Lock storm with deliberate lease expiry mid-effect → ledger fencing saves
  correctness; parity suite with locks enabled.
- **Docs:** Locking semantics page (what Redis adds, what it can never guarantee).
- **Acceptance criteria:** Correctness preserved under lock loss (the critical test).
- **Release / Migration / Rollback:** v0.5.x / none / revert-safe.
- **Depends on:** PR-046, PR-047 → **Enables:** PR-049.
- **Demo:** Benchmark table: claim latency with/without Redis locks.
- **Done when:** Acceptance green; ADR-014 merged.

### PR-049 — Multi-worker stress/soak suite and misuse detection
*Area: replaysafe hardening · Complexity: M · Contributor-friendly: no · Artifact: (with v0.5.x)*
- **Value:** Production claims are backed by sustained-load evidence; common misconfigurations
  are caught at startup.
- **Scope:** Nightly soak (hours-long, mixed workload, all backends) with invariant checking
  (at-most-once per key, chain integrity); startup misuse detection: SQLite-on-NFS warning,
  multi-node-SQLite detection heuristic (hostname records in ledger → error), clock-skew
  sanity check for leases; operational metrics counters (local only, queryable via CLI).
- **Non-goals:** Metrics exporters (post-v1, would route via broker per ADR-015).
- **Files/packages:** soak workflows, `replaysafe/diagnostics.py`.
- **Public APIs:** `replaysafe doctor`.
- **Data models:** none.
- **New deps:** none.
- **Security:** T16 sustained evidence; misuse detection closes the SQLite-multi-node residual.
- **Privacy/egress:** none.
- **Tests:** Soak meta-tests; misuse-detection unit tests (fake NFS statfs, seeded multi-host
  ledger).
- **Docs:** Operations page (what doctor checks and why).
- **Acceptance criteria:** First full soak green on SQLite+PG; doctor catches all seeded misuses.
- **Release / Migration / Rollback:** v0.5.x / none / revert-safe.
- **Depends on:** PR-047, PR-048 → **Enables:** PR-052.
- **Demo:** `replaysafe doctor` output on a healthy and a misconfigured setup.
- **Done when:** Acceptance green.

### PR-050 — Queue-consumer adapter and duplicate-delivery guide
*Area: replaysafe adapters · Complexity: M · Contributor-friendly: partially · Artifact: (with v0.5.x)*
- **Value:** The most common real-world duplicate source — webhooks/queues — gets a first-class
  recipe.
- **Scope:** Generic consumer adapter `rs.consume(message_id_fn, handler)` (claim on message id,
  ack/nack semantics documented per pattern); worked examples: FastAPI webhook endpoint, celery
  task, SQS-style loop (as *documentation* + example code, only stdlib/optional-extra deps in
  the package itself); duplicate-delivery guide consolidating patterns.
- **Non-goals:** Broker-specific packages (celery/SQS plugins post-v1 if demanded).
- **Files/packages:** `replaysafe/adapters/consumer.py`, `examples/webhook-consumer/`.
- **Public APIs:** `consume` adapter.
- **Data models:** none.
- **New deps:** none mandatory.
- **Security/Privacy:** standard; none.
- **Tests:** Duplicate/out-of-order/redelivery matrix on the adapter; example integration test.
- **Docs:** The guide (a marquee doc — likely the most-searched page).
- **Acceptance criteria:** Matrix green; example demonstrates exactly-one-processing per
  message id under triple delivery.
- **Release / Migration / Rollback:** v0.5.x / none / revert-safe.
- **Depends on:** PR-047 → **Enables:** —.
- **Demo:** Webhook example under a replay flood.
- **Done when:** Acceptance green.

### PR-051 — Rule AR012 (concurrent same-resource modification)
*Area: agent-lint rules · Complexity: L · Contributor-friendly: no · Artifact: (with v0.5.x train)*
- **Value:** The last spec rule lands, informed by real runtime semantics from F/G.
- **Scope:** AR012: same resource-key expression written from concurrently-spawned contexts
  (asyncio.gather/TaskGroup/threads/LangGraph parallel branches) without lock/claim evidence
  (replaysafe claim, explicit locks); conservative implementation (high-precision patterns only,
  confidence medium; documented FN posture — R1 guard).
- **Non-goals:** General race detection (impossible statically; stated).
- **Files/packages:** `rules/ar012/`, concurrency-context lowering in frontend + LG plugin.
- **Public APIs/Data models/New deps:** none.
- **Security/Privacy:** standard; none.
- **Tests:** Harness set with asyncio/threading/LangGraph-parallel fixtures; FP net.
- **Docs:** Catalog page with explicit limits section (longest in the catalog, by design).
- **Acceptance criteria:** Harness green; zero FPs on stdlib-concurrency safe corpus.
- **Release / Migration / Rollback:** v0.5.x / none / revert-safe.
- **Depends on:** PR-016, PR-025 (contexts), F-semantics (remediation content) → **Enables:** —.
- **Demo:** Parallel branch double-writing an order → AR012 recommending claims.
- **Done when:** Acceptance green (completes the AR001–AR015 catalog).

### PR-052 — v0.5.x adapters release and production guide
*Area: release · Complexity: S · Contributor-friendly: no · Artifact: **PyPI v0.5.x (extras)***
- **Value:** ReplaySafe is production-ready beyond a single process.
- **Scope:** Release train for extras; production deployment guide finalized; compatibility
  table (backend × guarantees) published.
- **Non-goals:** Feature changes.
- **Files/packages:** versions, changelog, docs.
- **Public APIs:** extras stabilized.
- **Data models:** none.
- **New deps:** none.
- **Security/Privacy:** checklist; none.
- **Tests:** Post-release smoke incl. `pip install replaysafe[postgres,redis]`.
- **Docs:** changelog; guides.
- **Acceptance criteria:** Milestone G exit criteria met.
- **Release / Migration / Rollback:** v0.5.x / none / yank+patch.
- **Depends on:** PR-046…051 → **Enables:** Milestone H at full strength.
- **Demo:** Production-guide walkthrough on containers.
- **Done when:** Release live.

---

## Milestone H — Agent Chaos MVP → ⛳ v0.6.0

> **Status: Planned architecture — implementation requires the Agent Chaos validation gate defined in PLAN.md §37 and EXECUTION.md.** Not automatically committed. Isolation claims follow the staged model in PLAN.md §17 (application-level guard = best-effort; strong containment = OS-level isolation).

### PR-053 — Scenario schema, loader, determinism core, and simulation boundary
*Area: agent-chaos · Complexity: L · Contributor-friendly: no · Artifact: agent-chaos (at PR-060)*
- **Value:** The chaos foundation: reproducible scenarios with an enforced, honestly-staged
  isolation boundary (application-level guard = best-effort containment; OS-level isolation =
  the strong boundary — PLAN.md §17).
- **Scope:** New package `packages/agent-chaos/`; scenario YAML schema v1 (PLAN.md §17) +
  loader/validator; seeded RNG plumbing (single seed → all fault schedules); target loading
  (`kind: python|command` entrypoints — LangGraph convenience in PR-057); **simulation boundary**:
  `mode: simulation` (socket-guard aborts on any real connection; registered test doubles only)
  and `mode: sandbox` (explicit loopback allowlist); no production mode exists (grep-test:
  the string is rejected by the schema).
- **Non-goals:** Faults (PR-054), invariants (PR-055), CLI (PR-056).
- **Files/packages:** `agent_reliability/chaos/{scenario,seed,boundary}/`, schema in
  `docs/schemas/scenario-v1.json`.
- **Public APIs:** scenario format v1 (contract).
- **Data models:** scenario schema v1.
- **New deps:** none new (pyyaml shared).
- **Security:** T-row for chaos (R8): boundary enforcement is the release-gating property;
  hostile-scenario fixtures (huge, recursive refs) → clean errors.
- **Privacy/egress:** simulation mode asserts zero egress by construction.
- **Tests:** Schema validation corpus; seed determinism (same seed → identical schedules);
  boundary tests (attempted real socket → abort with diagnostic); sandbox allowlist tests.
- **Docs:** Scenario format reference (normative).
- **Acceptance criteria:** Boundary abort proven; schema corpus green.
- **Release / Migration / Rollback:** in v0.6.0 / scenario schema v1 / revert-safe.
- **Depends on:** PR-006, PR-010 (guard reuse) → **Enables:** PR-054…059.
- **Demo:** Scenario file that tries `mode: production` → validation error.
- **Done when:** Acceptance green.

### PR-054 — Fault-adapter framework, first faults, and the scripted model stub
*Area: agent-chaos · Complexity: L · Contributor-friendly: partially (new faults later) · Artifact: (with v0.6.0)*
- **Value:** The first injectable failures, plus the stub that makes agent runs deterministic.
- **Scope:** `FaultAdapter` protocol (patch/arm/disarm lifecycle, seeded schedules, injection
  points: tool_call/http/llm/clock); faults: `rate_limit_429`, `timeout_before_action`,
  `timeout_after_send` (the uncertainty-maker), `malformed_json`, `partial_response`;
  **scripted model stub**: records/replays or hand-authors tool-call sequences (the `llm`
  injection point), enabling fully deterministic agent loops; httpx/requests transport doubles.
- **Non-goals:** Remaining catalog (PR-057/058); model-backed mode (PR-058 note; gated).
- **Files/packages:** `agent_reliability/chaos/{faults,stub}/`.
- **Public APIs:** `FaultAdapter` (plugin-facing — plugins may add faults per §12).
- **Data models:** stub transcript format (JSON, versioned).
- **New deps:** none mandatory.
- **Security:** doubles never dial out (boundary applies inside adapters too — tested).
- **Privacy/egress:** none.
- **Tests:** Per-fault unit tests (schedule honored, seeded reproducibility); stub replay
  fidelity; adapter lifecycle (disarm restores cleanly — no patch leakage between scenarios).
- **Docs:** Fault catalog page (grows with PR-057/058); stub authoring guide.
- **Acceptance criteria:** A scripted agent loop + `timeout_after_send` reproduces byte-identical
  reports across 2 runs and 3 OSes.
- **Release / Migration / Rollback:** in v0.6.0 / transcript v1 / revert-safe.
- **Depends on:** PR-053 → **Enables:** PR-055…058.
- **Demo:** Deterministic replay of a flaky-API story.
- **Done when:** Acceptance green.

### PR-055 — Invariant engine and built-in invariants
*Area: agent-chaos · Complexity: L · Contributor-friendly: partially · Artifact: (with v0.6.0)*
- **Value:** Scenarios don't just inject chaos — they *prove properties* under it.
- **Scope:** Invariant compilation + post-run evaluation over (trace stream, ReplaySafe ledger,
  counters) per PLAN.md §17; built-ins: `<action>_occurs_at_most_once`, `maximum_steps`,
  `maximum_cost_usd` (config price table), `uncertain_<class>_requires_human`,
  `no_secret_is_returned_to_model` (canary strings); custom invariants via project
  `invariants.py` callables on read-only `ChaosRun` view; evidence linkage (violations cite
  event ids).
- **Non-goals:** Streaming/online evaluation (post-run is the contract).
- **Files/packages:** `agent_reliability/chaos/invariants/`.
- **Public APIs:** invariant names in scenario schema; `ChaosRun` read view.
- **Data models:** invariant-result records in the report schema.
- **New deps:** none.
- **Security:** custom invariants are project code run *by the user's choice* (same trust as
  their tests — documented); canary machinery reused from §26.9.
- **Privacy/egress:** none.
- **Tests:** Per-invariant TP/TN pairs (violating + conforming runs); evidence-id assertions;
  custom-invariant loading tests.
- **Docs:** Invariant reference (normative), incl. how to write custom ones.
- **Acceptance criteria:** Every built-in has a demonstrated catch and a demonstrated pass.
- **Release / Migration / Rollback:** in v0.6.0 / report schema v1 (PR-056) / revert-safe.
- **Depends on:** PR-043 (trace), PR-054 → **Enables:** PR-056…059.
- **Demo:** `payment_occurs_at_most_once` catching an unprotected retry (and passing on the
  ReplaySafe-protected variant).
- **Done when:** Acceptance green.

### PR-056 — agent-chaos CLI, report format, and reproducibility gate
*Area: agent-chaos · Complexity: M · Contributor-friendly: no · Artifact: (with v0.6.0)*
- **Value:** Chaos runs become a CI-consumable product surface.
- **Scope:** `agent-chaos run <scenarios> [--seed N] [--format text|json|sarif]`,
  `agent-chaos list`, `agent-chaos validate`; ChaosReport schema v1 (verdicts, invariant
  evaluations + evidence, fault schedule, seed, environment digest, normalized timestamps);
  reproducibility CI gate (every shipped scenario ×2 same-seed → identical reports); exit codes
  (0 pass / 1 invariant violation / 2 config / 3 internal).
- **Non-goals:** pytest plugin (PR-059); HTML reports (post-v1).
- **Files/packages:** `agent_reliability/chaos/{cli,report}/`, `docs/schemas/chaos-report-v1.json`.
- **Public APIs:** CLI + report schema (contracts).
- **Data models:** report schema v1.
- **New deps:** none.
- **Security:** report strings pass the same sanitization as findings (T11/T12).
- **Privacy/egress:** reports contain no source code; env digest is hashes.
- **Tests:** CLI goldens; schema validation; the reproducibility gate itself; SARIF mapping
  validation.
- **Docs:** Chaos CLI reference; CI recipe.
- **Acceptance criteria:** Reproducibility gate green on all shipped scenarios.
- **Release / Migration / Rollback:** in v0.6.0 / report schema v1 / revert-safe.
- **Depends on:** PR-054, PR-055 → **Enables:** PR-057…060.
- **Demo:** CI job output: scenario verdict table.
- **Done when:** Acceptance green.

### PR-057 — Fault catalog II: delivery, crash, checkpoint, concurrency faults
*Area: agent-chaos faults · Complexity: L · Contributor-friendly: partially · Artifact: (with v0.6.0)*
- **Value:** The failure modes that motivated the whole toolkit become injectable.
- **Scope:** Faults: `duplicate_delivery` (webhook/message replay), `process_crash` (child-process
  target harness + scripted SIGKILL — reuses PR-042 machinery), `stale_checkpoint` (checkpointer
  wrapper serving N-1 state), `missing_memory_store`, `two_concurrent_workers` (process-pair
  driver), `delayed_success`, `database_lock`; LangGraph target convenience
  (`kind: langgraph`, wraps compiled graphs with the stub + checkpointer wrapper).
- **Non-goals:** Ledger/approval faults (PR-058).
- **Files/packages:** `chaos/faults/` additions.
- **Public APIs:** fault names in schema (documented).
- **Data models/New deps:** none.
- **Security:** crash harness confined to child processes of the run (never signals outside its
  tree — tested).
- **Privacy/egress:** none.
- **Tests:** Per-fault TP tests incl. the flagship: duplicate_delivery + unprotected agent →
  invariant violation; + ReplaySafe → pass.
- **Docs:** Fault catalog completion (part 2 in PR-058).
- **Acceptance criteria:** Flagship pair (violation/pass) green and reproducible.
- **Release / Migration / Rollback:** in v0.6.0 / none / revert-safe.
- **Depends on:** PR-056, PR-042 → **Enables:** PR-059.
- **Demo:** The duplicate-webhook story, end to end, seeded.
- **Done when:** Acceptance green.

### PR-058 — Fault catalog III: context, injection, ledger, approval, model-behavior faults
*Area: agent-chaos faults · Complexity: M · Contributor-friendly: partially · Artifact: (with v0.6.0)*
- **Value:** Catalog completeness per spec §4.5, including the model-behavior faults.
- **Scope:** Faults: `context_growth` (inflated tool outputs), `tool_result_injection`
  (canary payloads in tool results — pairs with `no_secret…`/action-canary invariants),
  `ledger_outage` (ledger proxy raising — proves fail-closed), `approval_timeout`,
  `repeated_tool_call` and `changed_tool_args` (scripted-stub behaviors); optional
  **model-backed mode** (local model via Egress Broker, marked non-reproducible, never a CI
  gate by default — documented posture).
- **Non-goals:** Remote-model chaos (broker allows it technically; docs discourage; not tested
  as a product path pre-v1).
- **Files/packages:** `chaos/faults/` completion; stub extensions.
- **Public APIs:** fault names; `mode: model-backed` scenario key.
- **Data models/New deps:** none.
- **Security:** injection canaries are inert markers (no real payloads shipped); ledger-outage
  fault proves T-row fail-closed behavior under test.
- **Privacy/egress:** model-backed mode goes through the broker like any advisor call.
- **Tests:** Per-fault TP/TN; fail-closed proof test (ledger outage + financial action → block,
  not execute); canary-flow tests.
- **Docs:** Fault catalog complete; model-backed mode caveats page.
- **Acceptance criteria:** Spec §4.5 fault list fully mapped (each item → fault name or explicit
  documented deferral — none expected).
- **Release / Migration / Rollback:** in v0.6.0 / none / revert-safe.
- **Depends on:** PR-057 → **Enables:** PR-059, PR-076.
- **Demo:** Injection canary caught by invariant before reaching an action.
- **Done when:** Acceptance green.

### PR-059 — pytest plugin and ReplaySafe acceptance scenarios
*Area: agent-chaos integration · Complexity: M · Contributor-friendly: partially · Artifact: (with v0.6.0)*
- **Value:** Chaos lives where tests live; ReplaySafe's guarantees become shipped scenarios.
- **Scope:** pytest plugin (`@pytest.mark.chaos(scenario=…)`, `chaos_env`/`chaos_report`
  fixtures, seed from pytest `-p chaos --chaos-seed`); shipped scenario library
  `scenarios/replaysafe/` (crash-between-intent-and-receipt, duplicate delivery, verify
  unavailable, ledger outage, approval timeout — doubling as ReplaySafe acceptance tests in its
  CI); chaos-testing guide.
- **Non-goals:** xdist parallel chaos (documented unsupported v1).
- **Files/packages:** `agent_reliability/chaos/pytest_plugin.py`, `scenarios/`.
- **Public APIs:** pytest marker/fixture names (contract).
- **Data models:** none.
- **New deps:** pytest (already); plugin entry point.
- **Security/Privacy:** standard; none.
- **Tests:** `pytester`-based plugin tests; scenario library runs in both chaos CI and
  replaysafe CI (cross-package integration in `tests/`).
- **Docs:** Chaos testing guide (the H marquee doc); pytest recipes.
- **Acceptance criteria:** Scenario library green under the reproducibility gate; plugin
  UX validated by example project.
- **Release / Migration / Rollback:** in v0.6.0 / none / revert-safe.
- **Depends on:** PR-056…058 → **Enables:** PR-060.
- **Demo:** `pytest -m chaos` output in the example repo.
- **Done when:** Acceptance green.

### PR-060 — ⛳ RELEASE v0.6.0 — Agent Chaos MVP
*Area: release · Complexity: S · Contributor-friendly: no · Artifact: **PyPI: + agent-chaos (v0.6.0)***
- **Value:** Resilience proofs in CI, installable.
- **Scope:** Release train; chaos quickstart; announcement notes.
- **Non-goals:** Feature changes.
- **Files/packages:** versions, changelog, docs.
- **Public APIs:** scenario/report schemas + CLI + pytest surface under compat policy.
- **Data models:** scenario v1, report v1, transcript v1 released.
- **New deps:** none.
- **Security/Privacy:** checklist; boundary docs prominent in release notes.
- **Tests:** Post-release smoke (clean install → shipped scenario → verdict).
- **Docs:** changelog; quickstart.
- **Acceptance criteria:** Milestone H exit criteria met.
- **Release / Migration / Rollback:** v0.6.0 / schemas v1 / yank+patch.
- **Depends on:** PR-053…059 → **Enables:** Milestone I.
- **Demo:** Quickstart verbatim.
- **Done when:** v0.6.0 live.

---

## Milestone I — Agent Contract MVP → ⛳ v0.7.0

> **Status: Planned architecture — implementation requires the Agent Contract validation gate defined in PLAN.md §37 and EXECUTION.md.** Not automatically committed.

### PR-061 — Contract format, schema, and parser
*Area: agent-contract · Complexity: M · Contributor-friendly: no · Artifact: agent-contract (at PR-067)*
- **Value:** A human-readable, machine-checkable contract language for tools.
- **Scope:** New package `packages/agent-contract/`; `toolcontract` YAML format v1 (PLAN.md §18)
  + JSON Schema + parser/validator; JSON-Schema handling for input/output schemas (inline +
  `$ref` local files only — no remote refs, ever); contract linting (missing side_effect class,
  draft flags).
- **Non-goals:** Runner (PR-062); MCP (PR-074).
- **Files/packages:** `agent_reliability/contract/{model,parse}/`,
  `docs/schemas/toolcontract-v1.json`.
- **Public APIs:** contract format v1 (contract, literally).
- **Data models:** contract schema v1.
- **New deps:** jsonschema **[runtime dep for this package]**.
- **Security:** No remote `$ref` resolution (SSRF-class guard, tested); size/depth caps on
  schemas (T3-adjacent).
- **Privacy/egress:** none.
- **Tests:** Format corpus (valid/invalid); remote-ref rejection; golden parse output.
- **Docs:** Contract format reference (normative).
- **Acceptance criteria:** Corpus green; format doc complete enough to author by hand.
- **Release / Migration / Rollback:** in v0.7.0 / schema v1 / revert-safe.
- **Depends on:** PR-005, PR-006 → **Enables:** PR-062…066.
- **Demo:** Annotated example contract in docs.
- **Done when:** Acceptance green.

### PR-062 — `agent-contract init` and the core test runner
*Area: agent-contract · Complexity: L · Contributor-friendly: no · Artifact: (with v0.7.0)*
- **Value:** Contracts are drafted from real tools and enforced against them.
- **Scope:** `init` (introspect a Python tools directory — function signatures, type hints,
  docstrings → draft contracts with `draft: true`, classification left `unknown`); `test`
  runner core: input-schema round-trip, required-field enforcement, enum rejection, response
  shape on `examples`; runner executes *user tools in the user's environment by explicit
  command* (this is test execution, not scanning — trust model documented: contract testing
  runs your code, lint never does).
- **Non-goals:** Timeout/error/annotation checks (PR-063); fuzz (PR-065).
- **Files/packages:** `agent_reliability/contract/{init,runner}/`, CLI.
- **Public APIs:** `init`, `test` commands.
- **Data models:** test-result records (report schema in PR-066).
- **New deps:** none.
- **Security:** The lint-vs-contract trust distinction is loud in docs and CLI help (`test`
  refuses to run on a directory lacking a `toolcontracts/` marker without `--i-know`); example
  invocation sandbox guidance.
- **Privacy/egress:** runner calls only the tools the user pointed it at.
- **Tests:** Init drafts match goldens for a tool corpus; runner TP/TN matrix (conforming and
  seeded-violation tools).
- **Docs:** Getting-started for contracts.
- **Acceptance criteria:** Seeded violations all caught; conforming corpus clean.
- **Release / Migration / Rollback:** in v0.7.0 / none / revert-safe.
- **Depends on:** PR-061 → **Enables:** PR-063…066.
- **Demo:** `init` then `test` on the example order-agent tools.
- **Done when:** Acceptance green.

### PR-063 — Timeout, error-contract, and annotation conformance testing
*Area: agent-contract · Complexity: M · Contributor-friendly: partially · Artifact: (with v0.7.0)*
- **Value:** The reliability half of contracts: how tools *fail* is now tested.
- **Scope:** Timeout-budget checks (declared `timeout_ms` honored; injected-clock where the tool
  accepts one, wall-clock cap otherwise); error-contract conformance (declared codes,
  retriability flags, `retry_after` presence, structured error shape); consistency checks:
  `idempotency.supported ⇒ key param in schema`, `side_effect ∈ {financial,destructive} ⇒
  approval_required` policy option, permission declarations present; side-effect annotation
  presence enforcement mode (`--require-annotations`).
- **Non-goals:** Actually *verifying* idempotency at runtime (that's ReplaySafe + chaos; docs
  cross-link).
- **Files/packages:** runner extensions.
- **Public APIs:** new checks + flags.
- **Data models/New deps:** none.
- **Security/Privacy:** standard; none.
- **Tests:** Per-check TP/TN pairs; consistency-rule matrix.
- **Docs:** Check reference (each check: what/why/limits).
- **Acceptance criteria:** Matrix green.
- **Release / Migration / Rollback:** in v0.7.0 / none / revert-safe.
- **Depends on:** PR-062 → **Enables:** PR-064, PR-066.
- **Demo:** Tool with undeclared error code caught in CI output.
- **Done when:** Acceptance green.

### PR-064 — Contract diff engine (breaking-change detection)
*Area: agent-contract · Complexity: M · Contributor-friendly: partially · Artifact: (with v0.7.0)*
- **Value:** Tool and MCP-server upgrades stop breaking agents silently.
- **Scope:** `agent-contract diff <old> <new>` over contracts or directories; change taxonomy:
  **breaking** (removed/renamed field, type change, narrowed enum, new required input, removed
  error code an agent may rely on), **risky** (widened permissions, side-effect class escalation,
  timeout increase past threshold, idempotency downgrade), **compatible**; exit code keyed to
  breaking; report formats text/json.
- **Non-goals:** Semantic-equivalence reasoning (structural diff only, stated).
- **Files/packages:** `agent_reliability/contract/diff.py`.
- **Public APIs:** `diff` command + taxonomy (documented contract).
- **Data models:** diff-report schema.
- **New deps:** none.
- **Security:** risky-class exists precisely for the security-relevant changes (permission
  widening, effect escalation) — P3's headline feature.
- **Privacy/egress:** none.
- **Tests:** Taxonomy matrix (every class ≥2 cases); directory-level diff; golden reports.
- **Docs:** Diff taxonomy reference; CI recipe (fail on breaking).
- **Acceptance criteria:** Seeded v1→v2 corpus classified 100% correctly.
- **Release / Migration / Rollback:** in v0.7.0 / none / revert-safe.
- **Depends on:** PR-061 → **Enables:** PR-074 (MCP diffs), PR-066.
- **Demo:** Widened-scope diff output (the P3 success moment from PLAN.md §4).
- **Done when:** Acceptance green.

### PR-065 — Schema-driven fuzzer
*Area: agent-contract · Complexity: L · Contributor-friendly: no · Artifact: (with v0.7.0)*
- **Value:** Error contracts survive hostile inputs, not just happy paths.
- **Scope:** `agent-contract fuzz <target>` — hypothesis-powered generation from input schemas:
  boundary values, type confusion, missing/extra fields, oversized strings, malformed framing;
  assertions: structured errors only (no crashes/hangs/stack dumps in payloads), bounded
  response size/time; seeded + reproducible (`--seed`, failing cases minimized and written as
  regression files); loopback-only default, `--allow-remote <host>` double-confirmation (TB9).
- **Non-goals:** Coverage-guided fuzzing; protocol fuzzing below the tool-call layer.
- **Files/packages:** `agent_reliability/contract/fuzz.py`.
- **Public APIs:** `fuzz` command.
- **Data models:** fuzz-report + regression-case format.
- **New deps:** hypothesis (runtime dep of this package).
- **Security:** TB9 bounds (size/time caps on responses); remote-host friction; fuzzing is
  *authorized testing* framing in docs (target must be yours — stated policy).
- **Privacy/egress:** loopback default; remote requires explicit opt-in.
- **Tests:** Fuzzer catches seeded bugs (crash on huge string, unstructured error) in a fixture
  tool server; reproducibility of failing cases; self-fuzz of the contract parser.
- **Docs:** Fuzzing guide + responsible-use note.
- **Acceptance criteria:** Seeded-bug corpus fully found within budgeted examples.
- **Release / Migration / Rollback:** in v0.7.0 / none / revert-safe.
- **Depends on:** PR-062 → **Enables:** PR-074.
- **Demo:** Fuzz run minimizing a crashing input to a 2-line regression file.
- **Done when:** Acceptance green.

### PR-066 — Contract→IR frontend, pytest integration, and CI reports
*Area: agent-contract integration · Complexity: M · Contributor-friendly: partially · Artifact: (with v0.7.0)*
- **Value:** One contract artifact now serves lint, tests, and CI dashboards.
- **Scope:** Frontend lowering contracts into IR (Tool + classifications with
  `source=contract`, authoritative) — agent-lint confidence upgrades (AR002 high-confidence when
  contract says `idempotency.supported: false`); pytest integration
  (`@pytest.mark.contract`, auto-discovery of `toolcontracts/`); report formats json/junit/sarif
  for `test`/`diff`/`fuzz`.
- **Non-goals:** MCP (next milestone).
- **Files/packages:** contract frontend (registered via plugin mechanics), pytest plugin,
  reporters.
- **Public APIs:** marker + report schemas.
- **Data models:** report schema v1 (shared shape with chaos where sensible).
- **New deps:** none.
- **Security/Privacy:** standard sanitization on all report paths; none.
- **Tests:** Lint-confidence upgrade tests (same fixture ± contract → confidence delta);
  `pytester` suite; junit/sarif validation.
- **Docs:** "One contract, three tools" concept page; CI recipes.
- **Acceptance criteria:** Confidence-upgrade demo green; reports validate.
- **Release / Migration / Rollback:** in v0.7.0 / report schema v1 / revert-safe.
- **Depends on:** PR-063, PR-064, PR-024 → **Enables:** PR-067, PR-073.
- **Demo:** AR002 finding citing the tool's own contract as evidence.
- **Done when:** Acceptance green.

### PR-067 — ⛳ RELEASE v0.7.0 — Tool contracts MVP
*Area: release · Complexity: S · Contributor-friendly: no · Artifact: **PyPI: + agent-contract (v0.7.0)***
- **Value:** Contract testing for the tool-calling world, installable.
- **Scope:** Release train; contract quickstart; announcement notes.
- **Non-goals:** Feature changes.
- **Files/packages:** versions, changelog, docs.
- **Public APIs:** contract format + CLI + taxonomy under compat policy.
- **Data models:** toolcontract v1 released.
- **New deps:** none.
- **Security/Privacy:** checklist; none.
- **Tests:** Post-release smoke.
- **Docs:** changelog; quickstart.
- **Acceptance criteria:** Milestone I exit criteria met.
- **Release / Migration / Rollback:** v0.7.0 / schema v1 / yank+patch.
- **Depends on:** PR-061…066 → **Enables:** Milestones J, K.
- **Demo:** Quickstart verbatim.
- **Done when:** v0.7.0 live.

---

## Milestone J — VS Code integration → ⛳ v0.8.0

> **Status: Planned architecture — implementation requires the VS Code validation gate defined in PLAN.md §37 and EXECUTION.md.** Not automatically committed.

### PR-068 — `agent-lint serve --lsp` language service
*Area: agent-lint LSP · Complexity: L · Contributor-friendly: no · Artifact: (with v0.8.0)*
- **Value:** Editor-grade latency for the same engine, with zero duplicated logic.
- **Scope:** LSP server over stdio (diagnostics on open/save, incremental single-file re-scan
  with project-context cache; code-action, hover, and command endpoints the extension will
  consume); document-version handling; graceful degradation on huge files (scan-limit
  diagnostics as editor warnings).
- **Non-goals:** The extension itself (PR-069); full workspace watching (save-triggered v1).
- **Files/packages:** `agent_reliability/lint/lsp/`.
- **Public APIs:** LSP surface (documented subset; the extension is the only supported client
  pre-v1).
- **Data models:** none.
- **New deps:** pygls **[ASSUMPTION: confirm at implementation]**.
- **Security:** stdio only (no TCP listener); same parse-only guarantees.
- **Privacy/egress:** offline; socket-guard job covers the LSP tests.
- **Tests:** LSP protocol tests (scripted client transcripts); latency budget test (single-file
  re-scan < 300 ms on fixture project **[ASSUMPTION]**); crash-isolation (bad file → diagnostic,
  server lives).
- **Docs:** LSP page (for future third-party editor clients).
- **Acceptance criteria:** Transcript suite green; latency budget met.
- **Release / Migration / Rollback:** in v0.8.0 / none / revert-safe.
- **Depends on:** PR-022 → **Enables:** PR-069…071.
- **Demo:** `agent-lint serve --lsp` driven by a scripted client showing live diagnostics.
- **Done when:** Acceptance green.

### PR-069 — VS Code extension: scaffold, diagnostics, privacy notice
*Area: vscode · Complexity: M · Contributor-friendly: no · Artifact: extension (marketplace at PR-071)*
- **Value:** Findings appear inline where developers live.
- **Scope:** pnpm sub-workspace `integrations/vscode/`; extension: binary discovery (venv →
  `art.path` setting → PATH; offers pip command if missing, never auto-installs), LSP client
  wiring, diagnostics with `AR###` codes + doc links, "ART: Run Scan" command, first-activation
  privacy notice (local-only, no telemetry), status bar item.
- **Non-goals:** Quick fixes/suppressions (PR-070); panel/config UI (PR-071).
- **Files/packages:** `integrations/vscode/`, CI job for TS lint/test/build.
- **Public APIs:** extension settings (`art.path`, `art.enable`).
- **Data models:** none.
- **New deps:** TS toolchain (isolated workspace); vscode-languageclient.
- **Security:** T22 posture: no network imports (CI bundle audit armed now), minimal deps,
  publisher 2FA documented.
- **Privacy/egress:** the notice + no-telemetry assertion (VS Code telemetry APIs unused —
  audit-tested).
- **Tests:** Extension unit tests; `@vscode/test-electron` smoke with stub LSP transcript;
  bundle audit.
- **Docs:** VS Code page (install, settings, troubleshooting).
- **Acceptance criteria:** Smoke shows a diagnostic on the example repo in CI.
- **Release / Migration / Rollback:** in v0.8.0 / none / revert-safe.
- **Depends on:** PR-068 → **Enables:** PR-070, PR-071.
- **Demo:** Screenshot: AR002 squiggle with hover card.
- **Done when:** Acceptance green.

### PR-070 — Explanations, quick fixes, and suppression insertion
*Area: vscode · Complexity: M · Contributor-friendly: partially · Artifact: (with v0.8.0)*
- **Value:** The full finding workflow — understand, fix, or accountably suppress — in-editor.
- **Scope:** Hover/code-action "Explain" rendering bundled rule docs (offline); quick-fix code
  actions for `safe`-class deterministic fixes (server-computed edits); `suggestion`-class shown
  behind explicit acceptance; suppression-insertion action generating
  `# art: ignore[…] reason="TODO"` with cursor placed in reason.
- **Non-goals:** AI-anything (advisor never ships in the extension pre-v1 — ADR-020 note).
- **Files/packages:** extension + LSP endpoints.
- **Public APIs:** none new beyond LSP additions.
- **Data models/New deps:** none.
- **Security:** fixes are server-computed deterministic edits; extension applies workspace edits
  only via VS Code API.
- **Privacy/egress:** all offline.
- **Tests:** Code-action transcript tests; fix-application round-trip (re-scan → finding gone);
  suppression-insertion goldens.
- **Docs:** VS Code page updates.
- **Acceptance criteria:** AR003 quick fix applies and clears in one cycle on the fixture.
- **Release / Migration / Rollback:** in v0.8.0 / none / revert-safe.
- **Depends on:** PR-069, PR-015, PR-021 → **Enables:** PR-071.
- **Demo:** GIF: finding → explain → quick fix → clean.
- **Done when:** Acceptance green.

### PR-071 — Finding panel, configuration UI, and marketplace packaging
*Area: vscode · Complexity: M · Contributor-friendly: no · Artifact: **VSIX / marketplace listing***
- **Value:** Complete, publishable editor experience.
- **Scope:** Finding-details webview (evidence, why-it-matters, remediation, links — CSP-locked,
  no remote content); settings UI contributions for severity gates and rule toggles (writes
  `.agent-reliability.yaml` via documented edits); VSIX packaging, marketplace metadata,
  publisher setup runbook; extension versioning policy (independent, compat table).
- **Non-goals:** Web extension (desktop only v1).
- **Files/packages:** extension.
- **Public APIs:** settings surface final for v0.8.
- **Data models:** none.
- **New deps:** none.
- **Security:** webview CSP audit test; T22 checklist complete.
- **Privacy/egress:** none.
- **Tests:** Webview content sanitization tests (hostile finding text inert); packaging CI
  (VSIX builds reproducibly).
- **Docs:** VS Code page final.
- **Acceptance criteria:** VSIX installs clean; hostile-evidence fixture renders inert.
- **Release / Migration / Rollback:** in v0.8.0 / none / unpublish+patch documented.
- **Depends on:** PR-070 → **Enables:** PR-072.
- **Demo:** Full-workflow screencast for the release notes.
- **Done when:** Acceptance green.

### PR-072 — ⛳ RELEASE v0.8.0 — VS Code integration
*Area: release · Complexity: S · Contributor-friendly: no · Artifact: **marketplace extension + PyPI v0.8.0***
- **Value:** The local developer loop is complete: editor → CLI → CI.
- **Scope:** Release train + first marketplace publish; compat table (extension ↔ CLI versions).
- **Non-goals:** Feature changes.
- **Files/packages:** versions, changelog, marketplace.
- **Public APIs:** none changed.
- **Data models/New deps:** none.
- **Security/Privacy:** T22 checklist re-run at publish; none.
- **Tests:** Post-release: marketplace install against pip-installed CLI (runbook + canary).
- **Docs:** changelog; VS Code quickstart.
- **Acceptance criteria:** Milestone J exit criteria met.
- **Release / Migration / Rollback:** v0.8.0 / none / yank+unpublish path documented.
- **Depends on:** PR-068…071 → **Enables:** Milestone K.
- **Demo:** Fresh-machine editor demo.
- **Done when:** Live.

---

## Milestone K — MCP reliability support → ⛳ v0.9.0

> **Status: Planned architecture — implementation requires the MCP validation gate defined in PLAN.md §37 and EXECUTION.md.** Not automatically committed.

### PR-073 — MCP manifest frontend and permission-scope rules
*Area: mcp plugin · Complexity: L · Contributor-friendly: no · Artifact: agent-reliability-mcp (at PR-077)*
- **Value:** MCP tool surfaces become analyzable IR; AR008 gets real evidence.
- **Scope:** New package `plugins/mcp/`; `agent-lint scan --mcp <client-config|url>` ingesting
  `tools/list` (stdio + HTTP within TB9 bounds: size/time caps, schema validation, responses
  untrusted); lowering to IR Tools; **AR008 full implementation** (declared scopes vs
  used-capability analysis where client code is also scanned; wildcard detection); proposed
  vendor extensions `x-art-side-effect`/`x-art-idempotency` documented; annotation-absence
  findings on risky-named tools (low confidence, per PLAN.md §22).
- **Non-goals:** General MCP vuln scanning (ADR-022; docs link mcp-scan); proxy mode (rejected).
- **Files/packages:** `plugins/mcp/` (frontend, rules), fixtures incl. a fixture MCP server.
- **Public APIs:** `--mcp` flag; extension-field spec.
- **Data models:** MCP-manifest → IR mapping (documented).
- **New deps:** `mcp` SDK (plugin-only dep) **[confirm at implementation]**.
- **Security:** T23: hostile-server fixtures (oversized, malformed, slow, injection strings in
  descriptions → sanitized in findings).
- **Privacy/egress:** connecting to a *user-named* MCP server is user infrastructure (same
  doctrine as PR-047); no other egress.
- **Tests:** Fixture-server corpus; hostile-server suite; AR008 harness set.
- **Docs:** MCP integration page (scope doctrine included).
- **Acceptance criteria:** Fixture server scan produces documented findings; hostile suite green.
- **Release / Migration / Rollback:** in v0.9.0 / none / revert-safe.
- **Depends on:** PR-024, PR-066 → **Enables:** PR-074…076.
- **Demo:** Scan of a wildcard-scoped fixture server → AR008 with manifest evidence.
- **Done when:** Acceptance green.

### PR-074 — agent-contract MCP adapter (test, diff, fuzz over MCP)
*Area: mcp/contract · Complexity: M · Contributor-friendly: no · Artifact: (with v0.9.0)*
- **Value:** The headline MCP feature: breaking-change detection across server versions.
- **Scope:** ContractAdapter for MCP: `agent-contract init mcp://…` (snapshot contracts from
  tools/list), `test` (invoke tools per contract within TB9 bounds), `diff` across snapshots
  (server-upgrade regression gate), `fuzz` (loopback default as PR-065).
- **Non-goals:** Resource/prompt endpoints (tools only, v1).
- **Files/packages:** `plugins/mcp/contract_adapter.py`.
- **Public APIs:** `mcp://` target scheme across agent-contract commands.
- **Data models:** none new (contracts v1 carry MCP metadata field).
- **New deps:** none beyond PR-073.
- **Security:** TB9 throughout; fuzz friction preserved.
- **Privacy/egress:** user-named servers only.
- **Tests:** Fixture-server round-trip (init→test green); seeded v1→v2 server diff caught;
  fuzz finds seeded error-contract bug over MCP.
- **Docs:** MCP contract guide (the P3 workflow end-to-end).
- **Acceptance criteria:** All three seeded demos green in CI.
- **Release / Migration / Rollback:** in v0.9.0 / none / revert-safe.
- **Depends on:** PR-073, PR-064, PR-065 → **Enables:** PR-077.
- **Demo:** CI failing on a server that renamed a tool field.
- **Done when:** Acceptance green.

### PR-075 — ReplaySafe MCP tool wrapper
*Area: mcp/replaysafe · Complexity: M · Contributor-friendly: no · Artifact: (with v0.9.0)*
- **Value:** Any MCP tool call becomes idempotent, claimed, and receipted — client-side.
- **Scope:** `rs.wrap_mcp_tool(session, name, key=…, effect=…, verify=…)` for the official
  Python SDK; contract-aware defaults (effect class and idempotency read from a toolcontract
  when present); example: MCP-based order agent protected end-to-end.
- **Non-goals:** Non-Python MCP clients (ADR-022 revisit trigger); server-side wrapping.
- **Files/packages:** `plugins/mcp/replaysafe_adapter.py`, example.
- **Public APIs:** the wrapper.
- **Data models:** none.
- **New deps:** none beyond PR-073.
- **Security:** wrapped calls inherit full ledger semantics (uncertain on transport loss —
  exercised against the fixture server with injected timeouts).
- **Privacy/egress:** none new.
- **Tests:** Wrapper matrix (dedupe, uncertain, verify) against fixture server; contract-default
  tests.
- **Docs:** MCP + ReplaySafe recipe.
- **Acceptance criteria:** Duplicate MCP tool call executes once; transport loss → uncertain →
  verify path green.
- **Release / Migration / Rollback:** in v0.9.0 / none / revert-safe.
- **Depends on:** PR-073, PR-044 → **Enables:** PR-076.
- **Demo:** Fixture-server charge tool surviving duplicate delivery.
- **Done when:** Acceptance green.

### PR-076 — MCP trust-boundary rules and injection chaos scenarios
*Area: mcp rules/chaos · Complexity: M · Contributor-friendly: partially · Artifact: (with v0.9.0)*
- **Value:** MCP-specific sharpening of the output-trust story.
- **Scope:** Rules: MCP tool output flowing unbounded into context (AR007 sharpened with MCP
  evidence), MCP output reaching high-risk sinks without mediation (AR009 sharpened);
  shipped chaos scenarios: `tool_result_injection` via fixture MCP server (canary → invariant),
  oversized-output, slow-server; MCP guide completed.
- **Non-goals:** Manifest injection scanning beyond what feeds these rules (ADR-022).
- **Files/packages:** `plugins/mcp/rules/`, `scenarios/mcp/`.
- **Public APIs:** none new.
- **Data models/New deps:** none.
- **Security:** the injection scenarios double as regression tests for T23 sanitization.
- **Privacy/egress:** simulation-mode scenarios only.
- **Tests:** Rule harness sets; scenario reproducibility; canary-flow assertions.
- **Docs:** MCP guide final (incl. "what we deliberately don't scan" section).
- **Acceptance criteria:** Harness + scenarios green.
- **Release / Migration / Rollback:** in v0.9.0 / none / revert-safe.
- **Depends on:** PR-073, PR-058 → **Enables:** PR-077.
- **Demo:** Canary injected by fixture server caught before reaching an action.
- **Done when:** Acceptance green.

### PR-077 — ⛳ RELEASE v0.9.0 — MCP support
*Area: release · Complexity: S · Contributor-friendly: no · Artifact: **PyPI: + agent-reliability-mcp (v0.9.0)***
- **Value:** The MCP ecosystem gets reliability tooling scoped to a real gap.
- **Scope:** Release train; MCP quickstart; announcement notes.
- **Non-goals:** Feature changes.
- **Files/packages:** versions, changelog, docs.
- **Public APIs:** `--mcp`, `mcp://`, wrapper under compat policy.
- **Data models/New deps:** none.
- **Security/Privacy:** checklist; none.
- **Tests:** Post-release smoke against the fixture server.
- **Docs:** changelog; quickstart.
- **Acceptance criteria:** Milestone K exit criteria met.
- **Release / Migration / Rollback:** v0.9.0 / none / yank+patch.
- **Depends on:** PR-073…076 → **Enables:** Milestones L, M.
- **Demo:** Quickstart verbatim.
- **Done when:** v0.9.0 live.

---

## Milestone L — n8n support → v0.9.x

> **Status: Planned architecture — implementation requires the n8n validation gate defined in PLAN.md §37 and EXECUTION.md.** Not automatically committed.

### PR-078 — n8n workflow JSON frontend
*Area: n8n plugin · Complexity: M · Contributor-friendly: no · Artifact: agent-reliability-n8n (at PR-083)*
- **Value:** Exported n8n workflows become IR — no TypeScript required.
- **Scope:** New package `plugins/n8n/` (Python); workflow-JSON schema handling (versioned,
  size/depth caps, hostile fixtures — T3); node/connection lowering per PLAN.md §23 (HTTP
  Request → tool+side-effect candidate, IF/Switch → router, Webhook/Wait → entries; node-type
  table as reviewable data file like PR-016's); credential references never resolved (T24).
- **Non-goals:** Rules (PR-079); nodes (PR-080/081); n8n runtime embedding (never).
- **Files/packages:** `plugins/n8n/frontend/`, fixtures (real exported workflows, scrubbed).
- **Public APIs:** `agent-lint scan workflow.json` path.
- **Data models:** node-type table format.
- **New deps:** none.
- **Security:** T3/T24 fixtures; expression fields treated as opaque strings (never evaluated).
- **Privacy/egress:** none.
- **Tests:** Expected-IR goldens; hostile-JSON suite; credential-redaction assertions.
- **Docs:** n8n page (what is modeled / what is not — n8n semantics ART does not simulate).
- **Acceptance criteria:** Fixture corpus green; planted credentials never appear in output.
- **Release / Migration / Rollback:** v0.9.x / none / revert-safe.
- **Depends on:** PR-024 → **Enables:** PR-079, PR-082.
- **Demo:** IR dump of a CRM-update workflow.
- **Done when:** Acceptance green.

### PR-079 — n8n reliability rules and local report
*Area: n8n plugin rules · Complexity: M · Contributor-friendly: yes · Artifact: (with v0.9.x)*
- **Value:** Workflow builders get actionable reliability findings without reading Python docs.
- **Scope:** Rules N8N001–006 (PLAN.md §23: missing error path on side-effect node; retry on
  non-idempotent HTTP node; webhook without dedupe; unbounded node loop; credentials in
  expression fields; missing HTTP timeout); `--format html` local static report (self-contained
  file, CSP-safe, no external assets).
- **Non-goals:** Auto-fixing workflows.
- **Files/packages:** `plugins/n8n/rules/`, HTML reporter.
- **Public APIs:** rule ids; html format flag.
- **Data models:** none.
- **New deps:** none (templated HTML, no JS framework).
- **Security:** HTML report escapes all workflow-derived strings (T11 applies to HTML too —
  injection corpus reused).
- **Privacy/egress:** report is a local file; no CDN links.
- **Tests:** Harness sets ×6; HTML injection corpus; report golden.
- **Docs:** n8n rule catalog; builder-oriented quickstart (screenshots).
- **Acceptance criteria:** Harness green; hostile workflow renders inert HTML.
- **Release / Migration / Rollback:** v0.9.x / none / revert-safe.
- **Depends on:** PR-078 → **Enables:** PR-083.
- **Demo:** HTML report of a flawed CRM workflow.
- **Done when:** Acceptance green.

### PR-080 — n8n nodes workspace and idempotency-key node
*Area: n8n nodes (TS) · Complexity: M · Contributor-friendly: no · Artifact: npm: n8n-nodes-agent-reliability (at PR-081)*
- **Value:** First runtime protection inside n8n itself.
- **Scope:** pnpm sub-workspace `plugins/n8n/nodes/` (isolated TS toolchain, n8n node linting);
  **Idempotency-Key node** (derives keys from configured expressions, injects into downstream
  HTTP headers/params); node testing harness (n8n-workflow test utilities).
- **Non-goals:** ReplaySafe/circuit-breaker nodes (PR-081); publishing (PR-081).
- **Files/packages:** `plugins/n8n/nodes/`, CI job (path-filtered).
- **Public APIs:** node parameters (n8n UX surface).
- **Data models:** none.
- **New deps:** TS/n8n toolchain (isolated).
- **Security:** node code review checklist (n8n nodes run in user's n8n — standard community-node
  trust model, documented).
- **Privacy/egress:** node makes no calls of its own.
- **Tests:** Node unit tests; workflow-level test with the n8n harness.
- **Docs:** Node README (n8n community standards).
- **Acceptance criteria:** Key node works in a test workflow; lint (n8n's) green.
- **Release / Migration / Rollback:** with PR-081 npm publish / none / revert-safe.
- **Depends on:** PR-002 (CI patterns), independent of Python packages → **Enables:** PR-081.
- **Demo:** Test workflow screenshot with injected key header.
- **Done when:** Acceptance green.

### PR-081 — ReplaySafe node and circuit-breaker node + npm publish
*Area: n8n nodes (TS) · Complexity: L · Contributor-friendly: no · Artifact: **npm package (published)***
- **Value:** Deduplicated execution (ambiguity blocked by default) and failure isolation
  inside n8n workflows.
- **Scope:** **ReplaySafe node** (claim/receipt around downstream execution; better-sqlite3
  local ledger, Postgres option for hosted n8n — schema-compatible with the Python ledger so
  `replaysafe` CLI can inspect it **[compat tested]**); **Circuit-breaker node**
  (closed/open/half-open, ledger-backed state); npm publish with provenance.
- **Non-goals:** Feature parity with Python ReplaySafe (subset semantics documented: claims,
  dedupe, receipts — no verify hooks in v1 nodes).
- **Files/packages:** nodes workspace.
- **Public APIs:** node parameter surfaces.
- **Data models:** reuses ledger schema v1 (cross-language compat suite).
- **New deps:** better-sqlite3, pg (node package deps).
- **Security:** same ledger perms/tamper posture; npm provenance.
- **Privacy/egress:** ledger is local/user infrastructure.
- **Tests:** Node suites incl. duplicate-execution workflow test (webhook replay → one HTTP
  call); cross-language ledger read test (Python CLI inspects node-written ledger).
- **Docs:** Node docs; hosted-n8n guidance.
- **Acceptance criteria:** Replay test green; cross-language inspection works.
- **Release / Migration / Rollback:** npm 0.1.0 / ledger schema shared / npm deprecate+patch.
- **Depends on:** PR-080, PR-037 (schema) → **Enables:** PR-082, PR-083.
- **Demo:** n8n workflow surviving webhook replay with receipt visible via `replaysafe list`.
- **Done when:** Published; acceptance green.

### PR-082 — Workflow chaos simulation
*Area: n8n chaos · Complexity: L · Contributor-friendly: no · Artifact: (with v0.9.x)*
- **Value:** Error paths and invariants of exported workflows validated before deployment.
- **Scope:** Graph-semantics simulator over the n8n IR (node execution order, error-output
  routing, retry settings) with chaos faults at node boundaries (http_error, timeout,
  duplicate_webhook) and invariants (`at_most_once` on side-effect nodes, error-path coverage);
  clearly labeled simulation scope (ART's model of n8n semantics, not n8n itself —
  divergence caveats documented per node type).
- **Non-goals:** Full n8n expression evaluation (expressions remain opaque; branches both-taken
  in coverage mode).
- **Files/packages:** `plugins/n8n/simulate/`, scenario extensions (`kind: n8n-workflow`).
- **Public APIs:** scenario target kind.
- **Data models:** none new.
- **New deps:** none.
- **Security:** simulation only — no real node execution, no credentials touched.
- **Privacy/egress:** none.
- **Tests:** Simulator conformance corpus (workflow + fault → expected path); invariant TP/TN;
  reproducibility gate.
- **Docs:** Workflow-chaos guide with honesty section.
- **Acceptance criteria:** Corpus green; flawed workflow's missing error path demonstrably
  caught, fixed variant passes.
- **Release / Migration / Rollback:** v0.9.x / none / revert-safe.
- **Depends on:** PR-078, PR-056 → **Enables:** PR-083.
- **Demo:** Simulated duplicate webhook against exported workflow.
- **Done when:** Acceptance green.

### PR-083 — v0.9.x n8n release
*Area: release · Complexity: S · Contributor-friendly: no · Artifact: **PyPI: + agent-reliability-n8n; npm already live***
- **Value:** The n8n story ships as a coherent unit.
- **Scope:** Release train; n8n quickstart (builder-oriented); announcement notes.
- **Non-goals:** Feature changes.
- **Files/packages:** versions, changelog, docs.
- **Public APIs:** n8n scan/simulate surfaces under compat policy.
- **Data models/New deps:** none.
- **Security/Privacy:** checklist; none.
- **Tests:** Post-release smoke (scan + simulate an example export).
- **Docs:** changelog; quickstart.
- **Acceptance criteria:** Milestone L exit criteria met.
- **Release / Migration / Rollback:** v0.9.x / none / yank+patch.
- **Depends on:** PR-078…082 → **Enables:** —.
- **Demo:** Quickstart verbatim.
- **Done when:** Live. *(Designated de-scope milestone: if v1.0 timing demands, L ships post-1.0
  — PLAN.md §33 R10.)*

---

## Milestone M — Optional model advisor → v0.9.x

> **Status: Planned architecture — optional forever; implementation requires the model-advisor validation gate defined in PLAN.md §37 and EXECUTION.md** (Egress Broker + preview/redaction/allowlist/approval prerequisites). **The advisor can never become a security or authorization authority.**

### PR-084 — Advisor package boundary and minimal-context extraction
*Area: model-advisor · Complexity: M · Contributor-friendly: no · Artifact: agent-reliability-advisor (at PR-087)*
- **Value:** The advisor exists as a *boundary* before it exists as a feature.
- **Scope:** New package `packages/model-advisor/`; entry-point plug-in surfaced as
  `art advise <finding-id>` / `agent-lint --advise` when installed; **minimal-context
  extraction** (finding evidence spans ± N lines, redacted; `--context full-file` explicit);
  offline degradation (no provider → deterministic explain content + notice); import-linter
  contracts: advisor cannot import network libs (broker injected), core cannot import advisor.
- **Non-goals:** Any provider (PR-085/086); suggestions (PR-085).
- **Files/packages:** `packages/model-advisor/`, CLI hook-point in agent-lint.
- **Public APIs:** `art advise` surface; `AdvisorProvider` protocol.
- **Data models:** advisor request/response envelope (schema-validated — TB4).
- **New deps:** none.
- **Security:** TB4 enforced structurally; envelope schema rejects anything that could mutate
  findings (annotative-only by type design).
- **Privacy/egress:** no egress exists yet in this PR (deny-only); redaction-before-envelope
  tests.
- **Tests:** Boundary tests (import-linter both directions); degradation test; envelope schema;
  context-extraction goldens (secrets redacted, spans capped).
- **Docs:** Advisor architecture page (the isolation story).
- **Acceptance criteria:** Core suite passes with advisor absent *and* installed-but-offline
  identically (zero behavior delta on findings).
- **Release / Migration / Rollback:** v0.9.x / none / revert-safe.
- **Depends on:** PR-010, PR-021 → **Enables:** PR-085…087.
- **Demo:** `art advise` without provider → graceful deterministic output.
- **Done when:** Acceptance green; ADR-020 merged.

### PR-085 — Local provider (Ollama) with explain and suggest flows
*Area: model-advisor · Complexity: M · Contributor-friendly: no · Artifact: (with v0.9.x)*
- **Value:** Model-assisted explanations and patch suggestions, fully on-device.
- **Scope:** Ollama-compatible provider via Egress Broker (loopback allowlist per PLAN.md §9
  example 2); `explain` flow (finding + minimal context → narrative, rendered clearly marked
  "model-generated"); `suggest` flow (patch suggestions as diffs, never auto-applied; validated
  to parse before display); prompt templates versioned in-repo.
- **Non-goals:** Remote providers (PR-086); test/scenario generation (PR-087).
- **Files/packages:** `model_advisor/providers/ollama.py`, flows.
- **Public APIs:** provider config keys.
- **Data models:** none new.
- **New deps:** none (broker does HTTP).
- **Security:** suggestions carry a determinism disclaimer + never touch files; broker audit
  records asserted per call.
- **Privacy/egress:** loopback-only allowlist in the example config; egress audit tested.
- **Tests:** Stub-server tests (canned completions); envelope round-trip; audit-record
  assertions; injection canary (hostile finding evidence must not produce tool-use/egress
  behavior — it's text-in/text-out by construction, asserted).
- **Docs:** Local-model setup guide.
- **Acceptance criteria:** Explain/suggest against stub green; audit complete.
- **Release / Migration / Rollback:** v0.9.x / none / revert-safe.
- **Depends on:** PR-084 → **Enables:** PR-086, PR-087.
- **Demo:** `art advise AR002-… --provider ollama` narrative + diff.
- **Done when:** Acceptance green.

### PR-086 — Controlled remote providers with preview and approval
*Area: model-advisor · Complexity: M · Contributor-friendly: no · Artifact: (with v0.9.x)*
- **Value:** Teams that permit egress get it with eyes open — preview, approval, audit.
- **Scope:** Anthropic-compatible and OpenAI-compatible adapters (behind broker allowlist);
  `controlled-egress` UX: per-request payload preview (post-redaction, pager/`--show-egress-
  payload`), session approval mode, provider allowlist config; corporate-proxy support
  (PLAN.md §9 example 5).
- **Non-goals:** Streaming; provider-specific features beyond completion.
- **Files/packages:** provider adapters, approval UX.
- **Public APIs:** provider config surface (final).
- **Data models:** none.
- **New deps:** none.
- **Security:** T19 closure: preview shows *exactly* the bytes to be sent (test: preview hash ==
  sent hash); no-hidden-fallback test (local provider down → error, remote never tried).
- **Privacy/egress:** the entire PR is the §9 controlled-egress contract, tested end-to-end
  against a stub remote.
- **Tests:** Preview-hash equality; approval deny → nothing sent (socket-level assertion);
  allowlist violations; proxy config tests.
- **Docs:** Controlled-egress guide; provider matrix.
- **Acceptance criteria:** A denied approval provably sends zero bytes; audit trail complete.
- **Release / Migration / Rollback:** v0.9.x / none / revert-safe.
- **Depends on:** PR-085 → **Enables:** PR-087.
- **Demo:** Preview → approve → response, with `art egress log` showing the audit record.
- **Done when:** Acceptance green.

### PR-087 — Advisor: tool classification, trace summaries, chaos drafting + release
*Area: model-advisor · Complexity: M · Contributor-friendly: no · Artifact: **PyPI: + agent-reliability-advisor (v0.9.x)***
- **Value:** The remaining advisor capabilities, all annotative, all bounded — and the release.
- **Scope:** Unknown-tool classification (result → `RiskClassification(source=classifier,
  confidence=low)`; deterministic rules unchanged — can only raise scrutiny); trace
  summarization (`art trace summarize <trace-id>`); chaos-scenario drafting
  (`agent-chaos draft --from-finding …` → scenario file marked `draft: true`, schema-validated
  before write); full injection test suite (hostile inputs across all flows); release train.
- **Non-goals:** Auto-generated tests applied without review; any authority over findings.
- **Files/packages:** advisor flows; release files.
- **Public APIs:** the three commands.
- **Data models:** none new.
- **New deps:** none.
- **Security:** classification-authority test (classifier output cannot suppress or downgrade
  any finding — engine-level assertion); draft scenarios cannot set `mode: sandbox` (simulation
  only for drafts).
- **Privacy/egress:** all flows broker-mediated; audit asserted.
- **Tests:** Authority tests; draft-validation tests; injection suite green; post-release smoke.
- **Docs:** Advisor guide complete; changelog.
- **Acceptance criteria:** Milestone M exit criteria met (offline degradation, injection
  canaries, audit completeness).
- **Release / Migration / Rollback:** v0.9.x / none / yank+patch.
- **Depends on:** PR-085, PR-086, PR-043, PR-053 → **Enables:** Milestone N.
- **Demo:** Finding → drafted chaos scenario → (human reviews) → scenario passes validation.
- **Done when:** Live.

---

## Milestone N — v1 hardening → ⛳ v1.0.0

> **Status: Validation-only.** Hardening applies to whatever scope actually shipped through the gates; the entries below assume the full architecture and are narrowed accordingly at planning time.

### PR-088 — Threat-model re-verification and security-audit fixes (wave 1)
*Area: security · Complexity: L · Contributor-friendly: no · Artifact: (with v1.0.0)*
- **Value:** Every §25 threat row is demonstrably tested; audit findings burn down.
- **Scope:** Traceability pass: each threat row T1–T26 mapped to named passing tests (gaps
  closed); commission external audit (core, replaysafe, broker, Action); triage + fix
  critical/high findings (follow-up wave in this PR or fast-follows as severity dictates);
  publish audit summary.
- **Non-goals:** New features.
- **Files/packages:** cross-cutting fixes; `docs/security/audit-2xxx.md`.
- **Public APIs:** none (unless a fix forces a documented breaking change — migration notes then).
- **Data models:** none.
- **New deps:** none.
- **Security:** the point; SECURITY.md updated with audit cadence commitment.
- **Privacy/egress:** re-verified as part of audit scope.
- **Tests:** The traceability matrix itself becomes a CI-checked doc (threat → test id).
- **Docs:** Threat-model doc final; audit summary.
- **Acceptance criteria:** Zero unmapped threats; zero open critical/high audit findings.
- **Release / Migration / Rollback:** gates v1.0.0 / as needed per fix / revert-safe per fix.
- **Depends on:** all component milestones → **Enables:** PR-095.
- **Demo:** Traceability matrix in docs.
- **Done when:** Acceptance green.

### PR-089 — Performance hardening and benchmark gates
*Area: performance · Complexity: M · Contributor-friendly: no · Artifact: (with v1.0.0)*
- **Value:** The perf budgets stop being advisory.
- **Scope:** Arm PR-022's benchmark job as a required gate (scan 10k files < 60 s, single-file
  LSP < 300 ms, ledger ops/sec floor, chaos overhead ceiling — final numbers ratified here);
  optimization pass to meet them (profiling-driven; caching between runs evaluated and either
  landed or explicitly deferred with ADR note); large-repo memory ceiling test.
- **Non-goals:** Distributed scanning.
- **Files/packages:** hot paths per profiling; CI gates.
- **Public APIs:** none.
- **Data models:** none (unless cache format — then versioned + documented).
- **New deps:** none.
- **Security:** cache (if landed) validated against poisoning (repo-local, hashed inputs).
- **Privacy/egress:** none.
- **Tests:** Gates armed; regression >20% fails.
- **Docs:** Performance page final.
- **Acceptance criteria:** All budgets green on the matrix.
- **Release / Migration / Rollback:** gates v1.0.0 / cache format if any / revert-safe.
- **Depends on:** PR-022, PR-068 → **Enables:** PR-095.
- **Demo:** Benchmark dashboard artifact in CI.
- **Done when:** Gates required.

### PR-090 — Public-API freeze and deprecation resolution
*Area: API stability · Complexity: M · Contributor-friendly: no · Artifact: (with v1.0.0)*
- **Value:** v1.0's compatibility promise has an exact, enforced perimeter.
- **Scope:** `__all__` audit across packages; `_internal` sweep (anything undocumented moves or
  gets documented); resolve all pending deprecations (remove or commit); API-diff CI job
  (public surface snapshot; changes require a changelog entry + label); plugin API (`ArtPlugin`,
  IR types, `CORE_API_VERSION`) declared stable with the compatibility policy.
- **Non-goals:** New surface.
- **Files/packages:** all packages; `tools/api_snapshot.py`.
- **Public APIs:** frozen (that's the PR).
- **Data models:** all schemas confirmed at their released versions.
- **New deps:** none (or griffe-style API extractor as dev-dep).
- **Security:** none specific.
- **Privacy/egress:** none.
- **Tests:** API-snapshot job; import-time contract tests (public imports stable).
- **Docs:** API reference generated + compatibility policy final.
- **Acceptance criteria:** Snapshot green; zero undecided deprecations.
- **Release / Migration / Rollback:** gates v1.0.0 / none / revert-safe.
- **Depends on:** all feature milestones → **Enables:** PR-095.
- **Demo:** API-diff job catching a seeded accidental export.
- **Done when:** Gates required.

### PR-091 — Schema and migration audit
*Area: data/migrations · Complexity: M · Contributor-friendly: no · Artifact: (with v1.0.0)*
- **Value:** Every persistent artifact upgrades cleanly — proven, not promised.
- **Scope:** Inventory all versioned artifacts (finding schema, SARIF fingerprints, baseline,
  ledger SQLite+PG, trace store, contracts, scenarios, reports, stub transcripts); N/N-1 reader
  tests against *populated* stores from v0.x releases (artifacts archived in CI from each
  release for exactly this); migration-command e2e per artifact; upgrade guide.
- **Non-goals:** Schema changes (only fixes to migration paths).
- **Files/packages:** migration tests, archived-artifact corpus, docs.
- **Public APIs:** migrate commands confirmed.
- **Data models:** compatibility matrix documented.
- **New deps:** none.
- **Security:** migration paths fuzzed with corrupted stores (clean errors, no partial writes).
- **Privacy/egress:** none.
- **Tests:** The populated-store matrix; corruption suite.
- **Docs:** Upgrade & migration guide.
- **Acceptance criteria:** Every artifact: v0.x-latest → v1.0 migration green with data intact.
- **Release / Migration / Rollback:** gates v1.0.0 / this PR *is* migration / revert-safe.
- **Depends on:** all storage-owning PRs → **Enables:** PR-095.
- **Demo:** v0.5.0 ledger opened and migrated by v1.0 code.
- **Done when:** Matrix green.

### PR-092 — Documentation overhaul and offline docs bundle
*Area: docs · Complexity: L · Contributor-friendly: yes · Artifact: versioned docs site + offline bundle*
- **Value:** v1-grade documentation: complete, versioned, and air-gap-ready.
- **Scope:** Versioned docs (mike); full §27 inventory audit (every listed doc exists, current,
  cross-linked); FAQ + troubleshooting completed from real issue history; `art docs --serve`
  offline bundle (built site shipped in a wheel extra `agent-reliability-docs` **[ASSUMPTION:
  wheel extra vs tarball — decide by size]**); doc-example execution in CI (all quickstart code
  blocks run).
- **Non-goals:** Marketing site.
- **Files/packages:** `docs/`, doc-test tooling.
- **Public APIs:** none.
- **Data models:** none.
- **New deps:** mike (dev).
- **Security:** docs site has no analytics (re-asserted); offline bundle integrity hash.
- **Privacy/egress:** offline bundle serves from localhost only.
- **Tests:** Doc-example execution job; link checker; bundle smoke.
- **Docs:** all of it.
- **Acceptance criteria:** §27 inventory 100%; every quickstart executes green.
- **Release / Migration / Rollback:** with v1.0.0 / none / revert-safe.
- **Depends on:** all feature docs → **Enables:** PR-095.
- **Demo:** Air-gapped container reading full docs via `art docs --serve`.
- **Done when:** Acceptance green.

### PR-093 — Supply-chain hardening: SBOM, provenance, publishing audit
*Area: supply chain · Complexity: M · Contributor-friendly: no · Artifact: attestations on all artifacts*
- **Value:** Consumers can verify what they run came from this repo's CI.
- **Scope:** SBOM generation (CycloneDX) for all Python packages, the extension, and npm nodes;
  SLSA-style provenance attestation on release artifacts (GitHub artifact attestations);
  trusted-publishing configuration audit; dependency-review gate; SHA-pin sweep across all
  workflows; release-process tabletop (key loss, yank, compromised-dep runbooks).
- **Non-goals:** Reproducible builds (documented aspiration post-v1).
- **Files/packages:** release workflows, `docs/security/supply-chain.md`.
- **Public APIs:** none.
- **Data models:** none.
- **New deps:** dev: cyclonedx tooling.
- **Security:** T8/T21 closure at v1 grade.
- **Privacy/egress:** none.
- **Tests:** Attestation verification in the post-release smoke (verify before install).
- **Docs:** Supply-chain page; verification instructions for users.
- **Acceptance criteria:** Smoke verifies provenance on real artifacts from a dry-run release.
- **Release / Migration / Rollback:** gates v1.0.0 / none / revert-safe.
- **Depends on:** PR-003 → **Enables:** PR-095.
- **Demo:** `gh attestation verify` transcript in docs.
- **Done when:** Gates required.

### PR-094 — Final compatibility matrix and air-gap verification
*Area: compatibility · Complexity: M · Contributor-friendly: no · Artifact: (with v1.0.0)*
- **Value:** The support claims on the tin are all CI-tested.
- **Scope:** Final matrix: OS (Linux/macOS/Windows) × Python (3.10–3.13, add 3.14 if released
  **[check at implementation]**) × LangGraph range endpoints; air-gapped install procedure
  executed in CI (no-network container, local wheel mirror, docs bundle, `art doctor
  --assert-offline`); Windows-specific sweep (paths, WAL behavior, signals-for-chaos
  alternatives documented).
- **Non-goals:** New platforms (ARM builds noted as best-effort via wheels).
- **Files/packages:** CI workflows, docs.
- **Public APIs:** supported-platforms statement (a compat contract).
- **Data models:** none.
- **New deps:** none.
- **Security:** none specific.
- **Privacy/egress:** the air-gap job is the ultimate offline proof (spec §14 Q28 evidence).
- **Tests:** The matrix + air-gap job, both required.
- **Docs:** Compatibility page final; air-gap install guide (verified verbatim by the CI job).
- **Acceptance criteria:** Matrix + air-gap green.
- **Release / Migration / Rollback:** gates v1.0.0 / none / revert-safe.
- **Depends on:** PR-091, PR-092 → **Enables:** PR-095.
- **Demo:** Air-gap CI job log: install → scan → chaos → all green, zero sockets.
- **Done when:** Gates required.

### PR-095 — ⛳ RELEASE v1.0.0 — stable local-first toolkit
*Area: release · Complexity: M · Contributor-friendly: no · Artifact: **v1.0.0 everywhere (PyPI ×6+, marketplace ×2, npm)***
- **Value:** The production-credibility commitment: stable APIs, audited security, proven
  semantics.
- **Scope:** Execute PLAN.md §36 checklist item by item (each item's evidence linked in the
  release PR description); `make demo` public case study finalized (lint → chaos-fail →
  ReplaySafe fix → chaos-pass, offline); v1 announcement; post-1.0 roadmap doc (candidates:
  TS analyzer, more frameworks, rule DSL — explicitly *not commitments*).
- **Non-goals:** Anything not already merged.
- **Files/packages:** versions, changelog, docs, demo make target.
- **Public APIs:** SemVer guarantees begin.
- **Data models:** all schemas at stable v-numbers.
- **New deps:** none.
- **Security:** audit summary published; disclosure SLA restated.
- **Privacy/egress:** the air-gap job green on the release commit is a release condition.
- **Tests:** Every gate in the repo, plus §36 checklist review.
- **Docs:** Release announcement; final changelog.
- **Acceptance criteria:** PLAN.md §36 items 1–10 each checked with linked evidence.
- **Release / Migration / Rollback:** v1.0.0 / §28 upgrade guide / yank+patch (1.0.1) runbook
  pre-written.
- **Depends on:** PR-088…094 → **Enables:** post-1.0 roadmap.
- **Demo:** `make demo` — the full story, offline, on a clean machine.
- **Done when:** v1.0.0 live and verified.

---

*End of PR plan. 95 PRs: A(4) B(7) C(12) D(8) E(5) F(9) G(7) H(8) I(7) J(5) K(5) L(6) M(4) N(8).*
