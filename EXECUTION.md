# Agent Reliability Toolkit — Open-Source Execution Roadmap

**Principle: build a serious core, release a narrow surface.**

This is the **authoritative implementation sequence for the first public execution wave** of the
Agent Reliability Toolkit. The complete system vision — every component, trust boundary, schema,
and runtime semantic through v1.0 — lives unchanged in the **Master Architecture Roadmap**:
[`PLAN.md`](PLAN.md) (architecture) and [`PLAN-PRS.md`](PLAN-PRS.md) (the 95-PR architectural
catalog). Nothing has been removed from that vision. What this document changes is the
*commitment model*: only the first wave below (E01–E14) is execution-committed; every later
component is architecturally designed and opens through an explicit validation gate.

## Execution principles

1. **Every release solves a real developer problem** and is installable and usable on its own,
   with a clear CLI or library interface.
2. **Every release ships tests, documentation, examples, and security notes.** No release
   depends on an unfinished future component.
3. **No speculative infrastructure.** Nothing merges without an immediate consumer in the same
   wave.
4. **No throwaway architecture.** The finding model, rule contract, frontend contract, CLI
   contract, and package namespace are final-shaped from the start — subsets of the Layer-1
   design that grow additively, never get rewritten. Each E-PR names its **evolution seam**.
5. **Evidence over roadmap.** Later components (ReplaySafe, agent-chaos, agent-contract, MCP,
   n8n, VS Code, model advisor) proceed when their validation gates open (§ Validation gates),
   or via a documented gate override — never automatically.
6. **Community from the start.** Each E-PR names its **contribution surface**; the public launch
   (E12) is a deliberate milestone, not an afterthought.

## Planning precedence

1. **`EXECUTION.md`** controls the active implementation sequence.
2. **`PLAN.md`** controls architectural boundaries, security principles, product scope, and the
   v1.0 direction.
3. **`PLAN-PRS.md`** is the detailed architectural catalog for later work.
4. If `EXECUTION.md` and `PLAN-PRS.md` differ in sequencing, `EXECUTION.md` wins.
5. If execution pressure conflicts with a security or privacy invariant in `PLAN.md`, the
   security/privacy invariant wins.
6. Any exception to a validation gate or major architecture boundary requires a documented ADR
   (see § Gate override rule).

## Release checkpoints (committed wave)

| Release | After | Minimum content | The real problem it solves |
|---|---|---|---|
| **v0.1.0** | E04 | CLI + safe parsing + AR001 | "My agent looped all night and burned $400 in API calls" — one real finding, offline, in under a minute |
| **v0.2.0** | E07 | AR003 + AR014 + JSON/SARIF + explain/docs/suppressions | The first useful standalone linter for Python agent code |
| **v0.3.0** | E09 | LangGraph recognition + first framework-aware rules | The LangGraph community's first reliability linter |
| **v0.4.0** | E12 | Hardened scanner + GitHub Action + **public launch** | Team-wide PR enforcement, safe to run on untrusted repos, zero infrastructure |
| **v0.5.x** | E13 | Adoption features + retry-safety headline rules (AR002/AR011) | Brownfield adoption + the signature "retry around a charge" detection (exact patch/minor split decided after E12 feedback) |

**After E14, releases become gate-driven.** No later milestone is committed automatically.

---

## The first execution wave: E01–E14

Each E-PR is a complete, reviewable vertical slice carrying 27 fields: the 25 fields of the
catalog template (ID, title, area, value, scope, non-goals, files, APIs, data models, deps,
security, privacy/egress, tests, docs, acceptance, release/migration/rollback, depends-on,
enables, complexity, contributor suitability, artifact, demo, definition of done) plus
**Contribution surface** (what a community member can contribute after this PR) and
**Evolution seam** (how the code grows into the full architecture without rework).
Catalog cross-references point at the `PLAN-PRS.md` PRs each E-PR draws from.

### E01 — Minimal OSS bootstrap
*Catalog: selected parts of PR-001, PR-002 · Area: repo · Complexity: S · Contributor-friendly: no · Artifact: none*
- **Value:** The project exists, is honest about its stage, and a contributor can clone, install,
  and run tests in under five minutes.
- **Scope:** Apache-2.0 LICENSE + NOTICE; short README (thesis, status, roadmap pointers);
  minimal SECURITY.md (contact + coordinated disclosure, one page); minimal CONTRIBUTING.md
  (dev setup, DCO, "rules and fixtures are the contribution path"); CODE_OF_CONDUCT.md
  (Contributor Covenant 2.1); `.gitignore` + `.editorconfig`; **one Python distribution**
  `agent-lint` with internal namespace `agent_reliability/core/` + `agent_reliability/lint/`
  (single pyproject, hatchling, uv for dev); one CI workflow: ruff + mypy + pytest on
  Linux/macOS/Windows × Python 3.10–3.13; hand-written `CHANGELOG.md`; verify the PyPI name
  `agent-lint` (fallback `art-lint`) and record it in `docs/DECISIONS.md` (lightweight decision
  log; formal ADR files arrive with the RFC process at launch).
- **Non-goals:** Full governance (GOVERNANCE.md gated on contributor volume); towncrier;
  release automation; plugin loading; multi-package workspace; docs framework (E12);
  issue-template suite (E12).
- **Files/packages:** repo root, `packages/agent-lint/`, `.github/workflows/ci.yml`,
  `docs/DECISIONS.md`, `CHANGELOG.md`.
- **Public APIs:** none. · **Data models:** none. · **New deps:** dev-only (ruff, mypy, pytest, uv).
- **Security:** disclosure contact live from day one; CI actions SHA-pinned from the first
  workflow (the one supply-chain habit that cannot be retrofitted cheaply).
- **Privacy/egress:** README states the permanent commitments: local-first, no telemetry,
  network-deny by default.
- **Tests:** placeholder test proves the harness; the CI matrix itself is the deliverable.
- **Acceptance criteria:** fresh clone → `uv sync` → `pytest` green on all matrix cells; PyPI
  name resolved and recorded.
- **Docs:** everything in scope is docs.
- **Release / Migration / Rollback:** none / none / revert-safe.
- **Depends on:** — → **Enables:** E02+.
- **Demo:** repo landing page + green CI badge on the 3-OS matrix.
- **Done when:** merged; branch protection enabled.
- **Contribution surface:** none yet, by design — README says so honestly ("contribution paths
  open at v0.4.0; watch the repo").
- **Evolution seam:** the namespace layout **is** the Layer-1 package boundary. When the
  ReplaySafe gate opens and needs a runtime-neutral core, `agent_reliability/core/` becomes its
  own distribution by moving a directory and adding a pyproject — zero import-path changes
  anywhere (PLAN-PRS.md § package-split gate).

### E02 — Final-shaped minimal contracts and finding model
*Catalog: minimal subset of PR-005, PR-007 · Area: core model · Complexity: M · Contributor-friendly: no · Artifact: (with v0.1.0)*
- **Value:** The permanent vocabulary of the whole toolkit exists — small, but with the final
  intended field names and contract shapes, so nothing built on it is ever thrown away.
- **Scope:** Minimal subset using final Layer-1 shapes (PLAN.md §11–§13, reviewed against them
  before merge): `SourceSpan`; `Finding` (with severity, confidence, category, evidence with
  length caps, remediation, references); `Severity` + `Confidence` enums; stable finding ID;
  the **`fp_v1` fingerprint contract** (rule id · rule major version · normalized path ·
  structural AST hash excluding positions · occurrence index); minimal `Rule` +
  `RuleContext` (read-only views, no I/O reachable by construction); minimal `Frontend`
  contract (files → IR fragments); **micro-IR**: `Agent` (loop evidence), `RetryPolicy`
  (with `UNKNOWN`/`UNBOUNDED` first-class), `ToolCall`, `TimeoutPolicy` — the Layer-1 IR types
  themselves, instantiated early; minimal config loader (`.agent-reliability.yaml`:
  `exclude`, `rules.enable/disable`; `yaml.safe_load` only; unknown keys warn — the TB7
  privilege posture from day one because the parser has no dangerous keys to honor).
- **Non-goals:** The complete generic IR (**the micro-IR grows only when a real rule requires a
  new concept** — evolution path documented against PLAN.md §11); rule engine batteries
  (dedupe/baselines later); reporters; parsing (E03); redaction pipeline beyond evidence caps.
- **Files/packages:** `agent_reliability/core/{model,config}/`, JSON round-trip serialization.
- **Public APIs:** `Rule`, `RuleContext`, `Frontend`, model types (documented pre-stable;
  shapes final, fields append-only).
- **Data models:** finding JSON shape (subset schema, published in-repo; fields only ever added,
  never renamed).
- **New deps:** pyyaml (runtime dep #1).
- **Security:** evidence length caps at the type level; paths normalized repo-relative at
  construction (T4 groundwork); no-I/O rule contract is a structural security property (T26).
- **Privacy/egress:** zero network paths exist in the codebase; a socket-guard test job asserts
  it from this PR forever (the standing offline-CI invariant).
- **Tests:** model round-trip tests; fingerprint stability property tests (formatting
  perturbations don't change `fp_v1`); config precedence + unknown-key warnings; contract-shape
  review against PLAN.md §12–§13 recorded in the PR description.
- **Docs:** domain-model docstrings; a short "how the micro-IR grows into the full IR" note
  linking PLAN.md §11.
- **Acceptance criteria:** serialized findings validate against the published subset schema;
  fingerprints stable under reformat; mypy strict green on `core`.
- **Release / Migration / Rollback:** none yet / schema fields append-only from here / revert-safe.
- **Depends on:** E01 → **Enables:** E03+ (everything).
- **Demo:** doctest builds a `Finding`, serializes it, validates it.
- **Done when:** acceptance green.
- **Contribution surface:** none yet (foundation work; deliberately maintainer-only).
- **Evolution seam:** these are the exact contracts the full rule engine (PR-007), plugin system
  (PR-024), and all frontends implement; the micro-IR types are the Layer-1 types with fewer
  siblings. Growth is additive by rule demand — no rewrite point exists.

### E03 — Safe local Python frontend
*Catalog: selected parts of PR-008 · Area: lint frontend · Complexity: L · Contributor-friendly: no · Artifact: (with v0.1.0)*
- **Value:** Python files become micro-IR safely — on hostile input, without ever executing a
  byte of scanned code. **No rules in this PR**; it proves the scanner substrate.
- **Scope:** Parse-only analysis via stdlib `ast` (no import, no exec, ever — T1); file
  discovery honoring `.gitignore` + config excludes; **symlinks not followed by default**;
  repository-root containment via resolved-path prefix checks (T4); safe path normalization
  (repo-relative POSIX); per-file size limit (2 MB), AST node-count limit, per-file time budget,
  wall-clock budget → **partial-scan diagnostics** (`scan-limit`, exit code 4 reserved);
  micro-IR lowering: loop constructs (`while True`, recursion candidates) with LLM/tool-loop
  recognition heuristics → `Agent`; call sites with kwarg extraction → `ToolCall` +
  `TimeoutPolicy` evidence; retry-pattern lowering (tenacity/stamina decorators, manual retry
  loops) → `RetryPolicy`; seed `fixtures/malicious/` (symlink escape, deep nesting, huge file,
  hostile filenames) consumed by CI from now on; `fixtures/frontends/` with expected-IR goldens.
- **Non-goals:** Rules (E04); side-effect classification (E09); dataflow; LangGraph (E08);
  multiprocessing (E10-era if needed for budgets).
- **Files/packages:** `agent_reliability/lint/frontend/`, `fixtures/{malicious,frontends}/`.
- **Public APIs:** `PythonFrontend` implementing the E02 `Frontend` contract.
- **Data models:** none new.
- **New deps:** none (stdlib ast — the Layer-1 ADR-004 decision, honored).
- **Security:** T1/T2/T4/T13 mitigations implemented **now with fixtures** — hostile-input safety
  is not deferrable; no code object is ever created from scanned content (structural test).
- **Privacy/egress:** none; socket guard covers all frontend tests.
- **Tests:** expected-IR goldens; malicious-fixture suite (no hang, no crash, correct
  diagnostics — time budget asserted); Windows path/junction tests; property test: discovery
  never yields a path outside the root.
- **Docs:** "What the analyzer sees" page — the honest capability statement (recognition
  heuristics, limits, `UNKNOWN` semantics).
- **Acceptance criteria:** full malicious suite green on 3 OSes; goldens stable across OSes;
  scans of pathological fixtures terminate within budget with `scan-limit` diagnostics.
- **Release / Migration / Rollback:** none / none / revert-safe.
- **Depends on:** E02 → **Enables:** E04.
- **Demo:** internal IR-dump command on a fixture; symlink-escape fixture rejected with a clean
  diagnostic.
- **Done when:** acceptance green.
- **Contribution surface:** `fixtures/malicious/` accepts community hostile-input cases from now
  on (documented in the fixture README) — the first open contribution path.
- **Evolution seam:** this is the Layer-1 Python frontend (PR-008) minus lowering breadth;
  LangGraph (E08), classification (E09), and every future frontend plug in behind the same
  `Frontend` contract. Resource-limit machinery is reused by every future frontend.

### E04 — Working CLI + AR001 → first real finding
*Catalog: PR-009 · Area: lint CLI · Complexity: M · Contributor-friendly: no · Artifact: **PyPI: agent-lint v0.1.0** ⛳*
- **Value:** **The product exists.** A developer pip-installs and sees a real unbounded-agent-loop
  finding in their own code, offline, in under a minute.
- **Scope:** `agent-lint scan [PATH]` with text reporter; **stable exit-code contract**
  (0 clean / 1 findings / 2 usage / 3 internal / 4 partial — final from day one); **AR001**
  (agent loop without step bound, per PLAN.md §14: loop drives LLM/tool calls with no counter,
  limit check, or bounded range in loop scope); the permanent rule-module structure
  (`rule.py` + `docs.md` + `fixtures/` + `expected.json`); the rule fixture harness
  (`art-rule-test`: every rule runs against every fixture; **cross-rule false-positive net** —
  no rule may fire on any safe control repo-wide); **one true-positive fixture, one safe
  fixture, one edge-case fixture** for AR001; quickstart + README demo; **v0.1.0 release**
  (manual documented checklist; PyPI trusted publishing configured now — one-time setup, not
  machinery).
- **Non-goals:** JSON/SARIF (E06); more rules (E05); explain (E07); suppressions (E07);
  baselines (E13).
- **Files/packages:** `agent_reliability/lint/{cli.py,rules/ar001/}`, `tools/art_rule_test.py`,
  `fixtures/rules/AR001/`.
- **Public APIs:** CLI command + exit codes (permanent contract).
- **Data models:** none new.
- **New deps:** typer (runtime dep #2).
- **Security:** terminal output escape-stripped (T12 baseline — output code is being written
  now, so its safety lands now); CLI e2e runs over `fixtures/malicious/` in CI.
- **Privacy/egress:** e2e asserts zero sockets during scan.
- **Tests:** AR001 harness set + goldens; CLI integration (exit codes, paths, config); the
  false-negative regression corpus directory is created with a README describing the
  report→fixture pipeline (PLAN.md §38).
- **Docs:** quickstart; AR001 rule page (the template every rule follows: what/why/limits/
  remediation/expected output).
- **Acceptance criteria:** `agent-lint scan fixtures/rules/AR001/unsafe` → 1 finding, exit 1;
  `.../safe` → clean, exit 0; **a clean installation (`pip install agent-lint==0.1.0`) produces
  one real finding offline**.
- **Release / Migration / Rollback:** **v0.1.0** / none / yank + patch (documented).
- **Depends on:** E03 → **Enables:** E05–E14.
- **Demo:** terminal recording in README: install → scan → finding with span, why-it-matters,
  remediation.
- **Done when:** v0.1.0 live on PyPI; clean-machine smoke green.
- **Contribution surface:** the rule-module layout + harness is the future one-directory rule
  contribution path (mechanics exist from here; opens publicly at E12).
- **Evolution seam:** CLI verbs and exit codes never change — `scan` grows flags, never new
  semantics. The harness is the same one that gates all 15 AR rules, all LG rules, and all
  future framework rules in the catalog.

### E05 — Rules AR003 and AR014
*Catalog: PR-012 · Area: lint rules · Complexity: M · Contributor-friendly: yes (pattern established) · Artifact: (with v0.2.0)*
- **Value:** The three highest-frequency, highest-confidence agent defects are all caught:
  unbounded loops (E04), missing timeouts, unbounded retries.
- **Scope:** **AR003** (tool/external call without timeout: `timeout` kwarg absent and no
  enclosing `TimeoutPolicy`; known-library call-shape table for requests/httpx/urllib3/
  openai/anthropic SDKs) and **AR014** (retry policy without upper bound: tenacity `stop`
  absent/None, `max_retries=None`, unbounded manual retry loops). **Pure AST, high-confidence
  patterns only, no side-effect classification, low false-positive posture.** Each rule ships
  true positive + safe control + edge case + documentation + exact expected output (the
  per-rule contract, CI-enforced from now on).
- **Non-goals:** Side-effect-aware rules (E13); auto-fix; medium/low-confidence heuristics.
- **Files/packages:** `rules/ar003/`, `rules/ar014/`, frontend lowering maturation, fixtures.
- **Public APIs:** none. · **Data models:** known-library table (reviewable YAML data file).
- **New deps:** none.
- **Security:** rule modules pass the no-I/O grep-guard (armed in CI from this PR).
- **Privacy/egress:** none.
- **Tests:** full harness sets ×2; cross-rule FP net rerun; goldens.
- **Docs:** rule pages with explicit "known limits" sections.
- **Acceptance criteria:** harness green; both rules fire on seeded fixtures and stay silent on
  every safe control repo-wide.
- **Release / Migration / Rollback:** in v0.2.0 / none / revert-safe.
- **Depends on:** E04 → **Enables:** E06, E13.
- **Demo:** tenacity-wrapped `requests.post` without timeout → two findings, two remediations.
- **Done when:** acceptance green.
- **Contribution surface:** these two rules are the copyable reference pattern the "add a rule"
  guide (E12) points at; the known-library table accepts community entries (with documentation
  citations) from now on.
- **Evolution seam:** the known-library table is the seed of the E09/PR-016 classification
  table (same reviewable-data-file format, same citation requirement).

### E06 — JSON + SARIF output and stable schemas
*Catalog: PR-013 · Area: lint output · Complexity: M · Contributor-friendly: no · Artifact: (with v0.2.0)*
- **Value:** Findings become machine-consumable and code-scanning-ready, with IDs that don't
  churn when code moves.
- **Scope:** `--format json` (published subset schema at `docs/schemas/finding-v1.json`) and
  `--format sarif` (SARIF 2.1.0: rules metadata, results, locations,
  `partialFingerprints["art/v1"]` from the E02 `fp_v1` contract, help URIs); **hostile-string
  sanitization** in both formats (T11: script tags, markdown links, control characters rendered
  inert); **schema validation in CI** for every emitted report across the whole fixture corpus;
  **line-drift stability tests** (insert/remove lines around a finding → same fingerprint).
- **Non-goals:** GitHub Action (E11); baseline files (E13); HTML output.
- **Files/packages:** `agent_reliability/core/reporting/{json,sarif}.py`, `docs/schemas/`.
- **Public APIs:** the two format flags (output contracts; append-only evolution).
- **Data models:** published finding JSON schema; SARIF mapping documented as a contract.
- **New deps:** none at runtime (schema validator dev-only).
- **Security:** T11 injection corpus in CI; reports carry spans + capped evidence, never file
  bodies.
- **Privacy/egress:** none.
- **Tests:** official SARIF 2.1.0 schema validation; golden reports; injection corpus;
  line-drift property tests.
- **Docs:** output-format reference; fingerprint stability guarantees page.
- **Acceptance criteria:** every fixture scan's SARIF validates against the official schema;
  hostile strings inert in both formats; line-drift tests green.
- **Release / Migration / Rollback:** in v0.2.0 / `art/v1` fingerprint version tag / revert-safe.
- **Depends on:** E04 → **Enables:** E11 (Action uploads SARIF), E13 (baselines consume
  fingerprints).
- **Demo:** fixture SARIF rendered in the VS Code SARIF viewer.
- **Done when:** acceptance green.
- **Contribution surface:** none new (format work is maintainer-gated; see review boundaries).
- **Evolution seam:** these are the Layer-1 reporters verbatim (PLAN.md §13); baselines (E13)
  and the Action (E11) consume `art/v1` fingerprints unchanged; future formats plug in behind
  the same `Reporter` seam.

### E07 — Explain, rule docs, and minimal suppressions → first useful standalone release
*Catalog: selected parts of PR-015, PR-021 · Area: lint UX · Complexity: M · Contributor-friendly: partially · Artifact: **PyPI v0.2.0** ⛳*
- **Value:** Every finding is educational offline, and false positives can be silenced
  accountably — the two things linter adoption dies without.
- **Scope:** `agent-lint explain AR###` (renders the rule's docs.md + limits + remediation in
  the terminal, fully offline); `agent-lint rules list [--format json]`; **one-source rule
  metadata/docs** (the same docs.md backs the rule page and the explain output — generated
  catalog page per rule); **minimal inline suppression**:
  `# art: ignore[AR003] reason="..."` — **reason required** (empty reason → warning finding
  `ART-META-001`); **no suppression expiry yet** (documented: expiry + suppression report arrive
  in v0.5.x — no permanent-blind-spot story yet, and the docs say so honestly); **contributor
  guide for adding a rule** (module layout, harness, fixture requirements); **v0.2.0 release**.
- **Non-goals:** Suppression expiry/report/file-scope (E13); docs site (E12); advisor hooks
  (gated, § Validation gates).
- **Files/packages:** CLI additions, suppression matcher, `tools/gen_catalog.py`,
  `docs/contributing/add-a-rule.md`.
- **Public APIs:** `explain`, `rules list`, suppression comment syntax (permanent).
- **Data models:** rule-metadata JSON shape.
- **New deps:** none.
- **Security:** suppression parsing is comment-lexing only (no eval); rendered docs are our own
  content, still escape-stripped.
- **Privacy/egress:** explain is offline by construction (test-asserted).
- **Tests:** golden explain output per rule; suppression corpus (match/no-match/missing-reason);
  meta-finding test; catalog-generation drift check.
- **Docs:** rule catalog (generated); add-a-rule guide; suppression policy note with the honest
  expiry caveat.
- **Acceptance criteria:** all three rules explain correctly offline; suppression round-trip
  works; unjustified suppression produces the meta-finding; clean-machine v0.2.0 smoke green.
- **Release / Migration / Rollback:** **v0.2.0** — first useful standalone linter / none /
  yank + patch.
- **Depends on:** E05, E06 → **Enables:** E08 (release rhythm), E12, E13.
- **Demo:** `agent-lint explain AR014` full output; suppressed finding with reason shown in
  verbose mode.
- **Done when:** v0.2.0 live; smoke green.
- **Contribution surface:** rule docs are plain markdown — docs-only contributions open here;
  the add-a-rule guide makes external rule PRs *possible* (publicly invited at E12).
- **Evolution seam:** suppression syntax is the Layer-1 syntax (PLAN.md §13); E13 adds
  `expires=` and the report command without changing anything already written in user code.

### E08 — LangGraph recognition
*Catalog: selected parts of PR-025, PR-026, PR-027 (lowering only) · Area: framework frontend · Complexity: L · Contributor-friendly: no · Artifact: (with v0.3.0)*
- **Value:** agent-lint understands LangGraph applications structurally. **No framework rules in
  this PR** — recognition and lowering are proven first, against real-world fixtures.
- **Scope:** LangGraph support **inside the current distribution**
  (`agent_reliability/lint/frameworks/langgraph/`), behind the existing `Frontend` contract —
  **no separate plugin distribution** (that waits for the plugin-loading gate). Recognize, where
  statically visible: `langgraph` imports; `StateGraph`/`MessageGraph` construction;
  `add_node`/`add_edge`/`add_conditional_edges`; `compile(...)`; **recursion-limit evidence**
  (literal `recursion_limit` config); **`MemorySaver` vs durable checkpointer classes**;
  **interrupt/approval evidence** (`interrupt_before/after`, `interrupt()`); **tool-node
  bindings** (`@tool`, `ToolNode`, `tools=[...]`); **terminal paths** (graph reachability over
  literal edges, `END` constants). Shape-matching only — LangGraph is never imported at scan
  time (test-dependency only, for fixture validation). **Explicitly document unsupported dynamic
  patterns** (graphs built in loops/from data, cross-module indirection, runtime config, dynamic
  tool registries → `UNKNOWN` in IR + `info` diagnostics naming the reason). Micro-IR grows here
  by rule-driven need: `Workflow`, `Node`, `Edge`, `ApprovalGate`, `Checkpoint` types activate
  (they exist in Layer 1's §11; this is their first instantiation).
- **Non-goals:** Framework rules (E09); separate plugin dist; dynamic-graph analysis; MCP.
- **Files/packages:** `agent_reliability/lint/frameworks/langgraph/`,
  `fixtures/frontends/langgraph/` (corpus incl. rewritten real-world examples).
- **Public APIs:** none new (internal frontend behind the E02 contract).
- **Data models:** micro-IR additions (Workflow/Node/Edge/ApprovalGate/Checkpoint — Layer-1
  types, additive).
- **New deps:** none at runtime; langgraph as test-dep, version range declared.
- **Security:** same parse-only guarantees (T1); detection-precision negative corpus (plain
  langchain code must not be misdetected).
- **Privacy/egress:** none.
- **Tests:** expected-IR goldens for the corpus; dynamic-pattern fixtures → `UNKNOWN` +
  diagnostics; negative-detection corpus; version-range endpoints validated in CI (langgraph
  min/max as test-deps).
- **Docs:** LangGraph page: what is seen / what is not (normative honest-limits list).
- **Acceptance criteria:** corpus goldens stable; zero misdetection on the negative corpus;
  every documented unsupported pattern demonstrably degrades to `UNKNOWN` with a diagnostic.
- **Release / Migration / Rollback:** in v0.3.0 / none / revert-safe.
- **Depends on:** E07 → **Enables:** E09.
- **Demo:** IR dump of a real-world-shaped order-agent graph showing nodes, edges, router,
  checkpointer class, and interrupt gates.
- **Done when:** acceptance green.
- **Contribution surface:** the LangGraph fixture corpus accepts community graph patterns
  (especially ones we mis-lower — each becomes a regression fixture).
- **Evolution seam:** this module is the future `agent-lint-langgraph` plugin distribution
  (catalog PR-025+) — behind the `Frontend` contract already, so extraction at the
  plugin-loading gate is a directory move plus entry-point registration, not a rewrite.

### E09 — Minimal side-effect classification + first LangGraph rules → v0.3.0
*Catalog: selected parts of PR-016 (subset), PR-027, PR-028 · Area: framework rules · Complexity: L · Contributor-friendly: partially · Artifact: **PyPI v0.3.0** ⛳*
- **Value:** The first framework-aware findings — and the classification groundwork the
  retry-safety headline (E13) needs. This PR deliberately resolves the dependency between
  framework rules and side-effect classification.
- **Scope:** **Deliberately narrow side-effect classifier**, three layers only:
  (1) explicit ART annotations (`# art: effect=financial` comment / decorator kwarg);
  (2) a small curated known-tool table (stripe charges, boto3 destructive ops, smtplib/sendgrid
  sends, subprocess, shutil.rmtree, SQL execute — every entry requires a documentation citation
  in review); (3) conservative name heuristics at **low confidence only** (`charge_*`,
  `delete_*`, `send_*`). Produces `SideEffect` + `RiskClassification` micro-IR with provenance.
  **Framework rules this classifier can support credibly:**
  - **LG002** — non-durable/in-memory checkpointing (`MemorySaver`) on a graph with risky
    (financial/destructive) tools;
  - **LG003** — high-risk action without visible approval/interrupt gate on its path;
  - **LG006** — router or graph path with no reachable terminal;
  - **AR001 enrichment** — silence AR001 when a visible recursion limit exists (false-positive
    elimination).
  Fallback rule (if any of LG002/LG003/LG006 cannot meet the FP threshold on the fixture
  corpus): **LG001** (side-effect nodes with no checkpointer at all) — structurally simpler,
  fully supported by the same IR; the swap and its reason get documented in the release notes
  and `docs/DECISIONS.md`. **v0.3.0 release.**
- **Non-goals:** Full classification engine (catalog PR-016: SDK breadth, contract sources);
  AR002/AR011 (E13); LG004/LG005/LG007 resume-semantics rules (catalog, post-wave); dataflow.
- **Files/packages:** `agent_reliability/lint/classify/` (+ table as reviewable YAML),
  `rules/lg002|lg003|lg006/`, AR001 enrichment, fixtures.
- **Public APIs:** annotation syntax (`# art: effect=...`) — permanent.
- **Data models:** known-tool table format (citation-required); `SideEffect`/
  `RiskClassification` micro-IR activation (Layer-1 types).
- **New deps:** none.
- **Security:** classifier is data + AST matching only; table entries citation-gated to prevent
  FP-inducing guesswork.
- **Privacy/egress:** none.
- **Tests:** classifier corpus per layer (annotation > table > heuristic precedence,
  provenance/confidence assertions); harness sets for each LG rule (TP/safe/edge); FP-threshold
  check on the LangGraph fixture corpus (documented threshold: zero FPs on safe corpus at
  medium+ confidence); AR001-enrichment regression (recursion-limited fixture → silent).
- **Docs:** classification model page (three layers, honest limits); LG rule pages; v0.3.0
  release notes.
- **Acceptance criteria:** harness green for all shipped rules; zero medium+-confidence FPs on
  the safe LangGraph corpus; AR001 FP eliminated on recursion-limited fixtures; clean-machine
  v0.3.0 smoke green.
- **Release / Migration / Rollback:** **v0.3.0** / none / yank + patch.
- **Depends on:** E08 → **Enables:** E13 (classifier expansion), catalog LG004+.
- **Demo:** `MemorySaver` + charge tool → LG002 critical finding naming the graph node, the
  tool, and the checkpointer class.
- **Done when:** v0.3.0 live; smoke green.
- **Contribution surface:** known-tool table entries (with citations) — a bounded, high-value
  community contribution; LG fixture corpus additions.
- **Evolution seam:** the three-layer classifier is the Layer-1 classification engine (PR-016)
  with fewer table entries and no contract/advisor sources yet — those attach as new provenance
  layers without changing rule code (rules read `RiskClassification`, not the classifier).

### E10 — Malicious-repository and offline hardening
*Catalog: selected parts of PR-006 (redaction subset), PR-010 (guard half), PR-022 · Area: security hardening · Complexity: L · Contributor-friendly: partially · Artifact: (with v0.4.0)*
- **Value:** The scanner is proven safe to run on untrusted repositories — the precondition for
  telling the world to put it in CI. **Lands before the public GitHub Action, deliberately.**
- **Scope:** **Complete T1/T2/T4/T11/T12/T13 fixture coverage** (PLAN.md §25): malicious source
  fixtures; path traversal; symlink containment (incl. Windows junctions); terminal escape
  sequences; SARIF/report injection; malicious filenames (unicode confusables, reserved names,
  huge names); huge/pathological inputs (deep nesting, megabyte literals, many-file repos) with
  budget-bounded degradation; **redaction before reporting** (pattern + entropy secret
  detectors applied to evidence in all output formats — the Layer-1 redaction pipeline's first
  slice, consumed immediately by report paths); **no-network socket-guard CI job over the
  entire test suite and every CLI command** — tests prove scanner commands do not open sockets.
  This is **the first enforcement half of the future egress design** (PLAN.md §9): the full
  Egress Broker object is *not* built here (no consumer exists until the advisor gate opens).
- **Non-goals:** The Egress Broker object; multiprocessing performance work beyond what budgets
  require; canary CI-log e2e (E11, where CI logs exist).
- **Files/packages:** `fixtures/malicious/` completion, `agent_reliability/core/redact/`
  (subset), CI workflow additions, hardening fixes across frontend/reporters.
- **Public APIs:** none.
- **Data models:** none.
- **New deps:** dev-only: socket-guard test plugin.
- **Security:** this PR *is* threat-model execution: T1, T2, T4, T11, T12, T13 rows each get a
  named passing test cited from the PLAN.md §25 table.
- **Privacy/egress:** the socket-guard job becomes a required check permanently; redaction
  before any sink (T6 first slice).
- **Tests:** the full hostile corpus; redaction corpus (AWS keys, JWTs, high-entropy strings,
  .env formats) asserted absent from text/JSON/SARIF outputs; escape-sequence corpus; filename
  torture suite; budget/DoS tests (no hang, exit 4, diagnostics).
- **Docs:** security posture page ("what happens when you scan a hostile repo"); SECURITY.md
  expanded with the tested threat list.
- **Acceptance criteria:** every T-row named above has a passing test; planted canary secrets
  appear in no output format; socket-guard job required on main.
- **Release / Migration / Rollback:** in v0.4.0 / none / revert-safe (guard jobs stay).
- **Depends on:** E06 (output paths exist to harden) → **Enables:** E11 (the Action may claim
  forced-offline behavior only because this PR proves and enforces it).
- **Demo:** scan of the nastiest fixture repo: clean diagnostics, zero sockets, nothing leaked.
- **Done when:** acceptance green; guard jobs required.
- **Contribution surface:** hostile-input and secret-format fixtures — bounded, well-defined
  community contributions with a dedicated guide section.
- **Evolution seam:** the socket guard is the enforcement invariant the Egress Broker (PLAN.md
  §9) later plugs into: when the advisor gate opens, the broker becomes the *only* module
  exempted from the guard. The redaction subset grows into the full Layer-1 pipeline (secret
  hooks, trace-store integration) without interface change. The future network capability model
  distinguishes model egress, test-target access, runtime datastore access, user-tool access,
  and telemetry (always off) — user-owned datastores and test targets are **not** forced through
  the broker (PLAN.md §9 note).

### E11 — GitHub Action
*Catalog: selected parts of PR-033, PR-034 (reduced), PR-035 · Area: CI integration · Complexity: M · Contributor-friendly: no · Artifact: **composite GitHub Action***
- **Value:** Two YAML lines put agent-lint findings on every PR — with the offline guarantee
  already proven, not promised.
- **Scope:** Composite action (`integrations/github-action/action.yml`) with **minimal inputs:
  `path`, `format`, `fail-on`**; pinned, hashed install of the released wheel; SARIF upload via
  SHA-pinned `codeql-action/upload-sarif`; **forced offline/no-network mode** regardless of
  repo config (the Action may claim this only because E10 proves and enforces it); minimal
  permissions (`security-events: write` for upload only); **SHA-pinned third-party actions**
  throughout; self-test workflow running the action on this repo's fixtures with a CI-log
  canary check (planted fake secret absent from logs, annotations, SARIF).
- **Non-goals:** Baseline/changed-files inputs (E13 adds them behind the same input surface);
  marketplace listing polish beyond a working listing (E12 announces it); Docker image;
  monorepo matrix recipes (docs later).
- **Files/packages:** `integrations/github-action/`, self-test workflow.
- **Public APIs:** action inputs `path`/`format`/`fail-on` (contract; inputs are append-only).
- **Data models:** none.
- **New deps:** none beyond pinned actions.
- **Security:** T21 posture (SHA pins, hashed installs, no third-party marketplace deps);
  T20 canary check; forced network-deny tested (a repo config attempting to widen anything is
  ignored in Action context).
- **Privacy/egress:** forced-deny is the headline property; log redaction verified by the
  canary e2e.
- **Tests:** self-test workflow (annotations appear, SARIF validates, severity gate works);
  forced-deny test; canary log check.
- **Docs:** CI integration page with the copy-paste snippet; permissions rationale.
- **Acceptance criteria:** action run on this repo produces code-scanning alerts; canary absent
  from all CI artifacts; consuming the action from a scratch repo works following only the docs.
- **Release / Migration / Rollback:** ships with v0.4.0 train / none / action tag rollback
  documented.
- **Depends on:** E06 (SARIF), E10 (hardening precondition) → **Enables:** E12 (launch story).
- **Demo:** screenshot: PR annotation of an AR003 finding from the self-test.
- **Done when:** acceptance green.
- **Contribution surface:** none new (CI/security path is maintainer-gated).
- **Evolution seam:** the input surface is a strict subset of the catalog Action (PR-033/034) —
  `baseline`, `changed-files`, `rules-allow/deny`, `working-directory` are added in E13/catalog
  without breaking existing consumers.

### E12 — Public launch and contribution surfaces → v0.4.0
*Catalog: selected parts of PR-004 (docs scaffold), PR-023 (examples), community docs · Area: launch/community · Complexity: M · Contributor-friendly: yes (that's the point) · Artifact: **PyPI v0.4.0 + docs site + marketplace listing** ⛳*
- **Value:** The first deliberate public launch: a hardened, CI-ready linter with open,
  well-marked doors for the community.
- **Scope:** **Canonical examples**: `examples/order-agent/unsafe/` (seeded with every shipped
  rule's defect) and `examples/order-agent/safe/` (clean), with an integration test asserting
  the exact finding set; **minimal docs site** (mkdocs-material: quickstart, rule catalog,
  CI guide, security posture, roadmap); **public release notes** (what problem is solved, demo,
  install command, known limitations, contribution requests, validation questions);
  **public roadmap** page (the two-layer model explained: committed wave done, gated components
  listed with their gates); **seeded good-first-issues** (safe fixtures, SDK table entries, rule
  explanations, malformed-input cases — bounded by design); **"add a rule" guide** (from E07,
  promoted + validated by a maintainer dry run); **"contribute a failure fixture" guide**;
  issue templates: **bug report**, **false positive**, **"did this catch a real bug?"**;
  launch-ready README; community feedback process (Discussions categories: Q&A, rule ideas,
  failure stories, roadmap feedback); **v0.4.0 release + announcement**.
- **Non-goals:** Heavy governance (gate §7.10); RFC tooling beyond a Discussions template;
  paid/hosted anything.
- **Files/packages:** `examples/`, `docs/` (site), `.github/ISSUE_TEMPLATE/`, README,
  release notes.
- **Public APIs:** none new.
- **Data models:** none.
- **New deps:** dev-only: mkdocs-material.
- **Security:** example secrets are obvious fakes (CI-asserted); docs site has no analytics;
  launch checklist includes a hostile-repo scan demo as public proof.
- **Privacy/egress:** the launch messaging leads with local-first/no-telemetry and links the
  proof (socket-guard CI, E10).
- **Tests:** example integration test (unsafe → exact findings; safe → clean); docs build
  strict; link check; template rendering.
- **Docs:** the site itself + all guides above.
- **Acceptance criteria:** clean-machine walkthrough of the public quickstart succeeds; all
  templates live; good-first-issues seeded (≥6); v0.4.0 smoke green.
- **Release / Migration / Rollback:** **v0.4.0 — public launch** / none / yank + patch.
- **Depends on:** E09, E10, E11 → **Enables:** E13 (feedback shapes it), E14 (evidence exists
  to review).
- **Demo:** the launch post: install → scan unsafe example → findings → fix → clean, plus the
  Action screenshot.
- **Done when:** v0.4.0 live; announcement out; feedback channels open.
- **Contribution surface:** everything opens here: rules, fixtures, table entries, docs,
  failure stories. This PR *is* the contribution surface.
- **Evolution seam:** issue templates are the demand instruments the validation gates (§ below)
  read; the roadmap page is where gate status is publicly tracked.

### E13 — Adoption features + retry-safety headline → v0.5.x
*Catalog: selected parts of PR-014, PR-015 (completion), PR-016 (expansion), PR-017, PR-032 · Area: lint depth · Complexity: L · Contributor-friendly: partially · Artifact: **PyPI v0.5.0 or v0.5.x** ⛳*
- **Value:** Brownfield teams can adopt without fixing history first — and the toolkit's
  signature detection lands: retries that can double-fire side effects. One execution-wave
  commitment (may be split into E13a/E13b at review time only).
- **Scope:**
  *Adoption features:* baseline creation (`baseline create` → fingerprint set file);
  new-vs-existing classification + `--fail-on new:severity`; **changed-files mode**
  (`--changed-files`, honest cross-file coverage notes); **suppression expiry**
  (`expires=YYYY-MM-DD`, default duration configurable) + **suppression report** (age,
  justification, expired-reactivation) — completing the PLAN.md §13 suppression lifecycle.
  *Retry-safety headline:* expanded side-effect classification (more curated SDK entries from
  community citations, idempotency-evidence detection: replaysafe usage, idempotency-key
  kwargs/headers); **AR002** (retry wraps a non-idempotent action — critical); **AR011** (retry
  may re-execute after uncertain success: timeout/connection-reset failure modes without a
  verify step); remediation links from both rules to the ReplaySafe design doc (Layer 1);
  **"did this bite you?" issue template** linked from AR002/AR011 finding output and docs —
  **the primary demand instrument for the ReplaySafe gate**. Exact v0.5.0 vs v0.5.x packaging
  decided after E12 feedback (stated in release notes).
- **Non-goals:** ReplaySafe implementation (gated); full dataflow (AR009-class rules remain in
  the catalog); org rule packs.
- **Files/packages:** baseline/suppression modules, `rules/ar002|ar011/`, classifier expansion,
  CLI flags, issue template.
- **Public APIs:** `baseline create`, `--fail-on`, `--changed-files`, `expires=` suppression
  field, baseline file format v1.
- **Data models:** baseline schema v1 (published).
- **New deps:** none.
- **Security:** baseline files from scanned repos are data-only (schema-validated, size-capped);
  criticals not baselineable by default (config override explicit).
- **Privacy/egress:** none.
- **Tests:** baseline lifecycle (create → rescan → new-finding detection); expiry reactivation
  (clock injection); harness sets for AR002/AR011 incl. the canonical "tenacity around
  stripe.Charge.create" TP and keyed safe control; changed-files correctness; FP net rerun.
- **Docs:** brownfield adoption guide; AR002/AR011 pages with precise language (see ReplaySafe
  claim precision, PLAN.md §16); suppression policy final.
- **Acceptance criteria:** legacy-repo fixture: baseline → clean CI → seeded new defect →
  exit 1; AR002 fires on the canonical fixture, silent on keyed variant; expired suppression
  reactivates; v0.5.x smoke green.
- **Release / Migration / Rollback:** **v0.5.0/v0.5.x** / baseline schema v1 / yank + patch.
- **Depends on:** E09 (classifier), E12 (feedback shapes packaging) → **Enables:** E14 (the
  gate evidence this PR instruments).
- **Demo:** the README hero: AR002 on a payment retry, with the "did this bite you?" link.
- **Done when:** release live; demand instrument collecting.
- **Contribution surface:** SDK/idempotency-evidence table entries; false-positive reports now
  have a complete suppression + report + fixture pipeline.
- **Evolution seam:** classification provenance layers are ready for contract-sourced
  authoritative classifications (catalog PR-066) and, much later, advisor suggestions (which can
  only raise scrutiny — PLAN.md §24); AR002/AR011 remediation text is the on-ramp to ReplaySafe
  when its gate opens.

### E14 — Evidence review and next-wave decision
*Catalog: no code equivalent — gate review checkpoint · Area: process · Complexity: S · Contributor-friendly: no · Artifact: public adoption report + next-wave ADR*
- **Value:** The next wave is chosen on evidence, in public — not on roadmap momentum. **Not a
  code PR.**
- **Scope:** Create and publish: **adoption report template** (filled for this review);
  **validation-gate scorecard** (each gate from § Validation gates: current counts vs
  thresholds, with links to the evidence); **issue/fixture summary** (what came in since
  launch); **false-positive summary** (rates per rule, fixes shipped); **rule-usage summary**
  (which rules users discuss/suppress/report — public signals only); **contributor summary**
  (who contributed what, credit); **next-wave ADR** (the decision, alternatives, trade-offs,
  review date). Possible outcomes, none automatic: ReplaySafe opens; Agent Chaos opens; Agent
  Contract opens; more lint depth first; MCP or n8n opens; continue feedback collection; stop
  or narrow a weak component.
- **Non-goals:** Committing any milestone without its gate or a documented override.
- **Files/packages:** `docs/reports/adoption-YYYY-MM.md`, `docs/DECISIONS.md` entry or ADR,
  roadmap page update.
- **Public APIs:** none. · **Data models:** report/scorecard templates (reused every cycle).
- **New deps:** none.
- **Security:** report contains only public/user-supplied signals (see adoption strategy below).
- **Privacy/egress:** no telemetry was collected; the report says so and shows what was used
  instead.
- **Tests:** none (process artifact); templates linted for completeness.
- **Docs:** the report + ADR are the docs.
- **Acceptance criteria:** scorecard covers every gate; decision ADR published with review
  date and success/failure criteria; roadmap page updated.
- **Release / Migration / Rollback:** none / none / decisions reversible at next review.
- **Depends on:** E12, E13 (evidence exists) → **Enables:** the next wave, whatever it is.
- **Demo:** the published report and ADR.
- **Done when:** decision made, published, and scheduled for review.
- **Contribution surface:** the report invites public comment before the ADR is finalized
  (Discussions thread).
- **Evolution seam:** this checkpoint recurs after every wave — it is the permanent mechanism
  by which the catalog (PLAN-PRS.md) becomes committed work.

---

## Validation gates

Measurable decision aids — not scientific laws, and not permanent vetoes (see § Gate override
rule). Gate status is tracked publicly on the roadmap page. The same gates appear normatively in
PLAN.md §37.

**ReplaySafe.** Standard gate: ≥5 distinct retry/resume/duplicate-side-effect failure reports,
from ≥3 independent users/teams/orgs, with ≥2 failures reproducible as fixtures or minimal
examples. Severe-event exception: a single severe, reproducible incident (payment duplication,
destructive duplicate action, high-cost runaway retry, compliance-impacting uncertain execution)
may open the milestone via ADR.

**Agent Chaos.** ≥3 independent users/teams request reproducible fault testing; ≥2 requested
scenarios representable as deterministic fixtures; ReplaySafe or agent-lint has already exposed
concrete failure classes worth testing.

**Agent Contract.** ≥3 distinct schema-drift/parameter-drift/tool-contract regression cases
reported; ≥2 with before/after schemas, code, or fixtures; plain JSON Schema validation shown
insufficient for at least one.

**MCP.** A user or maintainer provides a concrete MCP integration target; a reproducible
fixture/manifest/test server exists; the need is clearly differentiated from existing MCP
security scanners.

**n8n.** Any of: ≥3 real exported workflows available as sanitized fixtures; a contributor
commits to maintaining n8n fixtures; a repeated reliability failure appears across multiple
workflows.

**Plugin entry-point loading.** A third-party adapter is proposed; it needs to ship outside the
main distribution; the Frontend/Rule contracts have survived ≥2 public releases. Until then,
first-party integrations stay internal modules behind the same contracts.

**PostgreSQL/Redis (ReplaySafe backends).** ≥2 ReplaySafe users require multi-process or
multi-host coordination; SQLite limitations reproduced and documented; Ledger/Lock contracts
stable.

**VS Code.** CLI output and rule IDs stable for ≥2 public releases; ≥10 explicit requests/
positive confirmations that editor integration would materially help; the extension can reuse
the engine with zero duplicated analysis logic.

**Model advisor.** Optional forever; **can never become a security or authorization authority.**
Proceeds only when: users explicitly request model-assisted explanation/patch generation;
deterministic explain/remediation is already mature; the Egress Broker exists; payload preview,
redaction, allowlisting, and approval semantics are implemented.

**Governance expansion.** Heavier governance (formal GOVERNANCE.md, CODEOWNERS matrix,
multi-maintainer release process) only when contributor volume justifies it: 5+ non-maintainer
contributors, recurring review conflicts, multiple maintainers/release owners, or
security-sensitive external plugins. Do not front-load governance bureaucracy.

**Package split (`agent-reliability-core` as its own distribution).** ReplaySafe needs a
runtime-neutral core, a third-party plugin needs a stable dependency, or products require
independent release cycles. Never split merely because a version number was reached.

## Gate override rule

Numeric gates must not become permanent vetoes. Maintainers may open a gated milestone without
meeting the threshold when one of these applies: severe reproducible failure; strategic
integration; funded or committed contributor; ecosystem change; security incident; strong
maintainer evidence. **Every override requires: a public ADR, the evidence, explicit trade-offs,
a review date, and success/failure criteria.**

## Explicitly deferred architecture (and its cheap placeholder)

Nothing here is cancelled; each item is designed in Layer 1 and waits behind a placeholder with
no rewrite cost.

| Deferred | Placeholder until the gate | Arrives |
|---|---|---|
| **Full generic IR** (PLAN.md §11 complete inventory) | Micro-IR with final-shaped contracts; **add one concept only when a real rule needs it**; no speculative type inventory in implementation | Continuously, rule-driven |
| **Plugin entry-point loading** (PLAN.md §12) | Final `Frontend`/`Rule`/metadata contracts; first-party adapters as internal modules behind them | Plugin-loading gate |
| **Full Egress Broker** (PLAN.md §9) | No-network socket guard over the whole suite; direct network imports forbidden in scanner paths | Before any remote model support (advisor gate). The future network capability model distinguishes **model egress, test-target access, runtime datastore access, user-tool access, and telemetry (always off)** — user-owned datastores and test targets are not forced through a single god-object broker |
| **Full release machinery** (towncrier, lockstep automation) | Handwritten CHANGELOG; tagged releases; simple trusted publishing configured once at E04 | When release cadence becomes painful |
| **Monorepo package split** | Single `agent-lint` distribution containing `agent_reliability/{core,lint}/` | Package-split gate above |
| **Full suppression lifecycle** | Reason-required inline suppressions (E07) | E13 (expiry + report) — committed in this wave |
| **Redaction pipeline completion** (trace-store hooks, secret providers) | Report-path redaction subset (E10) | With the first component that persists data (ReplaySafe gate) |
| **Formal ADR files + RFC tooling** | `docs/DECISIONS.md` log | E12 (RFC process) / governance gate |

## Evidence and adoption collection — without telemetry

The project ships **no phone-home telemetry, no repository fingerprinting, no hidden analytics**
— permanently. Adoption evidence comes only from public or user-supplied signals, and the
roadmap page says exactly which:

- Issues and Discussions (especially the three instrumented templates: bug report,
  false positive, **"did this catch a real bug?"** / **"did this bite you?"**).
- Fixture and rule contributions; repeat participants in Discussions.
- GitHub stars/forks (weak awareness signal only), public dependency graph, public GitHub
  Action usage visible in consumers' workflows.
- PyPI download counts **as a trend only — explicitly not proof of active use**.
- Explicit user confirmations of caught bugs (the strongest signal; each becomes a case study
  with permission and a regression fixture).

The E14 scorecard evaluates every validation gate against these signals.

## Practical open-source strategy (short form — full version in PLAN.md §38)

- **Onboarding in under 30 minutes:** clone → `uv sync` → `pytest` → run one fixture scan →
  copy the AR003 rule directory and make a toy rule. CONTRIBUTING.md is exactly this path.
- **Adding a rule:** one directory (rule.py, metadata, docs.md, TP + safe + edge fixtures,
  expected.json); the harness and FP net enforce quality mechanically; reviewed by any
  maintainer.
- **Contributing a failure fixture:** sanitized code or minimal reproduction + expected
  safe/unsafe behavior + tool/framework versions; fixtures become part of the permanent
  regression suite; contributors credited.
- **Good-first issues are bounded:** safe fixtures, SDK call-pattern entries (with citations),
  rule-explanation improvements, malformed-input cases, false-positive documentation. Never
  architecture or security-boundary changes.
- **Review boundaries:** engine internals, parser safety, fingerprints, redaction, network
  policy, security boundaries, (later) ReplaySafe state semantics and plugin loading require
  maintainer-level review; rules/fixtures/docs are the easy path.
- **RFCs:** major architecture changes start as a GitHub Discussion + RFC doc (alternatives,
  security/privacy impact, migration plan), end as an ADR.
- **Release communication:** every release states the problem solved, a demo, the install
  command, breaking changes, known limitations, contribution requests, and open validation
  questions.
- **Bug report → regression fixture pipeline:** report → reproduce → sanitize → fixture →
  failing regression test → fix → fixture kept forever → contributor credited when allowed.
