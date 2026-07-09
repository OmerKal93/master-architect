# Agent Reliability Toolkit — Master Architecture Roadmap (Layer 1)

**Status:** Planning phase — no production code exists yet.
**Source specifications:** [`docs/planning-prompt.md`](docs/planning-prompt.md),
[`docs/execution-revision-prompt.md`](docs/execution-revision-prompt.md)
**Companion documents:** [`PLAN-PRS.md`](PLAN-PRS.md) — the architectural PR catalog (section
31); [`EXECUTION.md`](EXECUTION.md) — the active Open-Source Execution Roadmap.

This document is written so that a coding agent can implement the system without redesigning it
mid-flight. Where the specification left a choice open, the decision is made here, labeled, and
justified. Assumptions are marked **[ASSUMPTION]**.

## Two planning layers

The plan is split into two layers with different commitment levels:

| Layer | Documents | What it commits |
|---|---|---|
| **Layer 1 — Master Architecture Roadmap** | `PLAN.md` (this document) + `PLAN-PRS.md` | The complete system vision through v1.0: every component, package boundary, trust boundary, schema, runtime semantic, and threat mitigation. Architecture, not merge order. |
| **Layer 2 — Open-Source Execution Roadmap** | `EXECUTION.md` | The committed implementation sequence: the first execution wave (E01–E14), its releases (v0.1.0 → v0.5.x), and the validation gates that open later components. |

**Precedence rules:**

1. `EXECUTION.md` controls the active implementation sequence.
2. `PLAN.md` controls architectural boundaries, security principles, product scope, and the v1.0
   direction.
3. `PLAN-PRS.md` is the detailed architectural catalog for later work — it proves the system has
   been thought through end to end; it is **not** the committed merge order.
4. If `EXECUTION.md` and `PLAN-PRS.md` differ in sequencing, `EXECUTION.md` wins.
5. If execution pressure conflicts with a security or privacy invariant in this document, the
   security/privacy invariant wins.
6. Any exception to a validation gate (§37) or a major architecture boundary requires a
   documented, public ADR.

The guiding principle of the split: **build a serious core, release a narrow surface.** The
architecture anticipates the complete system; implementation progresses through independently
useful open-source releases, and later components open on real-world evidence, not roadmap
momentum.

---

## 1. Executive summary

The **Agent Reliability Toolkit (ART)** is an open-source (Apache-2.0), local-first suite of tools
that makes AI-agent systems **detectable, testable, bounded, auditable, recoverable, and safe to
retry**. It targets the *execution and harness layer* — agent loops, tool calls, retries, side
effects, checkpoints, workflows — where most production agent failures actually occur, rather than
the model layer that existing eval/observability products focus on.

The toolkit ships as six Python packages plus framework plugins and integrations, usable
standalone or together:

| Component | What it does | First release |
|---|---|---|
| `agent-core` | Shared domain model (IR), rule engine, finding schema, config, redaction, egress broker | v0.1.0 |
| `agent-lint` | Local static analyzer + CLI for agent reliability/security anti-patterns (AR-rules) | v0.1.0 (skeleton), v0.2.0 (useful) |
| LangGraph plugin | Framework-aware static analysis of LangGraph graphs, tools, checkpoints, interrupts | v0.3.0 |
| GitHub Action | SARIF-emitting CI integration with baselines and changed-files mode | v0.4.0 |
| `replaysafe` | Runtime idempotency, execution ledger, verify-before-retry, compensation, approval gates | v0.5.0 (SQLite), v0.5.x (Postgres/Redis) |
| `agent-chaos` | Fault injection + invariant checking for agent loops (CLI, pytest plugin, library) | v0.6.0 |
| `agent-contract` | Contract testing for tools and MCP servers (schemas, timeouts, side-effect annotations, fuzzing) | v0.7.0 |
| VS Code extension | Diagnostics, explanations, suppressions on top of the CLI/language service | v0.8.0 |
| MCP plugin | Manifest inspection, contract tests, ReplaySafe wrapping for MCP tools | v0.9.0 |
| n8n plugin | Workflow JSON static analysis + reliability community nodes | v0.9.x |
| `model-advisor` | Optional, isolated, egress-controlled LLM explanations/fix suggestions | v0.9.x |

**Non-negotiables baked into every design below:** all core analysis runs locally with
`network: deny` by default; no telemetry; deterministic engines make all safety decisions (an LLM
may explain, never authorize); scanned user code is never executed; SQLite before any database
server; small public APIs; SARIF and JSON as stable output contracts.

**Path to v1.0:** the complete architecture remains planned through v1.0 — 14 milestones (A–N)
decomposed into a **95-PR architectural catalog** (`PLAN-PRS.md`). **Only the first execution
wave is commitment-level work** (`EXECUTION.md`, E01–E14): the first real finding ships at
**v0.1.0** (CLI + AR001), the first genuinely useful standalone linter at **v0.2.0**
(AR001/AR003/AR014 + JSON/SARIF + explain + suppressions), LangGraph-aware rules at **v0.3.0**,
and the deliberate **public launch at v0.4.0** (hardened scanner + GitHub Action). Every later
component — ReplaySafe, agent-chaos, agent-contract, MCP, n8n, VS Code, the model advisor — is
fully designed here and proceeds through the validation gates in §37, or a documented gate
override, never automatically.

---

## 2. Product definition

**Product name:** Agent Reliability Toolkit (working name; short prefix `art`, PyPI namespace
`agent-reliability-*`, import namespace `agent_reliability.*` — see §10).

**One-sentence definition:** A local-first reliability and security harness for agentic systems
that finds execution-layer defects statically, prevents them at runtime, proves them under fault
injection, and records enough locally to explain and recover from them.

**Core thesis (from the specification):** agent failures happen predominantly at the execution and
harness layer — non-idempotent tools retried, unbounded loops, duplicate webhooks, crashes after a
side effect, uncertain execution state, prompt injection via tool output, missing approval gates —
not only at the model layer. The toolkit therefore treats the *harness* as the unit of analysis
and protection.

**What the toolkit is:**
- A static analyzer (`agent-lint`) with agent-specific deterministic rules.
- A runtime side-effect safety library (`replaysafe`).
- A fault-injection test harness (`agent-chaos`).
- A tool/MCP contract tester (`agent-contract`).
- A local trace/audit substrate shared by the above.
- CI and IDE integrations that reuse — never reimplement — the CLI engines.

**What the toolkit is not:** an orchestration framework, an observability platform, a hosted
service, a general SAST product, or an LLM-judged security gate. See §3.

---

## 3. Scope and non-goals

### In scope before v1.0

- Python ecosystem: CPython 3.10–3.13 **[ASSUMPTION: 3.10 floor — matches LangGraph's floor and
  keeps `ast` features like `match` parsing available; revisit at v1.0]**.
- LangGraph (Python) as the first framework adapter.
- CLI-first UX; pytest plugin; GitHub Actions; VS Code extension (thin client).
- MCP: manifest/schema inspection, contract testing, ReplaySafe wrapping, narrow trust-boundary
  rules (§22).
- n8n: workflow JSON static analysis + a small set of reliability community nodes (§23),
  introducing a TypeScript sub-workspace only at that point.
- Optional model advisor, strictly isolated behind the Egress Broker.
- Local persistence: SQLite (WAL). PostgreSQL and Redis adapters for ReplaySafe only.

### Explicit non-goals before v1.0 (from spec §15, all adopted)

Hosted SaaS control plane; multi-tenant backend; agent orchestration framework; visual workflow
editor; LangSmith/Langfuse replacement; general SIEM; general-purpose MCP vulnerability scanner;
custom model training; autonomous code modification (auto-fix is opt-in, previewed, deterministic
only); automatic remote repository upload; enterprise SSO; billing; team collaboration backend;
cloud dashboard; marketplace; support for every agent framework; automatic execution of user
repositories.

### Additional non-goals this plan adds

- **No dynamic/symbolic execution of scanned code** — pure AST + heuristics, honestly labeled.
- **No general Python linting** — if Ruff/Bandit already has the rule, ART does not duplicate it.
- **No cross-language IR before v1.0** — the IR is designed to admit a TypeScript frontend later
  (n8n JSON needs no TS frontend; it is data), but no TS analyzer ships before v1.0.
- **No distributed ReplaySafe coordination beyond per-resource locks** (no sagas orchestrator, no
  exactly-once messaging claims — the docs say "at-most-once with verification", never
  "exactly-once").

---

## 4. User personas

| Persona | Description | Primary components | Success moment |
|---|---|---|---|
| **P1 — Agent application developer** | Builds LangGraph/custom Python agents; ships to prod; burned by a duplicate side effect or runaway loop | agent-lint, replaysafe, VS Code | `agent-lint` flags the retry around a Stripe charge before code review does |
| **P2 — Platform / reliability engineer** | Owns the agent platform at a company; needs guardrails other teams can't skip | GitHub Action, baselines, org rules, replaysafe (Postgres) | CI blocks new critical findings repo-wide with zero external services |
| **P3 — Security engineer** | Reviews agent/MCP integrations; cares about egress, permissions, injection | agent-lint (AR008/AR009), agent-contract, MCP plugin, threat-model docs | Contract diff catches an MCP server that widened its permission scope |
| **P4 — QA / test engineer** | Writes agent test suites; needs failure-mode coverage | agent-chaos, pytest plugins, agent-contract | A chaos scenario proves the payment invariant holds under duplicate webhooks |
| **P5 — Workflow builder (n8n)** | Low-code automation author; no Python | n8n plugin, reliability nodes | Workflow report shows the un-retried HTTP node writing to a CRM |
| **P6 — Open-source contributor** | Wants to add a rule or adapter | rule-authoring guide, fixture library, plugin API | A new rule PR merges with only fixture + rule + docs files touched |
| **P7 — Air-gapped / regulated user** | No network egress permitted, ever | everything in offline mode | Full toolkit works from an internal mirror with `network: deny` untouched |

---

## 5. Main use cases

1. **Pre-commit / CI scan (P1, P2):** `agent-lint scan .` locally or in CI → findings in
   text/JSON/SARIF → PR annotations; baseline suppresses pre-existing findings; build fails only
   on configured severities.
2. **Making a side effect retry-safe (P1):** wrap `charge_customer` in
   `@replaysafe.action(key=..., effect="financial", retry="verify-before-retry")` → duplicate
   webhook and crash-resume no longer double-charge; ledger shows a receipt per action.
3. **Proving resilience (P4):** define invariants (`payment_occurs_at_most_once`,
   `maximum_steps: 12`) and run `agent-chaos run scenarios/` in CI with seeded, deterministic
   faults; failures reproduce with `--seed`.
4. **Tool/MCP governance (P3):** `agent-contract init` snapshots tool contracts;
   `agent-contract diff` in CI catches breaking schema/permission/side-effect-annotation changes;
   `agent-contract fuzz mcp://…` probes error contracts.
5. **Explaining a finding (P1):** `agent-lint explain AR002` shows the rule, why it matters, safe
   patterns, and framework-specific remediation — fully offline; optionally `--advise` uses a
   local model via the Egress Broker.
6. **Auditing what an agent did (P2, P3):** the local trace/audit store answers "which actions
   ran, with which idempotency keys, what was uncertain, who approved what" and exports to OTLP
   for teams that have collectors.
7. **n8n workflow review (P5):** `agent-lint scan workflow.json` (n8n frontend) → report of
   missing error paths, un-idempotent side-effect nodes, unbounded loops between nodes.

---

## 6. Competitive and overlap analysis

| Existing tool / class | Overlap | ART's differentiation / stance |
|---|---|---|
| **LangSmith, Langfuse, AgentOps** (observability/eval platforms) | Tracing, run inspection | ART is not an observability platform (explicit non-goal). ART records the *minimum local* audit data for findings/receipts/chaos evidence and exports OTLP. Docs will say: "use Langfuse for observability; ART for reliability enforcement." |
| **Semgrep, Bandit, CodeQL, Ruff** (generic SAST/linters) | Static analysis machinery | They have no agent-domain model: no concept of agent loop, tool call, idempotency, checkpoint, approval gate. ART rules operate on an agent-specific IR. ART does **not** duplicate generic rules (e.g. `eval` use → Bandit's job). SARIF output makes ART composable with them. |
| **Guardrails AI, NeMo Guardrails, Llama Guard** (content guardrails) | "Guardrail" naming | Those police model I/O content. ART polices *execution*: side effects, retries, loops, permissions. Complementary, not competing. |
| **mcp-scan (Invariant Labs), MCP security scanners** | MCP inspection | Spec §4.10 directs: do not rebuild a general MCP security scanner. ART's narrow MCP gap: **reliability contracts** (timeouts, idempotency/side-effect annotations, breaking-change diffs) + **ReplaySafe wrapping** of MCP tools. Injection-pattern scanning of manifests is limited to what feeds ART's own trust-boundary rules. |
| **Temporal, Restate, DBOS** (durable execution) | Idempotency, retries, exactly-once-ish semantics | They require adopting their runtime/control plane. ReplaySafe is a *library + local ledger* you add to existing code (LangGraph tools, plain functions) with no server. Docs position ReplaySafe as the "seatbelt you can adopt in an afternoon", and recommend durable-execution engines when teams outgrow it. |
| **tenacity, stamina** (retry libraries) | Retry policies | They make retrying *easy*; ReplaySafe makes it *safe* (ledger, verify-before-retry, uncertainty). ReplaySafe composes with them and `agent-lint` AR-rules recognize their call patterns. |
| **promptfoo, DeepEval, Giskard** (LLM eval/red-team) | Testing agents | Model-quality focused. agent-chaos injects *infrastructure* faults (429s, crashes, duplicate webhooks, concurrency) and checks *execution invariants* — a gap none of these own. |
| **pact, schemathesis** (contract testing) | Contract testing concepts | Neither understands tool-calling schemas, side-effect annotations, MCP manifests, or idempotency expectations. agent-contract borrows their consumer-driven ideas for the tool-call domain. |

**The exact gap ART owns (spec §14 Q24):** *deterministic, local-first reliability enforcement at
the agent execution layer* — the intersection of (a) agent-domain static rules, (b) retry/idempotency
runtime safety without a server, (c) agent-specific fault injection with invariants, and
(d) tool-contract regression testing. No existing tool covers any two of these together, locally.

---

## 7. Architecture overview

```text
                        ┌──────────────────────────────────────────────────┐
                        │                 Integrations                     │
                        │  CLI (art / agent-lint / agent-chaos / …)        │
                        │  pytest plugins   GitHub Action   VS Code (LSP)  │
                        └───────┬──────────────────┬───────────────────────┘
                                │ invokes          │ reuses (JSON-RPC/stdout)
        ┌───────────────────────▼──────────┐  ┌────▼─────────────────────────┐
        │        Analysis plane (static)   │  │      Runtime plane           │
        │                                  │  │                              │
        │  Frontends → IR:                 │  │  replaysafe (decorator/ctx)  │
        │   • Python AST frontend          │  │   ledger · claims · locks    │
        │   • LangGraph adapter            │  │   verify · compensate ·      │
        │   • MCP manifest frontend        │  │   approval hooks             │
        │   • n8n JSON frontend            │  │                              │
        │          │                       │  │  agent-chaos                 │
        │          ▼                       │  │   fault adapters · scenario  │
        │  Rule engine → Findings          │  │   runner · invariant engine  │
        │   (severity, confidence,         │  │                              │
        │    fingerprint, baseline)        │  │  agent-contract              │
        │          │                       │  │   contract runner · fuzzer   │
        │          ▼                       │  │   diff engine                │
        │  Reporters: text/JSON/SARIF      │  │                              │
        └──────────┬───────────────────────┘  └────────────┬─────────────────┘
                   │                                       │
        ┌──────────▼───────────────────────────────────────▼─────────────────┐
        │                       agent-core (shared)                          │
        │  IR types · finding schema · rule/plugin contracts · config loader │
        │  redaction · secret-detection hooks · error taxonomy · IDs         │
        │  trace/audit store (SQLite) · Egress Broker (deny by default)      │
        └────────────────────────────────────────────────────────────────────┘
                                        │ (only via Egress Broker, opt-in)
                              ┌─────────▼──────────┐
                              │   model-advisor    │  (separate package,
                              │ local/remote LLMs  │   never a decision authority)
                              └────────────────────┘
```

Key structural rules:

1. **One direction of dependency:** integrations → tools → plugins → `agent-core`. `agent-core`
   imports nothing from other ART packages.
2. **Frontends lower into a shared IR** (§11); rules run against IR + a raw-AST escape hatch, so a
   rule written once fires for plain Python and (with adapter-enriched IR) for LangGraph.
3. **Engines live in libraries; UIs are thin.** The VS Code extension and GitHub Action invoke the
   same CLI/language-service; no duplicated analysis logic.
4. **The Egress Broker is the only network path** in the entire codebase. Everything else is
   offline by construction, which makes "no telemetry / deny-by-default" testable (§9, egress
   denial tests assert no socket use outside the broker).
5. **Runtime plane never depends on analysis plane** — `replaysafe` must stay a lean production
   dependency (stdlib + SQLite; zero mandatory third-party deps is the target).

---

## 8. Trust boundaries

| # | Boundary | Untrusted side | Trusted side | Enforcement |
|---|---|---|---|---|
| TB1 | Scanned repository ↔ analyzer | All scanned files (Python source, workflow JSON, YAML config in the *target* repo) | agent-lint process | Parse-only (`ast.parse`, `json.loads`); never import/exec target code; resource limits (file size, node count, recursion caps); symlink/path-traversal guards |
| TB2 | Tool output ↔ agent context | Everything a tool returns | Agent harness | Runtime: ReplaySafe/chaos treat tool output as data; static: AR007/AR009 flag unbounded/sensitive flows; contract tests assert output shape |
| TB3 | ART ↔ network | Everything outside the machine | All ART processes | Egress Broker: deny by default, allowlist, preview, purpose, audit (§9) |
| TB4 | Model advisor ↔ deterministic engines | Model output (explanations, suggestions) | Findings, policy, ledger decisions | Advisor output is annotative only; schema-validated; cannot create/suppress/reclassify findings or authorize actions |
| TB5 | Reports ↔ consumers | Finding evidence (contains excerpts of untrusted code) | Terminals, SARIF viewers, PR annotations | Terminal-escape stripping; SARIF/Markdown encoding; evidence length caps; filename sanitization |
| TB6 | Ledger ↔ processes | Concurrent workers, crashed processes | ReplaySafe state machine | Single-writer transactions, atomic claims, monotonic status transitions, append-only audit events |
| TB7 | Config ↔ engines | `.agent-reliability.yaml` in *scanned* repos | Analyzer policy | Scanned-repo config can only *narrow* (add suppressions with justification), never widen permissions, enable egress, or load plugins; loading plugins requires user-level/CLI opt-in |
| TB8 | Third-party plugins ↔ core | Plugin code | Rule engine, IR | Plugins are ordinary Python packages the *user* chose to install (same trust as any dependency); no auto-discovery from scanned repos, entry-point registration only, compatibility handshake (§12) |
| TB9 | MCP servers ↔ contract tester | MCP server responses | agent-contract | Responses schema-validated; size/time bounded; fuzzing only against explicitly named endpoints |
| TB10 | CI ↔ repository secrets | CI logs, SARIF artifacts | Secrets, source | Redaction before any output; SARIF contains spans + hashes, not full files; Action needs no token beyond SARIF upload |

---

## 9. Privacy and egress architecture

### Principles

- **Offline is the default and is complete.** Every feature except the model advisor's remote
  providers works with the network stack never touched.
- **One choke point.** `agent_reliability.core.egress.EgressBroker` is the only component allowed
  to open outbound connections. CI enforces this: an import-linter contract plus a test-time
  socket guard (`pytest-socket`-style) fail the build if any other module touches the network.
- **No telemetry, ever, by default.** No analytics, crash reporting, fingerprinting, or
  install-time calls. Any future telemetry requires a separate opt-in config key and its own ADR.

### EgressBroker contract

```python
class EgressBroker(Protocol):
    def request(
        self,
        *,
        destination: str,          # must match an allowlist entry exactly (scheme+host+port)
        purpose: EgressPurpose,    # enum: MODEL_EXPLAIN, MODEL_SUGGEST, CONTRACT_PROBE, ...
        payload: RedactedPayload,  # constructed only via redaction pipeline
        approval: ApprovalMode,    # PER_REQUEST | SESSION | CONFIG
        timeout_s: float,
        max_bytes: int,
    ) -> EgressResult: ...
```

Behavior: deny unless `network.mode != deny` **and** destination allowlisted **and** purpose
permitted **and** payload passed redaction **and** approval satisfied. Every attempt (allowed or
denied) writes a local audit record: timestamp, destination, purpose, payload *metadata*
(byte size, redaction summary, content hash — never the payload body), decision, approver.
Timeouts and bounded retries are broker-owned; adapters (Ollama, OpenAI-compatible,
Anthropic-compatible) cannot bypass them. **No hidden fallback:** if a local provider fails, the
broker returns `EgressDenied`/`ProviderUnavailable` — it never silently tries a remote one.
Payload preview: in `controlled-egress` mode with `approval: PER_REQUEST`, the exact
post-redaction payload is shown (TTY pager or `--show-egress-payload` dump) before send.

### Privacy modes and configuration examples

```yaml
# 1. Fully offline (DEFAULT — also the air-gapped configuration; nothing to change)
network: { mode: deny }
privacy: { mode: offline }
```

```yaml
# 2. Local model (Ollama on localhost; loopback only)
network: { mode: allowlist, allow: ["http://127.0.0.1:11434"] }
privacy: { mode: local-model }
advisor: { provider: ollama, model: qwen2.5-coder:7b }
```

```yaml
# 3. Controlled remote provider (Anthropic- or OpenAI-compatible)
network: { mode: allowlist, allow: ["https://api.anthropic.com"] }
privacy:
  mode: controlled-egress
  approval: per-request        # show payload preview before every send
  redaction: strict            # secrets + paths + identifiers
advisor: { provider: anthropic-compatible, model: claude-sonnet-5 }
```

```yaml
# 4. CI with no network (explicitly pinned so a misconfigured runner can't widen it)
network: { mode: deny }
privacy: { mode: offline }
ci: { fail_on_egress_attempt: true }   # any broker attempt fails the build
```

```yaml
# 5. Corporate proxy
network:
  mode: allowlist
  allow: ["https://llm-gateway.corp.example:8443"]
  proxy: { https: "http://proxy.corp.example:3128", ca_bundle: /etc/ssl/corp-ca.pem }
privacy: { mode: controlled-egress, approval: session }
```

```yaml
# 6. Air-gapped: identical to (1). Docs additionally cover offline installation
# (pip download / internal mirror), offline docs bundle, and no-network verification:
#   art doctor --assert-offline   # exits non-zero if any egress path is configured
```

Config precedence: CLI flags > env (`ART_*`) > user config (`~/.config/agent-reliability/config.yaml`)
> project config (`.agent-reliability.yaml`) > built-in defaults. Per TB7, *scanned-repo* config is
further restricted: it may never enable egress or load plugins.

---

## 10. Package and repository structure

### Repository layout (monorepo — see ADR-001)

```text
agent-reliability-toolkit/
├── packages/
│   ├── agent-core/              # dist: agent-reliability-core   → agent_reliability.core
│   ├── agent-lint/              # dist: agent-lint               → agent_reliability.lint
│   ├── replaysafe/              # dist: replaysafe               → replaysafe  (see note)
│   ├── agent-chaos/             # dist: agent-chaos              → agent_reliability.chaos
│   ├── agent-contract/          # dist: agent-contract           → agent_reliability.contract
│   └── model-advisor/           # dist: agent-reliability-advisor→ agent_reliability.advisor
├── plugins/
│   ├── langgraph-python/        # dist: agent-lint-langgraph     → agent_reliability.plugins.langgraph
│   ├── mcp/                     # dist: agent-reliability-mcp    → agent_reliability.plugins.mcp
│   └── n8n/                     # dist: agent-reliability-n8n    → agent_reliability.plugins.n8n
│       └── nodes/               # TypeScript sub-workspace (pnpm), Milestone L only
├── integrations/
│   ├── github-action/           # composite action + Dockerfile-less runner script
│   └── vscode/                  # TypeScript extension (thin LSP/CLI client)
├── examples/
│   ├── langgraph-order-agent/   # the canonical demo app (intentionally unsafe + fixed variants)
│   └── ...
├── docs/                        # mkdocs-material site; ADRs in docs/adr/
├── tests/                       # cross-package integration tests only (unit tests live in packages)
├── fixtures/                    # shared fixture library: safe/unsafe code samples, malicious-repo cases
├── tools/                       # repo maintenance scripts (release, fixture verification)
├── pyproject.toml               # uv workspace root (not a distribution)
├── LICENSE  NOTICE  SECURITY.md  CONTRIBUTING.md  CODE_OF_CONDUCT.md  GOVERNANCE.md
└── README.md
```

Changes vs. the spec's sketch, with justification: a top-level `fixtures/` directory (the fixture
library is a first-class, security-sensitive asset shared by all packages — burying it under
`tests/` hides that); unit tests live inside each package (keeps packages independently
releasable and testable); `examples/` contains one *canonical* runnable app reused by docs, chaos
scenarios, and demos rather than many small snippets.

### Packaging and tooling decisions

| Concern | Decision | Rationale |
|---|---|---|
| Workspace/deps | **uv workspaces** with a single lockfile | Boring, fast, first-class monorepo support; one resolver for all packages |
| Build backend | **hatchling** | Simple, standard, no setup.py |
| Naming | Import namespace `agent_reliability.*`; **exception: `replaysafe`** keeps its own top-level import (`import replaysafe`) because it is a production runtime dependency marketed standalone | Discoverability + squatting protection for the suite; ergonomics for the one package users type in prod code |
| CLI | Umbrella `art` command + per-tool entry points (`agent-lint`, `agent-chaos`, `agent-contract`) as aliases to the same Click/Typer apps **[ASSUMPTION: Typer]** | Spec's commands preserved verbatim; umbrella aids discovery |
| Versioning | **Lockstep (unified) versions across Python packages until v1.0** (ADR-018); VS Code extension and n8n nodes version independently (different ecosystems) | Eliminates a compatibility matrix during rapid iteration; plugins pin `agent-reliability-core ==X.Y.*` |
| API stability | Pre-1.0: minor = may break with changelog + migration note; post-1.0: SemVer, public API = documented + exported in `__all__`; everything under `_internal` is free to change | Honest, standard |
| Lint/type | ruff (format+lint), mypy strict on `agent-core`/`replaysafe`, standard on the rest | Core contracts deserve strictness |
| Tests | pytest + hypothesis; coverage gate 85% on core packages | §26 |
| Docs | mkdocs-material; rule catalog pages generated from rule metadata (single source of truth) | §27 |
| Changelog | towncrier fragments per PR; Conventional Commits enforced by CI (commit-lint) | Mechanical release notes |
| Supported OS | Linux, macOS, Windows (CI matrix on all three; Windows path/symlink semantics are part of TB1 tests) | CLI tools must be portable |
| Generated files | Never committed except lockfiles (`uv.lock`, `pnpm-lock.yaml`) and JSON Schemas published in `docs/schemas/` (generated in CI, checked for drift) | Reviewability |
| TypeScript workspace | pnpm workspace introduced only in Milestone J (vscode) / L (n8n nodes); isolated under its directories; no TS at repo root | Avoid dragging Node into Python contributors' setup |
| Internal vs public | `agent-core` is public-but-plugin-facing (stability promised to plugin authors from v0.3); `_internal` modules exempt | Plugin ecosystem needs a stable floor |

---

## 11. Domain model

All types live in `agent_reliability.core.model` as frozen dataclasses (msgspec/pydantic avoided in
core to keep the dependency surface minimal **[ASSUMPTION: stdlib dataclasses + a small validation
helper; revisit only if schema evolution becomes painful]**). Every entity has a **stable internal
ID**: `EntityId = f"{kind}:{deterministic-hash}"` derived from content + source location, never
from memory addresses or counters, so re-scans are diffable.

### Static-analysis IR (produced by frontends, consumed by rules)

| Type | Key fields | Notes |
|---|---|---|
| `SourceSpan` | file (repo-relative, normalized POSIX), start/end line+col | The only place file paths appear |
| `Program` | files, frontends_used, framework detections | Root of one scan |
| `Agent` | id, name, loop constructs, step-limit evidence, framework | "Agent" = an identified agentic loop or graph app |
| `Workflow` | id, nodes, edges, entry/exit, framework | LangGraph graph, n8n workflow |
| `Node` / `Edge` | id, kind (llm/tool/router/human/side-effect/unknown), conditional?, span | |
| `Tool` | id, name, schema (if visible), permissions, side_effect_class, timeout evidence | |
| `ToolCall` | id, tool ref, call site span, timeout evidence, output-bound evidence | |
| `SideEffect` | id, class (`financial/destructive/write/notify/read/unknown`), idempotency evidence, audit-id evidence | Classification model in §14 Q5/Q6 |
| `RetryPolicy` | max_attempts (int \| UNKNOWN \| UNBOUNDED), backoff, wraps → entity refs | Lowered from tenacity/stamina/for-loops/framework config |
| `TimeoutPolicy` | value (seconds \| UNKNOWN \| ABSENT), source | |
| `ApprovalGate` | id, guards → entity refs, mechanism (interrupt/human input/custom) | |
| `Checkpoint` | id, kind (langgraph checkpointer/manual), durability evidence | |
| `RiskClassification` | entity ref, class, source (`annotation/classifier/plugin/default`), confidence | |
| `Invariant` | id, name, expression, source | Shared with agent-chaos |

`UNKNOWN` is a first-class value everywhere — rules distinguish "provably absent" (high
confidence) from "not visible statically" (lower confidence or no finding), which is how the
plan avoids overclaiming (§15).

### Findings and rules

| Type | Key fields |
|---|---|
| `Finding` | rule_id, rule_version, title, description, severity, confidence, category, framework, span(s), evidence (redacted excerpts, length-capped), why_it_matters, remediation, fix (optional `Fix` object), references, suppression_key, fingerprint, baseline_status (`new/existing/absent`), dataflow_path (optional list of spans) |
| `Rule` | id (`AR###`), version (int, bumped on behavior change), title, default_severity, confidence_model, categories, frameworks, requires (IR capabilities needed), docs (markdown), author metadata |
| `Suppression` | key, scope (line/file/project), justification (required), expires (optional date), source span |
| `Baseline` | schema_version, created_at, tool versions, fingerprint set |
| `Fix` | edits (span + replacement), safety (`safe/suggestion`), description — deterministic only |

### Runtime domain (ReplaySafe / chaos / trace)

| Type | Key fields |
|---|---|
| `ActionRecord` | action_id (ULID), key (namespaced idempotency key), args_hash, effect class, status (§16 state machine), attempt, claim (worker id + lease), created/updated, receipt |
| `ExecutionReceipt` | action_id, outcome, result_hash or result (if serializable + policy allows), verified_by, completed_at |
| `AuditEvent` | append-only: actor, action_id/finding_id, event kind, metadata, hash-chained `prev_hash` (§19) |
| `TraceEvent` | trace_id, span_id, parent, kind (tool_call/llm_call/decision/fault_injected/invariant_eval), redacted attrs |

### Shared infrastructure in `agent-core` (bounded — see below)

Rule engine (§13); plugin contracts (§12); finding lifecycle (create → dedupe/merge → baseline
classify → suppress → report); severity/confidence scales (§13); reporters (text/JSON/SARIF);
redaction pipeline + secret-detection hooks (detect-secrets-style regex+entropy providers,
pluggable); config loader (§9 precedence); error taxonomy (`ArtError` → `ConfigError`,
`FrontendError`, `RuleError`, `LedgerError`, `EgressDenied`, … — every CLI exit path maps to a
documented exit code); compatibility metadata (`core_api_version`).

**Boundary rule (spec §4.1):** `agent-core` may contain only: the domain model, contracts
(Protocols), the finding pipeline, config, redaction, egress broker, trace store, and error
taxonomy. It may **not** contain: any frontend, any rule, any CLI command, any framework import,
any network adapter. CI enforces this with import-linter contracts. Anything else lives in the
tool packages — if two tools need it, it must be promoted deliberately via a PR that touches the
public-API docs.

---

## 12. Plugin architecture

**Mechanism:** Python entry points (group `agent_reliability.plugins`), loaded explicitly — never
auto-discovered from the scanned repository (TB8).

```python
class ArtPlugin(Protocol):
    meta: PluginMeta          # name, version, core_api_version_required (SemVer range),
                              # frameworks, capabilities
    def frontends(self) -> list[Frontend]: ...       # lower source → IR fragments
    def rules(self) -> list[Rule]: ...               # framework-specific rules
    def enrichers(self) -> list[Enricher]: ...       # annotate existing IR (e.g. classify tools)
    def contract_adapters(self) -> list[ContractAdapter]: ...   # for agent-contract
    def fault_adapters(self) -> list[FaultAdapter]: ...         # for agent-chaos
```

- **Compatibility handshake (spec §14 Q19):** at load, core checks
  `plugin.meta.core_api_version_required` against its own `CORE_API_VERSION`. Incompatible →
  plugin skipped with a *finding-like diagnostic* (visible in output, not a silent log line).
  Lockstep versioning makes first-party plugins trivially compatible; the handshake exists for
  third parties.
- **Isolation:** a plugin exception is caught per-callback, converted to a `PluginError`
  diagnostic, and the scan continues (a broken plugin must not kill CI).
- **Determinism:** plugin execution order is sorted by (name, version); rules receive IR only
  through read-only views.
- **What belongs in core vs plugins (spec §14 Q22):** core = domain model + engines + generic
  Python frontend + AR-rules that need only generic IR. Plugins = anything importing or
  pattern-matching a specific framework (LangGraph, MCP, n8n), framework-specific rules and
  enrichment, contract/fault adapters for that ecosystem.

---

## 13. Rule engine design

**Execution model:** two-phase, deterministic, no I/O in rules.

1. **Lowering:** frontends parse files (never execute), produce IR fragments; enrichers annotate.
2. **Evaluation:** each rule declares `requires` (IR capabilities, e.g. `retry_policies`,
   `langgraph.graph`) and receives a read-only `RuleContext` (IR + raw AST access + config).
   Rules yield `Finding`s. The engine handles: dedup/merge (same fingerprint from generic +
   framework rule → framework evidence wins, merged into one finding), severity overrides from
   config, suppression matching, baseline classification, reporter dispatch.

**Severity scale** (decision model, not arbitrary scores — spec §8): `critical` (can cause
irreversible external damage: double charge, data deletion, secret egress), `high` (can cause
outage/runaway cost/unbounded behavior), `medium` (weakens recovery or auditability), `low`
(hygiene), `info` (informational detection notes). **Confidence scale:** `high` (pattern provably
present), `medium` (pattern present, safety mechanism possibly elsewhere), `low` (heuristic).
CI failure threshold = f(severity) only; confidence is surfaced to humans and filterable.

**Categories:** `loop-safety`, `retry-safety`, `side-effects`, `timeouts`, `context-hygiene`,
`permissions`, `data-exposure`, `auditability`, `concurrency`, `recovery`.

**Fingerprints (spec §14 Q17):**
`sha256(rule_id · rule_major_version · normalized_path · structural_hash(anchor_ast_node) · occurrence_index)`.
The structural hash covers node type + names + literals-of-interest but **not line/column**, so
formatting and line drift don't churn baselines; `occurrence_index` disambiguates identical
constructs in one file. Fingerprint algorithm is versioned (`fp_v1`); SARIF `partialFingerprints`
carries `art/v1`. Changing the algorithm requires a baseline migration command
(`agent-lint baseline migrate`).

**Suppressions (spec §14 Q18 — avoiding permanent blind spots):**
- Inline: `# art: ignore[AR002] reason="charge is idempotent via Stripe key" expires=2026-12-31`
- Project file: same fields, plus scope globs.
- **Justification is mandatory** (empty reason = the suppression itself becomes a `low` finding).
- **Expiry is default-on** (config default 180 days **[ASSUMPTION]**); expired suppressions
  reactivate the finding at original severity + an `expired-suppression` note.
- `agent-lint suppressions report` lists all active suppressions with age — designed for periodic
  review; GitHub Action can post it as a PR comment on request.

**Baselines:** `agent-lint baseline create` writes `art-baseline.json` (fingerprints + tool
versions). Scans classify findings `new`/`existing`; CI mode `--fail-on new:high+`. Baselines
never hide `critical` by default (config can override with an explicit
`baseline.allow_critical: true`).

**Rule authoring & testing (spec §4.2, §14 Q26):** a rule is one module:
`rule.py` (logic + metadata) + `docs.md` (catalog page source) + `fixtures/` (true-positive cases,
safe controls, edge cases) + `expected.json` (golden findings). `art-rule-test` harness runs every
rule against every fixture repo-wide, asserting: expected findings appear exactly, **no rule fires
on any safe control anywhere** (cross-rule false-positive net), goldens match byte-for-byte
(normalized). External contributors touch only these files; the engine guarantees rules can't
execute scanned code (no `exec`/`import` of target content is reachable from `RuleContext` —
enforced by API design + a security test greping rule modules for forbidden calls).

**Custom organization rules:** orgs ship rules as ordinary plugins (entry points) with an
`ORG###`-prefixed namespace; config `rules.enable/disable/severity` per rule id. No rule DSL
before v1.0 — Python is the rule language (ADR-016 revisit trigger: 3+ orgs ask for
non-programmatic rules).

**Auto-fix policy:** fixes are deterministic AST-anchored edits, opt-in
(`agent-lint fix --rule AR003 --diff` shows patch first), only for rules whose fix is provably
behavior-preserving-or-safer (e.g. add `timeout=` with a documented default). Fixes never run
in CI. Marked `safe` vs `suggestion`; `suggestion` fixes require `--accept-suggestions`.

**Rule versioning:** every behavior change bumps rule `version`; majors change fingerprints (rare,
requires migration note in the rule doc + changelog). Deprecation: rule enters `deprecated` state
(still runs, warns) one minor release before removal; removed rule IDs are never reused.

---

## 14. `agent-lint` design

**Commands (from spec, all kept, plus additions):**

```bash
agent-lint scan .                       # text output
agent-lint scan . --format json|sarif|text
agent-lint scan . --changed-files <list># CI changed-files mode
agent-lint explain AR002                # offline rule documentation
agent-lint rules list [--format json]
agent-lint baseline create|migrate
agent-lint suppressions report
agent-lint fix --rule AR003 --diff      # deterministic autofix preview/apply
agent-lint serve --lsp                  # language service for VS Code (Milestone J)
art doctor [--assert-offline]           # environment/config sanity
```

Exit codes: 0 clean · 1 findings ≥ threshold · 2 usage/config error · 3 internal error ·
4 partial scan (some files skipped — see resource limits). Stable and documented; CI keys off them.

**Scan pipeline:** discover files (respect `.gitignore` + `art.exclude`; symlinks not followed by
default; per-file size cap 2 MB, total node cap, wall-clock budget → oversized inputs produce a
`scan-limit` diagnostic + exit 4, never a hang — DoS mitigation from §25) → parse to AST →
frontends lower to IR → enrichers → rules → finding pipeline → reporter. Multiprocessing across
files **[ASSUMPTION: process pool, size = CPU count, deterministic merge order]**.

**Initial rule set — all 15 AR-rules from the spec are adopted** with the detection strategy,
default severity/confidence, and milestone recorded per rule in the catalog. Summary:

| Rule | Detection sketch (deterministic) | Sev/Conf | Milestone |
|---|---|---|---|
| AR001 no max step count | `while True`/unbounded recursion driving an LLM/tool loop with no counter/limit check in loop scope; LangGraph: no `recursion_limit` and no bounded router | high/high | B (generic), D (LG) |
| AR002 retry wraps non-idempotent action | RetryPolicy IR node whose wrapped call graph contains a SideEffect classified non-idempotent (write/financial/destructive) without idempotency evidence | critical/medium | C |
| AR003 tool call without timeout | ToolCall/HTTP/SDK call with `timeout` param absent and no enclosing TimeoutPolicy | high/high | C |
| AR004 side effect without idempotency key | SideEffect (write+) with no key derivation evidence (replaysafe/stripe-style key/header patterns) | high/medium | C |
| AR005 high-risk action without approval gate | SideEffect class financial/destructive not dominated by an ApprovalGate in IR path | critical/medium | C (generic), D (LG interrupts) |
| AR006 side effect before durable checkpoint | In frameworks with checkpoints: SideEffect node ordered before checkpoint write on the same path | high/medium | D |
| AR007 tool output unbounded into context | Tool return value concatenated/appended to messages/state without slicing/truncation/summary call between | medium/medium | C |
| AR008 overly broad permission scope | MCP/tool manifest scopes ⊃ used capabilities; wildcard scopes | high/high | K (full), C (annotation-based subset) |
| AR009 sensitive output may return to model | Dataflow: source (env/secret manager/credential field names) → tool return / message append, intra-file, explicit-flow only | critical/medium | C (v1 heuristic), N (tuning) |
| AR010 external write without audit identifier | SideEffect write+ with no id/logging call carrying a correlation id in same function | medium/medium | C |
| AR011 retry after uncertain success | Retry wraps call whose failure modes include timeout/connection-reset (HTTP/SDK) and no verify step precedes re-execution | critical/medium | C |
| AR012 concurrent runs may modify same resource | Same resource-key expression written from spawned tasks/threads/graph branches without lock/claim evidence | high/low→medium | G-era (needs IR maturity) |
| AR013 catch-all hides tool failure | `except Exception`/bare except around tool call that swallows (no re-raise/log/status set) | medium/high | C |
| AR014 retry without upper bound | tenacity `stop=None`/missing, `while` retry loops without attempt bound, `max_retries=None` | high/high | B |
| AR015 destructive action without verification/compensation | SideEffect destructive with no compensate/verify registration or surrounding transaction | high/medium | C |

**First three rules (spec §14 Q2): AR001, AR003, AR014.** Rationale: highest real-world frequency;
detectable from generic Python AST with high confidence and low false-positive rates (no
side-effect classification needed yet); each demonstrates a different engine capability (loop
analysis, call-site analysis, retry-policy lowering) — proving the architecture before the harder
classification-dependent rules (AR002/AR004/AR005) land in Milestone C.

---

## 15. LangGraph plugin design

**Recognition (spec §14 Q4):** a file/project is "LangGraph" when imports match
`langgraph.*` and construction patterns are found: `StateGraph(...)`/`MessageGraph(...)`,
`.add_node/.add_edge/.add_conditional_edges`, `.compile(...)`, `create_react_agent(...)`,
`@tool`/`ToolNode` from `langchain_core.tools`/`langgraph.prebuilt`. Version drift is handled by
matching *shapes* (call names + kwarg names) rather than importing LangGraph; the plugin declares
`tested_with: langgraph >=0.2,<0.6` **[ASSUMPTION: verify current versions at implementation
time]** and emits an `info` diagnostic when it detects a newer untested import surface.

**What is lowered into IR (statically reliable):** graph topology from literal
`add_node`/`add_edge` calls; conditional edges (router function refs, path maps);
`compile(checkpointer=…)` presence and checkpointer class; `interrupt_before/after` /
`interrupt()` usage → ApprovalGates; `recursion_limit` in invocation configs when literal;
`@tool` functions → Tools (with docstring/schema extraction); `ToolNode` membership;
retry policies passed to nodes; state schema (TypedDict/Pydantic class fields) for
context-growth rules (AR007: unbounded `messages` append without trimming).

**Explicitly out of reach (documented, not silently wrong — spec §14 Q8):** graphs built in loops
or from data; nodes added via variables resolved across modules (only intra-module and direct
import resolution in v1); runtime-config recursion limits; dynamic tool registries; `Send`-based
dynamic fan-out semantics; actual checkpoint durability (backend config strings are matched:
`MemorySaver` → finding "non-durable checkpointer in production path" vs `SqliteSaver/PostgresSaver`);
subgraph resume semantics beyond structural presence. Each unreachable case degrades to
`UNKNOWN` in IR → rules either stay silent or emit lower-confidence findings per rule policy.

**Framework-specific rules (LG-prefixed, complementing AR-rules with better evidence):**
LG001 compiled graph without checkpointer but with side-effect nodes; LG002 `MemorySaver` on a
graph with financial/destructive tools; LG003 interrupt (approval) missing before high-risk tool
node (sharpens AR005); LG004 unbounded `messages` growth (state append with no trim hook —
sharpens AR007); LG005 side-effect node precedes checkpoint on resume path (sharpens AR006);
LG006 conditional router with no terminal path (loop can never exit — sharpens AR001);
LG007 tool wrapped in node lacks retry/timeout policy while graph resumes on failure (sharpens
AR011). Final list confirmed during Milestone D with fixtures from real LangGraph example repos.

---

## 16. ReplaySafe design

**Goal:** make agent actions safe under retry, resume, duplicate delivery, timeout, crash, and
concurrency — as a library with a local ledger, no server.

**Claim precision (normative for all ReplaySafe docs and marketing):** ReplaySafe
**deduplicates confirmed executions and blocks ambiguous re-execution by default.** It is never
described as guaranteeing that "the external effect ran at most once" — no client-side library
can promise that unaided. True end-to-end protection depends on at least one of: service-side
idempotency (e.g. a provider idempotency key), authoritative verification (a `verify` hook that
can query the real outcome), a transactional outbox on the caller's side, a compensating action,
or human resolution. ReplaySafe's contribution is that **uncertain execution is a first-class
state** and there is **no silent retry after ambiguous success** — the ledger makes the ambiguity
visible and policy-controlled instead of invisible.

### Public API (target shape)

```python
import replaysafe

rs = replaysafe.ReplaySafe(ledger="sqlite:///./.art/ledger.db")   # or Postgres URL later

@rs.action(
    key=lambda order_id: f"charge:{order_id}",   # idempotency key (namespaced by action name)
    effect="financial",                           # read|write|notify|destructive|financial
    retry=rs.policy(max_attempts=3, verify_before_retry=True, backoff="expo"),
    verify=lambda ctx: stripe_lookup(ctx.key),    # authoritative outcome check → Verified(...)
    compensate=lambda ctx: refund(ctx.receipt),   # optional compensation hook
    approval=None,                                # or rs.approval(required_for=["destructive"])
)
def charge_customer(order_id: str) -> ChargeResult: ...

# also: rs.wrap(fn, ...) for functions you don't own; context-manager form `with rs.claim(key):`;
# adapters: rs.wrap_langgraph_tool(tool), rs.wrap_mcp_tool(session, name), rs.wrap_http(client)
```

### State machine (authoritative)

```text
            claim OK                    effect ran, receipt persisted
 (none) ──► pending ──► started ──────────────────────────► completed
                          │   │                                  ▲
                          │   └─ raised before effect ─► failed  │ verify says "happened"
                          │                                      │
                          └─ crash / timeout / lost response ─► uncertain
                                                                 │  verify says "didn't happen" → failed (retry eligible)
                                                                 │  compensation executed        → compensated
                                                                 └─ verify unavailable → stays uncertain (escalate)
```

Transitions are monotonic and executed in single ledger transactions. `attempt` increments only
via legal `failed → pending(attempt+1)` re-arms under the retry policy bound.

**Write ordering (crash safety):** (1) INSERT intent row `started` (with args_hash, claim, lease)
**before** the side effect executes; (2) run effect; (3) UPDATE to `completed` + receipt. A crash
between 1–3 leaves `started` past its lease → recovery sweep marks it `uncertain`. **Uncertain
never silently retries** (spec §14 Q9): with a `verify` hook, verification decides
(happened → completed-by-verification; didn't → failed, retry-eligible); without one, policy
`on_uncertain: block | compensate | require_approval` (default **block** for
`financial/destructive`, `require_approval` surfaces to the approval hook). This is the honest
"at-most-once, with verified retry" semantic — docs never claim exactly-once.

### Failure semantics (spec §4.4 list, each defined)

| Scenario | Behavior |
|---|---|
| Completed but response lost | Row `started` + lease expiry → `uncertain` → verify path above |
| Crash before receipt persisted | Same as above (intent row is the ground truth that an attempt may have fired) |
| Two workers claim same action | Atomic claim: `INSERT … ON CONFLICT` / `UPDATE … WHERE status IN (…) AND lease_expired` in one transaction. Loser gets `ActionAlreadyClaimed` with current status; may wait-and-observe (`rs.await_result(key, timeout)`) or fail fast |
| Verification endpoint unavailable | Bounded verify retries (own policy) → remains `uncertain`, emits audit event + optional approval escalation; never assumes either outcome |
| Compensation fails | Status stays `uncertain`, `compensation_failed` audit event with attempt count; bounded compensation retries; terminal escalation to approval hook. (No silent `compensated`) |
| Idempotency key collision (same key, different args) | `args_hash` mismatch → `KeyReuseError` (hard fail). Same key + same args = dedupe: return stored receipt/`completed` result |
| Ledger unavailable (spec §14 Q11) | **Fail closed** for `write/financial/destructive/notify` (raise `LedgerUnavailable`, do not run effect); configurable fail-open for `effect="read"` only. Never queue effects in memory |
| User requests force retry | `rs.force_retry(key, actor=…, reason=…)` — requires explicit actor + reason, writes audit event, re-arms from `uncertain/failed` bypassing verify **once**; CLI: `replaysafe force-retry <key>` prompts for confirmation |
| Non-serializable result | Effect still protected: receipt stores `result_omitted=True` + `result_hash=None`; dedup returns `CompletedNoResult` sentinel; docs recommend returning serializable summaries |

**Locking/concurrency:** per-resource locks derive from the key namespace
(`lock:{action}:{key}`); SQLite backend uses the claim row itself as the lock (single-node);
Postgres uses `SELECT … FOR UPDATE SKIP LOCKED` claims; Redis adapter (later) provides lease-based
locks for multi-node — documented as *advisory across nodes* with the usual fencing caveats
(lease token checked at receipt-write time; stale lease → receipt rejected).

**Idempotency keys (spec §14 Q10):** developer supplies the key function (they know the natural
key); ReplaySafe namespaces it (`{action_name}:{key}`), validates (non-empty, ≤512 bytes, UTF-8,
no control chars), hashes long keys, and stores `args_hash` alongside to catch reuse. A `key=AUTO`
mode (hash of qualified name + canonicalized args) exists for pure-ish operations but docs warn
it's wrong for calls whose args differ across legitimate retries.

**Storage:** SQLite first (WAL, `synchronous=FULL` for the intent/receipt writes,
single-writer connection, busy_timeout). Schema versioned with embedded migrations
(`user_version` pragma); `replaysafe migrate` CLI. Postgres backend implements the same `Ledger`
protocol + real migrations (Alembic **[ASSUMPTION]**). Ledger rows are append-preserving: status
changes UPDATE the row but every transition also appends an `AuditEvent` (hash-chained, §19) so
tampering is detectable.

**Approval hooks:** pluggable `ApprovalProvider` (CLI prompt provider first; callback provider for
frameworks; "file drop" provider for headless approve-by-writing-a-token). Approval decisions are
audit events with actor identity.

---

## 17. Agent Chaos design

**Interfaces:** `agent-chaos run scenarios/` CLI; `pytest` plugin (`@pytest.mark.chaos(scenario=…)`,
fixtures `chaos_env`, `chaos_report`); library (`agent_reliability.chaos.api`).

### Scenario format (YAML, versioned `scenario_schema: 1`)

```yaml
scenario: duplicate-webhook-during-charge
seed: 42                      # required for CI; omitted → random seed, printed for repro
target:
  kind: python                # python | langgraph | command
  entrypoint: examples.order_agent:app
  mode: simulation            # simulation | sandbox  (see safety boundary below)
faults:
  - at: tool_call             # injection point: tool_call | http | llm | process | clock | ledger
    match: { tool: charge_customer, call_index: 1 }
    inject: duplicate_delivery          # from the fault catalog
  - at: http
    match: { host: api.stripe.example }
    inject: { kind: timeout_after_send, delay_ms: 30000 }
invariants:
  - payment_occurs_at_most_once          # named invariant bound to ledger/trace queries
  - maximum_steps: 12
  - maximum_cost_usd: 0.50
  - uncertain_payment_requires_human: true
  - no_secret_is_returned_to_model: true
report: { format: [text, json], out: .art/chaos/ }
```

**Fault catalog (mapped to spec's list; each is a `FaultAdapter`):** rate-limit 429; timeout
before action; timeout after action may have succeeded; malformed JSON; invalid tool schema;
partial response; duplicate webhook/delivery; process crash (child-process harness + SIGKILL);
stale checkpoint (checkpointer wrapper serves N-1 state); missing memory store; context growth
(inflate tool outputs); tool-result prompt injection (canary strings — the invariant checks the
canary never reaches an *action*, deterministic); two concurrent workers; delayed success; DB
lock; ledger outage (ledger proxy raises); approval timeout; model returns repeated tool call;
model changes tool args between retries (the last two require the **scripted model stub**).

**Determinism (spec §14 Q15 context):** two modes. `deterministic` (default, CI-safe): the model
is a **scripted stub** (recorded or hand-written tool-call sequences); faults fire on seeded
schedules; runs are byte-reproducible given (scenario, seed, code). `model-backed` (opt-in, local
model via Egress Broker): explores realistic behavior, marked non-reproducible in reports; never
used for pass/fail gating by default.

**Invariant engine:** invariants compile to deterministic evaluators over three sources —
the trace event stream, the ReplaySafe ledger, and process/cost counters. Built-ins:
`*_occurs_at_most_once(action)`, `maximum_steps`, `maximum_cost_usd` (token/price table supplied
by config, counted from stubbed or real usage events), `uncertain_*_requires_human` (ledger:
every `uncertain` row of class X has an approval audit event), `no_secret_is_returned_to_model`
(canary secrets planted in env/fixtures must not appear in any model-bound message —
deterministic string/hash match). Custom invariants: Python callables registered per project
(`invariants.py`), receiving a read-only `ChaosRun` view. Evaluation happens post-run (stream is
persisted), so failures show *which event* violated what.

**Production-safety boundary (spec §14 Q14 — mandatory, with honest isolation levels):** chaos
refuses to run unless the target declares `mode: simulation` (all external I/O must pass through
registered test doubles; any unmatched real socket attempt aborts the run — enforced with the
same socket-guard used in §9) or `mode: sandbox` (explicit allowlist of local endpoints, e.g. a
local Stripe mock; still deny-by-default). There is deliberately **no `mode: production`**, and
fault adapters patch client libraries and ART components — they never target real infrastructure.

The isolation model is staged and its limits are stated, not hidden. The plan distinguishes three
distinct things: **deterministic simulation** (scripted model stub + test doubles — reproducible
by construction), **application-level fault injection** (in-process patching + socket guard +
subprocess restrictions — *best-effort containment*: a Python-level socket guard cannot stop
native extensions or subprocesses that bypass Python's socket layer, and the docs say so), and
**OS-level isolation** (container boundary, network namespace, OS sandbox, explicit target
allowlist — the *strong* boundary, recommended for CI and required before any claim of hard
containment). Before strong sandboxing ships, all chaos documentation describes the guard as
best-effort with visible limitations; ART never claims that an application-level guard makes it
"physically unable" to reach production. This staging is documented in SECURITY.md.

**Outputs:** `ChaosReport` (JSON, schema-versioned) + human text: per-scenario verdict, invariant
evaluations with evidence event ids, fault schedule, seed, environment digest; `--format sarif`
maps invariant violations to SARIF results for CI annotation. Reports feed the trace store for
later inspection. Integration with ReplaySafe: ledger assertions are first-class (the
`payment_occurs_at_most_once` invariant is literally a ledger query), and chaos ships scenarios
specifically exercising ReplaySafe semantics (crash-between-intent-and-receipt, etc.) — these
double as ReplaySafe's own acceptance tests.

---

## 18. Agent Contract design

**Contract format (`toolcontract`, YAML, human-readable, schema-versioned):**

```yaml
contract_schema: 1
tool: charge_customer
version: 2                       # contract version, not tool code version
description: Charge a customer order
input_schema: { $ref: "./schemas/charge_input.json" }   # JSON Schema (inline or ref)
required: [order_id]
enums: { currency: [USD, EUR] }
output_schema: { $ref: "./schemas/charge_output.json" }
errors:                          # error contract
  - { code: card_declined, retriable: false }
  - { code: rate_limited,  retriable: true, retry_after: true }
timeout_ms: 5000
side_effect: financial           # must match ART's classification vocabulary
idempotency: { supported: true, mechanism: key, key_param: idempotency_key }
approval_required: true
permissions: [payments:write]
examples:
  - { input: {...}, expect: {status: succeeded} }
```

**Capabilities → commands:**
- `agent-contract init` — introspect a tools directory / MCP server, *draft* contracts (marked
  `draft: true`; classification fields left `unknown` for humans to fill — the tool never guesses
  side-effect class silently).
- `agent-contract test ./tools` — validate implementations against contracts: schema round-trip,
  required fields, enum rejection of out-of-set values, response shape on examples, timeout
  budget honored (measured against declared `timeout_ms` with a test double clock where possible),
  error-contract conformance (declared codes/retriability), side-effect and idempotency
  annotations present and consistent (e.g. `idempotency.supported` ⇒ key param exists in schema),
  approval/permission declarations present for `financial/destructive`.
- `agent-contract diff v1/ v2/` — breaking-change detection: removed/renamed fields, narrowed
  enums, type changes, new required inputs, widened permissions, side-effect class escalation,
  timeout increases past thresholds, idempotency downgrades. Output: report with
  `breaking | risky | compatible` classes; exit code keyed to `breaking`.
- `agent-contract fuzz mcp://localhost:3000` — schema-driven fuzzing (hypothesis): boundary
  values, type confusion, oversized strings, missing/extra fields, malformed JSON framing;
  asserts the error contract (structured errors, no crashes/hangs, bounded response sizes).
  Only runs against explicitly named endpoints (TB9); refuses non-loopback hosts unless
  `--allow-remote <host>` is passed twice-confirmed.
- `agent-contract report --format json|junit|sarif` — CI-friendly.

**MCP adapter:** contracts generated from `tools/list` schemas + ART-extension annotations
(`x-art-side-effect`, `x-art-idempotency` — proposed vendor extensions; absence = `unknown` and
a finding when the tool is high-risk by name heuristics *at low confidence only*). Same runner
tests any MCP server over stdio or HTTP within TB9 bounds.

**Relationship to agent-lint:** contracts, when present, upgrade static confidence (AR002 on a
tool whose contract says `idempotency.supported: false` → confidence high). Contract files are
lowered into IR by a frontend, which is how one artifact serves lint, chaos, and contract testing.

---

## 19. Trace and audit design

**Positioning:** the minimum local substrate needed to explain findings, reproduce failures, show
execution timelines, track ReplaySafe decisions, hold chaos evidence, and audit policy/egress
decisions. Not an observability platform (§3, §6).

**What is recorded (locally, SQLite at `.art/trace.db` per project, or `ART_HOME` override):**
tool-call events (tool name, args *hash* + redacted arg summary per policy, duration, outcome);
ReplaySafe transitions and receipts; approval decisions (actor, action, timestamp);
egress broker decisions (metadata only, §9); chaos runs (scenario, seed, fault schedule,
invariant evaluations); scan summaries (tool versions, counts, duration — no source code).

**What is never recorded:** raw source code; secrets (redaction runs *before* persistence, not at
export); full model prompts/responses by default (opt-in `trace.capture_model_io: true` records
redacted versions with a size cap); environment variables; absolute paths outside the project
root (paths are repo-relative).

**IDs and correlation:** `trace_id` (per run, ULID), `span_id`/`parent_span_id`,
`tool_call_id`, `action_id` (ReplaySafe), `finding_id`, `scenario_id`. ReplaySafe receipts carry
`trace_id` so a ledger row links to its timeline; findings link to fixtures/evidence spans; W3C
`traceparent` accepted/propagated when the host app supplies one.

**Retention & privacy:** default retention 30 days / 500 MB per store, whichever first
**[ASSUMPTION]**; `art trace prune|purge` commands; stores are plain SQLite files the user can
delete; documented paths (no hidden state). Audit events (approvals, egress, force-retries,
ledger transitions) are **hash-chained** (`event_hash = H(prev_hash · payload)`) so tampering is
detectable by `art trace verify-chain`; chains are per-store, no external anchor (documented
limitation — this detects casual tampering, not a root attacker).

**Export:** `art trace export --format otlp-json|json` maps spans/events to OpenTelemetry
semantics (span kind, attributes namespaced `art.*`). No OTLP network exporter in-process before
v1 — export writes files; users ship them with their own collector (keeps the no-network invariant
clean; ADR-015 records this and its revisit trigger).

---

## 20. GitHub Action design

**Form:** composite action (`integrations/github-action/action.yml`) that installs pinned wheels
(`pip install agent-lint==X.Y.Z --no-deps` from a hashed requirements file) and runs the CLI.
No Docker image to maintain initially **[ASSUMPTION: composite over Docker for speed and
supply-chain simplicity; revisit if runner Python matrix hurts]**. Published to the Marketplace as
`agent-reliability/agent-lint-action@v1` with major-version tags; README instructs consumers to
pin by commit SHA.

```yaml
- uses: agent-reliability/agent-lint-action@<sha>   # v0.4.0
  with:
    path: .
    format: sarif                # → uploaded via github/codeql-action/upload-sarif
    fail-on: "new:high"          # severity gate; "none" = report-only
    baseline: art-baseline.json
    changed-files: auto          # auto = derive from PR diff; also: explicit list / "all"
    rules-allow: ""              # allowlist/denylist of rule ids
    rules-deny: "AR012"
    config: .agent-reliability.yaml
    working-directory: packages/agent-app   # monorepo support; run matrix per package
```

Behaviors: SARIF output feeds GitHub code scanning for PR annotations (no PAT needed beyond
default token with `security-events: write`); `network: deny` is *forced* in the Action
environment regardless of repo config (TB7 — scanned repo cannot enable egress in CI);
`fail_on_egress_attempt: true` is forced likewise; logs print finding summaries with terminal-safe
encoding and secrets redacted (CI-log leakage, §25); exit-code mapping documented for non-GitHub
CI reuse (the same runner script works in GitLab/Buildkite — documented, not packaged, pre-v1).
Changed-files mode maps the PR diff to scan scope but *cross-file rules* (AR012-class) note
reduced coverage in the report footer — no silent narrowing.

Supply-chain posture: all third-party actions referenced by SHA; the action's own CI includes a
job that runs it against `examples/` and validates SARIF against the 2.1.0 schema; provenance via
GitHub artifact attestation at v1 (Milestone N).

---

## 21. VS Code design

**Architecture:** thin TypeScript extension over `agent-lint serve --lsp` (JSON-RPC/LSP over
stdio). All analysis stays in the Python process — the extension never re-implements rules
(spec §4.9). Ships only after CLI + rule engine stabilize (Milestone J, after v0.7.0).

Capabilities mapped to LSP: findings → diagnostics (with severity/confidence in the message and
`AR###` codes linking to docs); `explain` → hover/code-action "Explain AR002" opening the
rendered rule page (bundled docs, offline); deterministic quick fixes → code actions (only
`safe`-class fixes; `suggestion` fixes shown but require explicit acceptance); suppression
insertion → code action generating `# art: ignore[…] reason="TODO"` with cursor in the reason
(nudges justification); "Run scan" command; finding-details panel (webview reading JSON output);
configuration UI for severity gates and rule toggles writing `.agent-reliability.yaml`.

Privacy: on first activation the extension shows a workspace notice: "agent-lint runs locally;
no code leaves this machine; network is denied by default" with a link to the privacy doc.
The extension makes no network calls itself (marketplace update checks are VS Code's own);
telemetry APIs unused; CI verifies no `fetch`/`http` imports in the extension bundle.

Discovery of the Python binary: workspace venv → `ART_PATH` setting → PATH; if missing, the
extension offers the pip command, never auto-installs.

---

## 22. MCP plan

**Narrow gap ART owns (spec §4.10):** *reliability* contracts and retry-safety for MCP tools —
not a general MCP vulnerability scanner (existing tools like mcp-scan already cover
injection-focused scanning; docs will link them).

Scope (Milestone K):
1. **Manifest/schema inspection:** `agent-lint scan --mcp <config|url>` lowers `tools/list`
   output into IR Tools; rules: missing timeout guidance, absent side-effect/idempotency
   annotations on risky-named tools (low confidence), wildcard/over-broad permission scopes
   (AR008 with real evidence), tool-count/context-size warnings.
2. **Contract testing:** agent-contract MCP adapter (§18) — snapshot, test, diff, fuzz MCP
   servers; breaking-change detection across server versions is the headline feature.
3. **ReplaySafe wrapping:** `rs.wrap_mcp_tool(session, name, key=…, effect=…)` client-side
   wrapper making any MCP tool call idempotent/verified — works with any MCP client library
   exposing a call function **[ASSUMPTION: adapter targets the official `mcp` Python SDK]**.
4. **Trust-boundary rules:** flag agent code that pipes MCP tool output into high-risk sinks
   without bounds (sharpens AR007/AR009 with MCP evidence).
5. **Prompt-injection test cases:** shipped as *chaos scenarios* (canary-based, deterministic —
   §17), not as a scanner.

**Explicitly rejected:** local MCP proxy mode. Justification: a proxy is a new trust boundary and
availability risk that duplicates what client-side wrapping achieves for our use cases; revisit
(ADR-021) only if wrapping proves insufficient for non-Python clients.

---

## 23. n8n plan

Scope (Milestone L) — analysis of exported workflow JSON plus a small set of runtime nodes; no
workflow editor, no n8n fork.

1. **Static analysis (Python, no TS needed):** `agent-lint scan workflow.json` — the n8n frontend
   lowers nodes/connections into IR (`Node` kinds mapped from node types: HTTP Request → tool +
   side-effect candidate, IF/Switch → router, Wait/Webhook → entry). Rules: N8N001 no error
   workflow/error output on side-effect node; N8N002 retry enabled on non-idempotent node (HTTP
   POST without idempotency header expression); N8N003 webhook without dedupe guard; N8N004 loop
   between nodes without counter guard (AR001 analog); N8N005 credentials referenced in plain
   expression fields; N8N006 missing timeout on HTTP node (AR003 analog). Reports render as text/
   JSON/SARIF like any scan (`--format html` local report **[ASSUMPTION: simple static HTML, no
   server]**).
2. **Runtime nodes (TypeScript, `plugins/n8n/nodes/`, pnpm sub-workspace):** community nodes —
   **ReplaySafe node** (wraps downstream execution with key/claim/receipt against a SQLite/
   Postgres ledger via a small local HTTP shim or direct DB access **[ASSUMPTION: direct
   better-sqlite3 for local n8n; documented Postgres option for hosted]**), **Idempotency-key
   node** (derives and injects keys into HTTP nodes), **Circuit-breaker node** (open/half-open/
   closed with ledger-backed state). Published to npm as `n8n-nodes-agent-reliability`.
3. **Chaos simulation against exported workflows:** interpreter-level simulation of the workflow
   graph with fault injection at node boundaries (no n8n runtime embedded) — validates error
   paths and invariants (`at_most_once` on side-effect nodes) statically-plus-simulated;
   clearly labeled as simulation of the *graph semantics ART models*, not full n8n semantics.

---

## 24. Optional model advisor

Separate package (`model-advisor`), separate install (`pip install agent-reliability-advisor`),
hard security boundary (TB4): core packages have **zero** imports from it; it plugs in via an
entry point the CLI surfaces as `--advise` / `art advise <finding-id>`.

May do (spec §3.3): explain findings in context; suggest patches (rendered as diffs the user
applies manually — never auto-applied); generate test/chaos scenarios (drafts, marked as such);
classify an unknown custom tool (result enters IR as `RiskClassification(source=classifier,
confidence=low)` — deterministic rules decide what that classification *means*, and it can only
*raise* scrutiny, never lower a deterministic finding); summarize traces.

May never do: override/suppress/reclassify deterministic findings; access secrets (redaction
before prompt assembly; canary tests verify); read beyond minimal context (the *finding's*
evidence spans ± N lines, never whole files by default; `--context full-file` requires explicit
flag); send anything except through the Egress Broker (import-linter forbids `httpx/requests/
socket` in the advisor package; broker is injected); act externally; make authorization decisions.

Providers: Ollama-compatible local endpoints; Anthropic-compatible and OpenAI-compatible remote
adapters behind allowlist + approval. Offline mode: `art advise` degrades to the deterministic
`explain` content with a note — full functionality without any model remains intact (spec §14
Q20: the deterministic rule docs, remediation templates, receipts, and reports are the product;
the advisor is commentary).

Auditability (spec §14 Q21): every advisor request/response leaves an audit record (provider,
model, purpose, byte sizes, redaction summary, content hashes, approval actor); `art egress log`
lists them.


---

## 25. Threat model

Assets: user source code and secrets; the developer machine; ledger/trace/audit stores; finding
reports; CI environment; the toolkit's own supply chain. Attacker classes: **A1** author of a
malicious repository the user scans; **A2** compromiser of a dependency/plugin; **A3** malicious
or compromised MCP server / tool endpoint; **A4** local co-tenant process (same user account is
out of scope — no privilege boundary is claimed within one OS user); **A5** network adversary /
malicious model provider; **A6** contributor submitting malicious PRs.

| # | Threat | Attacker / Entry point | Impact | Mitigation | Residual risk | Tests | Milestone |
|---|---|---|---|---|---|---|---|
| T1 | Malicious repo content triggers code execution during scan | A1 / scanned files | RCE on dev/CI machine | Parse-only (`ast.parse`, `json.loads`); no import/exec of target; no `eval` of config; rules get read-only IR | Parser CVEs in CPython | Malicious-repo fixture suite; grep-tests forbidding exec/import-target APIs; fuzz parsers | B, C |
| T2 | Malicious Python syntax / pathological code | A1 / parser | DoS (hang, memory) | File-size cap, AST-node cap, recursion caps, per-file timeout, exit-code 4 partial scan | Extreme cases skip analysis (visible) | Pathological fixtures (deep nesting, huge literals) | C |
| T3 | Malicious workflow JSON (n8n) / manifest (MCP) | A1, A3 | DoS, misleading findings | Schema validation, size/depth caps, no expression evaluation | — | Malformed/hostile JSON fixtures | K, L |
| T4 | Symlink/path traversal during discovery or report write | A1 / repo layout | Read/write outside repo | Symlinks not followed by default; all paths resolved+prefix-checked against root; report paths sanitized | Race (TOCTOU) on exotic FS | FS-safety tests incl. Windows junctions | C |
| T5 | Config injection from scanned repo | A1 / `.agent-reliability.yaml` | Widen egress, load plugins, hide findings | TB7: repo config can only narrow; egress/plugins/telemetry keys ignored (with warning) from repo scope; `yaml.safe_load` only | Suppression abuse (visible via suppressions report) | Config-precedence tests; hostile-config fixtures | B |
| T6 | Secret leakage into findings/traces/SARIF/CI logs | self-inflicted / evidence capture | Credential exposure | Redaction before persistence and before output; entropy+pattern detectors; evidence length caps; SARIF carries spans not file bodies | Novel secret formats missed | Redaction test corpus; canary-secret e2e (plant secret, assert absent from every artifact) | B, E |
| T7 | Prompt injection in source/tool output steering the advisor | A1, A3 / advisor context | Bad advice, exfil attempt via "suggested" egress | Advisor is annotative only (TB4); egress broker approval; minimal-context extraction; injection canaries in advisor tests | User follows bad advice — docs warn | Advisor injection suite (canary must not trigger tool/egress calls) | M |
| T8 | Dependency compromise | A2 / PyPI | Full toolkit compromise | Minimal deps (core: stdlib-only target); uv lockfile with hashes; Dependabot + review policy; release from CI only via trusted publishing (OIDC) | Upstream 0-day window | CI: pip-audit; lockfile-drift check | A, N |
| T9 | Plugin compromise | A2 / entry points | Same as T8 for plugin users | Plugins are explicit installs (TB8); no auto-discovery from scanned repos; compatibility handshake; docs: treat plugins as dependencies | User installs hostile plugin | Plugin-isolation tests (exceptions contained; no rule can reach exec path) | D |
| T10 | Unsafe deserialization | A1 / baselines, ledgers, reports, caches | RCE | No pickle anywhere (banned by lint rule in CI); JSON/SQLite only; schema-versioned parsers reject unknown | — | Deserialization fuzz; pickle-ban test | B+ |
| T11 | SARIF/report injection (markdown/HTML/JS via finding text) | A1 / file contents echoed into reports | XSS in viewers, misleading PR annotations | Encode/escape all evidence; length caps; no raw HTML in reports; SARIF strings sanitized | Downstream viewer bugs | Report-injection fixtures (`<script>`, markdown links) | C, E |
| T12 | Terminal escape injection via filenames/contents | A1 | Terminal hijack, spoofed output | Strip/replace C0/C1 + OSC/CSI sequences in all terminal output; filenames printed repr-safe | — | Escape-sequence fixture tests | C |
| T13 | Malicious filenames (unicode confusables, huge names, reserved names) | A1 | Crashes, path abuse | Normalize + validate; skip-with-diagnostic on invalid | — | Filename torture fixtures | C |
| T14 | Ledger tampering | A4 / SQLite file | Hide double-execution, forge receipts | Hash-chained audit events; `verify-chain` command; file perms 0600; docs: ledger integrity = file integrity within one OS user | Root/same-user attacker wins (documented) | Chain-verification tests incl. tamper cases | F |
| T15 | Idempotency-key collision (accidental or crafted) | A1-adjacent app code | Wrong dedupe → skipped or duplicated action | Namespacing (`action:key`), args_hash check → `KeyReuseError`, key validation, hashing of long keys | Hash collision (SHA-256, negligible) | Property tests for key derivation; collision fixtures | F |
| T16 | Race conditions in claims/locks | concurrency / ledger | Double execution | Single-transaction atomic claims; lease expiry; fencing token checked at receipt write; concurrency test suite with process-level parallelism | Cross-node SQLite misuse (docs forbid; detect NFS and warn) | Stress tests: N workers × M actions, assert at-most-once | F, G |
| T17 | Lock bypass (developer calls effect directly) | app code | Unprotected side effect | Not preventable by a library — mitigated by agent-lint rule (AR004 pattern) + docs; ReplaySafe adapters make wrapped path the easy path | Discipline | Lint fixture: unwrapped call next to wrapped | F |
| T18 | Local privilege boundaries | A4 | Read stores/config of another project | Stores under project dir or `ART_HOME` with 0700/0600; no world-readable defaults; no setuid anything | Same-user malware (out of scope, stated) | Permission-bit tests (POSIX), best-effort Windows ACL note | F |
| T19 | Model provider data exfiltration | A5 / advisor egress | Source/secret leak | Broker: allowlist, redaction, preview, per-request approval, audit metadata; minimal context; offline default | User approves a bad payload | Egress-denial tests; redaction canaries; audit-record assertions | M |
| T20 | CI log leakage | CI echo of findings | Secrets/source in public logs | Redaction on all CLI output; evidence caps; Action masks known patterns; SARIF-only detail mode (`--quiet-logs`) | Repo-specific secrets unknown to detectors | Action e2e asserting canaries absent from logs | E |
| T21 | GitHub Actions supply chain | A2 / action deps | CI compromise of consumers | Composite action, SHA-pinned internals, hashed pip install, no third-party marketplace deps, provenance attestation at v1 | GitHub platform compromise | Action integration test from a clean repo | E, N |
| T22 | VS Code extension trust boundary | A2 / marketplace | Workstation compromise | Thin client (no analysis logic), no network, minimal deps, CI bundle audit, publisher 2FA | Marketplace account compromise | Extension packaging audit test (no net imports) | J |
| T23 | MCP interaction risks (hostile server responses) | A3 / contract tester, wrapper | Parser abuse, oversized payloads, injection into reports | Size/time bounds on all MCP I/O; schema validation; responses treated as untrusted (TB9); no proxy mode | Hostile server wastes a test run | Hostile-MCP-server fixture (oversized, malformed, slow) | K |
| T24 | n8n credential exposure | workflow JSON contents | Credentials in reports | n8n frontend never resolves credentials; expression fields carrying secrets flagged (N8N005) and redacted in evidence | Users paste secrets in odd fields | n8n fixture with planted credentials; assert redacted | L |
| T25 | DoS via huge repos/graphs | A1 / scale | CI burn, hangs | Caps + budgets (T2), changed-files mode, per-package scoping, streaming file walk | Very large monorepos need config | Perf tests: 10k-file synthetic repo under time budget | C, N |
| T26 | Malicious contributor PR (rule with backdoor) | A6 / repo | Supply chain | Rules can't do I/O by API design; CI greps for forbidden calls in rule modules; CODEOWNERS review on engine/broker paths; two-review rule for `agent-core` | Sophisticated obfuscation | CI policy checks; security review checklist in CONTRIBUTING | A, N |

---

## 26. Testing strategy

**Layers (with the owning infrastructure PRs in `PLAN-PRS.md`):**

1. **Unit tests** — per package, colocated (`packages/*/tests/`); pytest; coverage gate 85% on
   `agent-core`/`replaysafe`, 80% elsewhere **[ASSUMPTION]**.
2. **Parser/AST fixture tests** — every frontend has a fixture corpus (`fixtures/frontends/…`)
   with expected-IR golden files (JSON, normalized, schema-validated).
3. **Rule tests / golden files** — per §13: each rule ships true-positive fixtures, safe controls,
   edge cases, `expected.json`. The harness additionally runs **every rule against every safe
   control in the whole fixture library** (cross-rule false-positive net) and keeps a
   **false-negative regression corpus**: every real-world missed-bug report becomes a fixture.
4. **Property-based tests (hypothesis)** — key derivation, fingerprint stability under
   formatting-preserving AST perturbations, redaction idempotence, schema round-trips,
   contract fuzz generators.
5. **Fuzzing** — parser inputs (Python via `ast.parse` guarded, JSON/YAML), SARIF writer
   (arbitrary finding text), contract fuzzer self-test. Nightly CI job, seeds committed on
   failure as regression fixtures.
6. **Concurrency tests** — ReplaySafe: multi-process claim storms (N workers × M duplicate
   deliveries ⇒ exactly one `completed` per key), lease-expiry races, verify-vs-claim
   interleavings (scripted with barrier fixtures).
7. **Crash-recovery tests** — child process SIGKILLed between intent and receipt; assert
   `uncertain` on sweep, correct verify/block behavior; SQLite WAL recovery after kill -9.
8. **Filesystem safety** — symlink/junction traversal, long paths, unicode names, case
   collisions, read-only trees; Windows runners included.
9. **Security tests** — malicious-repo fixture suite (T1–T13 cases); pickle-ban; egress-denial
   (socket guard asserts zero network from every CLI command in offline mode); redaction
   canaries end-to-end (plant → scan/trace/report/SARIF/logs → assert absent); report/terminal
   injection corpus.
10. **Plugin compatibility** — matrix job: LangGraph plugin against pinned LangGraph versions
    (min/max of declared range); handshake rejection tests.
11. **CLI integration** — end-to-end `agent-lint scan` on `examples/` (both unsafe and fixed
    variants; unsafe must produce the documented findings, fixed must be clean); exit-code
    contract tests; `--format` snapshot tests.
12. **Format validation** — SARIF 2.1.0 JSON-schema validation of every emitted report in CI;
    published JSON Schemas for findings/reports/contracts/scenarios validated against examples
    (drift check).
13. **Storage** — SQLite migration tests (create at schema v1 → migrate → verify);
    Postgres adapter tests (service container in CI); Redis lock adapter tests (service
    container); cross-backend semantics parity suite (same scenario, same outcomes).
14. **pytest plugins** — `pytester`-based tests for the chaos and contract plugins.
15. **GitHub Action** — workflow-under-test in this repo: runs the action on `examples/`,
    validates SARIF upload artifact, severity gating, changed-files mode, baseline mode.
16. **VS Code** — extension unit tests + `@vscode/test-electron` smoke (open workspace,
    receive diagnostics from a stub LSP transcript); bundle audit (no network imports).
17. **Offline-mode tests** — the entire integration suite runs in a no-network CI job
    (unshare/net-namespace or socket guard); any egress attempt fails the build.
18. **Performance** — benchmark job (pytest-benchmark): scan throughput on synthetic 10k-file
    repo (budget: < 60 s **[ASSUMPTION: tune at Milestone N]**), ledger ops/sec, chaos overhead;
    regressions > 20% fail.
19. **Reproducible chaos** — every shipped scenario runs twice with the same seed in CI; reports
    must be byte-identical (modulo timestamps, which are normalized).

**Fixture library (`fixtures/`)** is a first-class deliverable: `fixtures/rules/<AR###>/…`,
`fixtures/frontends/…`, `fixtures/malicious/…` (T-cases), `fixtures/repos/…` (synthetic apps:
`unsafe-order-agent`, `safe-order-agent`, `pathological`, `big-synthetic`). Every rule PR must add
≥1 true positive, ≥1 safe control, ≥1 edge case (spec §9) — enforced by a CI check that maps
changed rules to changed fixtures.

---

## 27. Documentation strategy

**Tooling:** mkdocs-material in `docs/`; versioned docs with mike at v1 **[ASSUMPTION]**; rule
catalog generated from rule metadata + per-rule `docs.md` (single source of truth — the same
content backs `agent-lint explain` offline output); JSON Schemas published under `docs/schemas/`;
an offline docs bundle (`art docs --serve` serves the built site locally) for air-gapped users.

**Document set → owning milestone** (every doc listed in spec §10 is assigned):

| Document | Milestone |
|---|---|
| README (repo + per-package) | A (skeleton), N (final) |
| Quickstart (lint), per-tool quickstarts | B/C, F, H, I |
| Architecture overview (+ diagrams) | B, maintained every milestone |
| Threat model (this §25, expanded) | A (initial), N (audited) |
| Privacy & egress | B (broker lands), M (advisor) |
| Rule catalog (generated) | C onward, every rule PR |
| Writing custom rules | C |
| Plugin author guide | D |
| ReplaySafe semantics (state machine, failure table — normative) | F |
| Chaos testing guide + scenario reference | H |
| Contract format reference (normative, schema-versioned) | I |
| CI integration (GitHub + generic) | E |
| VS Code guide | J |
| MCP integration | K |
| n8n integration | L |
| SECURITY.md (disclosure: security@…, 90-day coordinated, GH security advisories) | A |
| CONTRIBUTING, CODE_OF_CONDUCT (Contributor Covenant 2.1), GOVERNANCE (BDFL→maintainer team, documented) | A |
| Release guide, versioning & compatibility policy | A (initial), N |
| FAQ, Troubleshooting | C onward |
| ADRs (`docs/adr/NNN-*.md`, MADR format) | continuous; list in §29 |

**Doc gates:** every PR that changes public behavior must touch docs (CI check: `docs/` or
package README changed, or PR labeled `docs-exempt` with justification). Every rule/scenario/
contract feature ships its reference page in the same PR (spec §3.7).

---

## 28. Release and versioning strategy

- **Cadence:** release when a milestone completes (checkpoints below); patch releases as needed.
- **Versioning:** lockstep across Python packages pre-1.0 (ADR-018); tags `vX.Y.Z`; SemVer
  semantics post-1.0 (public API = documented + `__all__`; `_internal` exempt). VS Code extension
  and npm nodes follow their ecosystems' versioning independently, with a compatibility table in
  docs.
- **Process:** towncrier assembles changelog → release PR bumps versions → tag → CI builds
  sdists/wheels → **PyPI trusted publishing (OIDC, no long-lived tokens)** → GitHub release with
  artifacts + SLSA-style provenance attestation (from Milestone N) → Marketplace/npm publishes for
  their components. A release is blocked unless: full matrix green, offline-mode job green,
  SARIF/schema validation green, docs build green, changelog assembled.
- **Deprecation policy:** deprecate with warning ≥1 minor release before removal; rule removals
  follow §13; config keys get aliases + warnings for one minor.
- **Upgrade/migration (spec §14 Q29):** schema-versioned artifacts (baseline, ledger, contracts,
  scenarios, trace store) each carry `schema_version`; readers accept N and N-1 with automatic
  or command-driven migration (`agent-lint baseline migrate`, `replaysafe migrate`,
  `agent-contract migrate`); migration notes are a required PR field (see PLAN-PRS template);
  ledger migrations are transactional and tested against populated stores.
- **Support window:** latest minor receives fixes; last pre-1.0 minor receives critical security
  fixes for 6 months after 1.0 **[ASSUMPTION]**.

---

## 29. ADR list

ADRs live in `docs/adr/NNN-title.md` (MADR format). Those marked ★ must be written in Milestone A
(they gate everything); the rest are written in the milestone that implements them. Each row
records decision · context/options · trade-offs & consequences · revisit trigger.

| ADR | Decision | Context & options considered | Trade-offs / consequences | Revisit trigger |
|---|---|---|---|---|
| 001 ★ Monorepo | Single repo, uv workspace | Multi-repo (independent cadence) vs monorepo (atomic cross-package change, one CI, shared fixtures) | Heavier CI; path-filtered jobs mitigate. Atomic refactors while pre-1.0 APIs move | A package needs an external release cadence (e.g. replaysafe adopted widely standalone) |
| 002 ★ Apache-2.0 | Apache-2.0 + NOTICE | MIT (simpler) vs Apache-2.0 (patent grant, enterprise comfort) — spec mandates | NOTICE upkeep | Never (license changes are traumatic) |
| 003 ★ Python-first | Python 3.10–3.13; TS only for VS Code/n8n nodes | TS-first, dual-language core | Reaches LangGraph/MCP/pytest audience first; n8n static analysis still possible (JSON is data) | TS agent frameworks demand a TS analyzer (post-v1 plan §3) |
| 004 ★ AST strategy | stdlib `ast`, parse-only, never execute; no libcst/tree-sitter in core | libcst (format-preserving, heavier), tree-sitter (multi-lang, C dep) | Loses format-preserving autofix edits → fixes use span-based text edits with re-parse validation; zero native deps | Multi-language IR (tree-sitter becomes attractive); autofix fidelity problems |
| 005 ★ Intermediate representation | Frontends lower to shared IR; rules read IR + raw-AST escape hatch; `UNKNOWN` first-class | Rules directly on AST (simple, framework-coupled) vs IR (portable rules) | IR design cost up front; rules become portable across LangGraph/n8n/MCP | IR can't express a new framework's semantics without contortion |
| 006 Plugin system | Python entry points, explicit install, compat handshake, per-callback isolation | Import-path config; subprocess plugins (isolation but IPC cost) | In-process = fast, trusted-dependency model (TB8); no sandbox claimed | Evidence of plugin ecosystem needing sandboxing |
| 007 ★ Local-first | All core function offline; `network: deny` default | Hosted control plane (rejected by spec) | No usage insight (accepted); trust story is the product | Never for core; hosted *additions* post-v1 possible |
| 008 ★ No telemetry | Zero telemetry; future telemetry = explicit opt-in + own ADR | Opt-out telemetry (norm elsewhere) | Blind to usage; compensate with GitHub discussions/issue templates | Never for default-on |
| 009 ★ Egress broker | Single choke point, allowlist+preview+audit; CI socket-guard | Per-component HTTP clients | One hard boundary to test; slight ceremony for advisor | New egress class (e.g. OTLP push) — must still go through broker |
| 010 SARIF | SARIF 2.1.0 first-class + JSON native format | Custom format only | SARIF unlocks GitHub/IDE ecosystems; fingerprint discipline required | SARIF 3.x adoption |
| 011 ★ SQLite first | SQLite (WAL) for ledger/trace/baseline stores | Postgres-first (server dep), files/JSON (no transactions) | Single-node truth; NFS misuse detected+warned; Postgres later (G) | — (Postgres adapter is the planned answer) |
| 012 ReplaySafe state model | pending→started→completed/failed/uncertain(+compensated); intent-before-effect | Two-phase records vs post-hoc logging vs full event sourcing | Every effect costs 2 ledger writes (~ms); crash ambiguity becomes explicit `uncertain` | Event-sourcing needs (full history replay) |
| 013 Idempotency semantics | At-most-once + verify-before-retry; never "exactly-once" claims; `KeyReuseError` on args drift | Exactly-once marketing (dishonest); at-least-once default (unsafe for money) | Some flows need verify hooks to make progress after uncertainty | — |
| 014 Locking strategy | Ledger-claim-as-lock (SQLite), `FOR UPDATE SKIP LOCKED` (PG), lease+fencing (Redis, advisory) | Separate lock service; file locks | No new infra; cross-node guarantees honestly labeled advisory | Distributed-correctness demand → recommend Temporal-class tools instead |
| 015 OTel compatibility | OTLP-JSON file export; no in-process network exporter pre-v1 | Full OTel SDK dependency | Keeps no-network invariant testable; users bring collectors | Strong demand for direct OTLP push (would route via broker) |
| 016 Rule authoring & versioning | Rules are Python modules with metadata; integer rule versions; majors change fingerprints; IDs never reused | YAML/DSL rules (limited power, safer authoring) | Python power + fixture-harness safety rails; DSL deferred | ≥3 orgs blocked by needing non-programmatic rules |
| 017 Baseline design | Fingerprint set file, `new`/`existing` classification, `--fail-on new:sev`; criticals not baselined by default | Suppress-by-inline-only; date-based baselines | Adoptable in brownfield repos day one; baseline file churn managed by stable fingerprints | Fingerprint algorithm change (needs `baseline migrate`) |
| 018 Suppression design | Mandatory justification, default expiry, suppressions report; expired = reactivated | Permanent suppressions (blind spots) | Slight friction; auditability of ignores | — |
| 019 Release/versioning | Lockstep pre-1.0, SemVer post-1.0, towncrier, trusted publishing | Independent versions (matrix pain) | One version to reason about; forces whole-train releases | Post-1.0 if packages mature at different rates |
| 020 Model advisor isolation | Separate package, entry-point plug-in, annotative-only, broker-only egress | Advisor inside agent-lint (convenient, dangerous) | Import-linter + canary tests keep the boundary honest | Never weaken; revisit only to tighten (e.g. subprocess isolation) |
| 021 TS/n8n workspace | pnpm sub-workspaces under `integrations/vscode` and `plugins/n8n/nodes` only | TS at repo root; separate repos | Python contributors never touch Node; CI path-filtered | TS analyzer post-v1 → dedicated workspace design |
| 022 MCP scope | Reliability contracts + wrapping only; no general MCP security scanner; no proxy | Proxy mode (new trust boundary), full scanner (crowded space) | Differentiated, small surface; links out to mcp-scan et al. | Wrapping insufficient for non-Python clients → reconsider proxy |

---

## 30. Milestone plan (architecture roadmap — not automatically committed)

Milestones A–N are the **architecture roadmap**: they show how the complete system decomposes
and what "done" means for each component. They are **not automatically committed** — commitment
status is per milestone below. **Committed** work lives in `EXECUTION.md` (E01–E14, which
resequences and narrows Milestones A–E); **gated** milestones proceed when their §37 validation
gate opens (or via a documented gate override); **optional** components may never be built
without harming v1.0; **validation-only** means scope is set by which gates actually opened.
Every milestone, when executed, still ends with main releasable and all gates green (spec §3.7).
PR details: [`PLAN-PRS.md`](PLAN-PRS.md).

Release numbers in this table are the original architecture-era ladder; the committed wave
redefined v0.1.0–v0.5.x (see `EXECUTION.md`). Gated milestones ship under the next available
version when they open — their *content* promises are unchanged.

| Milestone | Goal | Catalog PRs | Release (architecture-era) | Commitment status | Exit criteria |
|---|---|---|---|---|---|
| **A — Repository & governance foundation** | Complete OSS repo skeleton: license, governance, CI, fixtures scaffold, first ADRs | PR-001…004 | — | **Committed** in minimal form (E01); full governance behind the governance-expansion gate | CI green on installable package; minimal governance docs present; decision log started |
| **B — Core domain & CLI walking skeleton** | `agent-lint scan` returns one real finding (AR001) end-to-end; offline guard in place | PR-005…011 | v0.1.0 | **Committed** (E02–E04); Egress Broker *object* deferred to the advisor gate (socket guard stands in) | Fixture scan produces AR001 in text; socket-guard CI green; PyPI package installs |
| **C — Static analyzer MVP** | 12+ deterministic rules, SARIF, baselines, suppressions, explain, hardening | PR-012…023 | v0.2.0 | **Committed** as a subset (E05–E07, E10, E13: 7 rules + SARIF + suppressions + baselines + hardening); remaining rule depth decided at E14 | Shipped rules pass fixture harness incl. cross-rule FP net; SARIF validates; unsafe example yields documented findings, safe variant clean |
| **D — LangGraph plugin** | Framework-aware IR + LG-rules; plugin loading proven | PR-024…031 | v0.3.0 | **Committed** in reduced, in-package form (E08–E09: recognition + LG002/LG003/LG006); plugin *loading* (PR-024) and remaining LG rules **gated** | LangGraph fixtures produce LG/AR findings with framework evidence; negative-detection corpus clean |
| **E — CI integration** | GitHub Action, SARIF upload, changed-files, log hygiene | PR-032…036 | v0.4.0 | **Committed** in minimal form (E11: path/format/fail-on; E13 adds changed-files/baseline) | Action runs on examples in CI; annotations visible; canary secrets absent from logs |
| **F — ReplaySafe MVP** | SQLite ledger, decorator, claims, verify-before-retry, compensation, CLI | PR-037…045 | v0.5.0 | **Gated** — ReplaySafe gate (§37) | Crash/concurrency suites green; duplicate-delivery demo executes the charge once (deduped, ambiguity blocked); semantics doc normative |
| **G — ReplaySafe production adapters** | Postgres, Redis locks, stress suites, AR012 | PR-046…052 | v0.5.x | **Gated** — Postgres/Redis gate (§37); requires F | Backend parity suite green on SQLite+PG; storm tests: duplicates deduped, no ambiguous re-execution |
| **H — Agent Chaos MVP** | Scenario runner, fault catalog, invariants, pytest plugin | PR-053…060 | v0.6.0 | **Gated** — chaos gate (§37) | Shipped scenarios reproduce byte-identically by seed; staged isolation model enforced and documented; ReplaySafe acceptance scenarios green |
| **I — Agent Contract MVP** | Contract format, test/diff/fuzz, IR feedback | PR-061…067 | v0.7.0 | **Gated** — contract gate (§37) | Contract suite runs on example tools + MCP fixture server; diff catches seeded breaking changes; fuzz finds seeded error-contract bug |
| **J — VS Code integration** | LSP service + thin extension | PR-068…072 | v0.8.0 | **Gated** — VS Code gate (§37) | Extension shows diagnostics/quick fixes on example repo; bundle audit green; marketplace listing |
| **K — MCP reliability support** | Manifest frontend, contract adapter, wrapper, trust rules | PR-073…077 | v0.9.0 | **Gated** — MCP gate (§37) | MCP fixture server: scan+contract+wrap all work within TB9 bounds |
| **L — n8n support** | Workflow analysis + reliability nodes + simulation | PR-078…083 | v0.9.x | **Gated** — n8n gate (§37) | n8n fixture workflows yield N8N findings; nodes pass n8n lint & publish to npm; simulation validates error paths |
| **M — Optional model advisor** | Isolated advisor, local+remote providers, approval UX | PR-084…087 | v0.9.x | **Optional** — advisor gate (§37); optional forever, never a security authority | Offline degradation test green; injection canaries never trigger egress; audit records complete |
| **N — v1 hardening** | Security audit, perf, API freeze, migrations, docs, supply chain | PR-088…095 | v1.0.0 | **Validation-only** — scope set by which gates opened; hardening applies to whatever shipped | §36 definition of readiness fully checked for the shipped scope |

Sequencing notes (architectural dependencies, valid whenever gates open): F/G (runtime plane)
share no code path with D/E (analysis plane) beyond `agent-core`, so waves can parallelize once
the core exists; H depends on F (ledger invariants) and the scripted stub only; I depends on C
(IR) not on H. The E14 evidence review is the standing mechanism that converts gated milestones
into committed waves.

---

## 31. Architectural PR catalog

The full catalog — one subsection per PR with all 25 required fields — is in
[`PLAN-PRS.md`](PLAN-PRS.md): **95 PRs**, PR-001…PR-095, grouped by milestone A–N in
*architectural dependency order*, with release-boundary PRs flagged. The catalog proves the
system has been decomposed end to end; **it is not the committed merge order**. The active
sequence is `EXECUTION.md` (E01–E14), which maps onto catalog PRs via the table in
`PLAN-PRS.md`'s header; later catalog PRs may be reordered, merged, split, or deferred after
validation. Complexity distribution: ~30 small, ~45 medium, ~20 large. ~35 PRs are marked
external-contributor-friendly (rules, fixtures, fault adapters, docs).

---

## 32. Release checkpoints

**Committed** releases come from `EXECUTION.md`; **gated** rows below describe the release
*content* each gated milestone delivers when its §37 gate opens (under the next available
version number at that time — the architecture-era numbers are kept for reference only).

| Version (architecture-era) | Boundary PR | Contents (cumulative) | Commitment status | "Why anyone installs it" |
|---|---|---|---|---|
| v0.1.0 | E04 (catalog PR-009) | CLI + safe parsing + AR001, offline guarantee | **Committed** | Early adopters validate the approach; the finding is real |
| v0.2.0 | E07 (catalog PR-012/013/015/021 subset) | AR001/003/014, JSON/SARIF, explain, suppressions | **Committed** | **First genuinely useful release** — standalone lint value |
| v0.3.0 | E09 (catalog PR-025…028 subset) | LangGraph-aware findings | **Committed** | The LangGraph community's linter |
| v0.4.0 | E12 (catalog PR-033…035 subset + launch) | Hardened scanner + GitHub Action + public launch | **Committed** | Team-wide enforcement without infra, safe on untrusted repos |
| v0.5.x | E13 (catalog PR-014…017/032 subset) | Baselines, changed-files, suppression lifecycle, AR002/AR011 | **Committed** | Brownfield adoption + the retry-safety headline |
| — | PR-045 (+G) | ReplaySafe SQLite runtime (then PG/Redis) | **Gated** (ReplaySafe gate) | Retry-safety in an afternoon |
| — | PR-060 | Agent Chaos MVP | **Gated** (chaos gate) | Prove invariants under faults in CI |
| — | PR-067 | Tool contracts MVP | **Gated** (contract gate) | Stop breaking tool changes at review time |
| — | PR-072 | VS Code integration | **Gated** (VS Code gate) | Findings where developers live |
| — | PR-077 (+L/M) | MCP support (then n8n, advisor) | **Gated** (MCP/n8n gates; advisor optional) | Reliability for the MCP ecosystem |
| v1.0.0 | PR-095 | Hardened, audited, stable APIs for the shipped scope | **Validation-only** | Production-credible commitment |

Architectural sequencing rationale (valid whenever gates open): lint-first builds the audience
and the IR every later component reuses; ReplaySafe before chaos because chaos's most valuable
invariants query the ledger; contracts benefit from field experience but can open earlier with
no dependency violation. The E14 evidence review decides actual order.

---

## 33. Critical risks

| # | Risk | Likelihood/Impact | Mitigation in plan |
|---|---|---|---|
| R1 | **False-positive rate kills adoption** (lint cries wolf) | High/High | Confidence model + `UNKNOWN` discipline (§11); cross-rule FP net over all safe fixtures (§26); baseline+suppression UX (§13); v0.2 ships only high-confidence rules by default |
| R2 | **LangGraph API churn** breaks the plugin | High/Medium | Shape-matching not imports (§15); version matrix CI (PR-030); untested-version diagnostics; plugin releases decoupled via lockstep train patches |
| R3 | **ReplaySafe correctness bug** (double side effect despite the pitch) | Medium/Critical | Intent-before-effect ordering; crash/concurrency suites as release gates (PR-042/049); honest at-most-once claims; external security/correctness audit at N |
| R4 | **Scope creep into observability/orchestration** | Medium/High | §3 non-goals; §6 positioning docs; ADR-007/022 revisit triggers; PR template requires non-goals |
| R5 | **Static claims overreach** (marketing writes checks AST can't cash) | Medium/High | §15 "explicitly out of reach" list is normative; every rule doc states detection limits; `UNKNOWN` semantics |
| R6 | **Solo-maintainer bus factor / contributor drought** | Medium/Medium | 35 contributor-friendly PRs; rule authoring guide + fixture harness make rules a 1-file contribution; GOVERNANCE.md defines maintainer path |
| R7 | **Security incident in the toolkit itself** (ironic, fatal to trust) | Low/Critical | Threat model with tests per threat (§25); malicious-repo fixtures in CI; SECURITY.md disclosure; audit at N; minimal dependencies |
| R8 | **Chaos harness touches something real** | Low/Critical | No production mode exists; socket-guard enforcement; simulation-only defaults (§17) |
| R9 | **Plan stalls before value** | Medium/High | The committed wave (`EXECUTION.md`) front-loads value: first real finding at v0.1.0 (E04), useful standalone linter at v0.2.0, public launch at v0.4.0; every release independently useful; later work is gated, so a stall strands no half-built component |
| R10 | **n8n/TS scope drags Python velocity** | Medium/Low | Isolated workspaces (ADR-021); n8n is gated (§37) and skippable without affecting v1 core claims |
| R11 | **Validation gates never open** (demand exists but signals never cross thresholds, or the audience never finds the project) | Medium/High | Gates are demand *instruments*, not passive waiting: findings and issue templates actively measure demand (AR002/AR011 link "did this bite you?"); gate overrides available through public ADR; periodic E14-style reassessment with a scheduled review date; maintainers may choose more lint depth instead of waiting — forward motion never requires a gate |

---

## 34. Open questions and assumptions

All labeled **[ASSUMPTION]** items are collected here; each is safe to proceed on and cheap to
change at the flagged point.

1. Python floor 3.10 / ceiling 3.13 — confirm against LangGraph floor at PR-002.
2. Typer for CLI — confirm at PR-009 (Click acceptable; no functional impact).
3. Default suppression expiry 180 days; trace retention 30 days/500 MB — product-tune before v0.2/v0.5.
4. Composite GitHub Action (no Docker) — confirm at PR-033 against runner Python availability.
5. Alembic for Postgres migrations — confirm at PR-047.
6. Official `mcp` Python SDK as wrapper target — confirm at PR-073 (ecosystem moves fast).
7. n8n nodes use better-sqlite3 locally / Postgres hosted — confirm at PR-080.
8. mkdocs+mike versioned docs — confirm at PR-092.
9. Coverage gates (85/80) and perf budget (10k files < 60 s) — ratify at PR-022/089.
10. Milestone L (n8n) is the designated de-scope if v1.0 timing demands — decide at v0.9.0.
11. Name availability: `agent-lint`, `replaysafe`, `agent-chaos`, `agent-contract` on PyPI, and
    the GitHub org name — **must be verified at PR-001; fallbacks (`art-lint`, `art-replaysafe`,
    …) reserved in the same PR.** This is the only assumption that blocks the first PR.
12. LG-rule final list (§15) — confirm against real-world LangGraph fixture corpus at PR-025.

No open question blocks PR-001…PR-011 except #11, which PR-001 resolves.

---

## 35. Recommended first implementation PR

**E01 — Minimal OSS bootstrap** (full detail in `EXECUTION.md`) starts the repository: license,
minimal governance, one CI workflow, the single `agent-lint` distribution with the permanent
`agent_reliability.{core,lint}` namespace, and the PyPI name verification (#11 above). It is
deliberately boring — the first *product value* ships in **E04**, where
`agent-lint scan fixtures/rules/AR001/unsafe` prints a real finding with a real rule ID, offline,
end to end through parser → micro-IR → rule → reporter, released as **v0.1.0**. Everything
between E01 and E04 exists only to make E04 honest (final-shaped contracts, safe frontend). An
implementing agent should treat E04 as the first milestone-defining target and E01–E03 as its
shortest honest path. (The catalog equivalents, PR-001/PR-009, remain in `PLAN-PRS.md` as the
architecture-era decomposition.)

---

## 36. Definition of v1.0 readiness

v1.0.0 ships when **all** of the following are demonstrably true (each maps to a Milestone N PR):

1. **Spec quality gate (§18) re-verified:** every product component implemented per this plan or
   its ADR-documented amendment; no component depends on any hosted service.
2. **Offline completeness:** entire test suite passes in the no-network CI job; `art doctor
   --assert-offline` clean on a fresh air-gapped install (documented procedure executed).
3. **Security:** external audit of `agent-core`, `replaysafe`, egress broker, and the Action
   completed; all critical/high findings fixed; threat-model table (§25) has a passing test per
   row; 90-day disclosure process live with a tested contact path.
4. **Correctness:** ReplaySafe crash/concurrency/parity suites green on SQLite+Postgres across
   the OS matrix; chaos reproducibility check green; at-most-once demo runs in CI.
5. **Stability contracts:** public APIs frozen and documented (`__all__` audit); finding schema,
   SARIF fingerprints (`art/v1`), contract format, scenario schema, baseline format, ledger
   schema all versioned with N/N-1 migration commands tested against populated artifacts.
6. **Performance:** 10k-file synthetic repo scans within budget; benchmark regression gate armed.
7. **Docs:** every §27 document exists and is versioned; rule catalog complete with limits
   stated per rule; ReplaySafe semantics doc is normative and matches implementation (tested by
   doc-example execution).
8. **Supply chain:** trusted publishing, SHA-pinned CI, SBOM + provenance attestations on all
   release artifacts; lockfile-hash verification in CI.
9. **Community:** ≥ the governance docs' maintainer quorum; contributor ladder documented; rule
   contribution demonstrated by at least one external-authored rule merged.
10. **Credibility demo (spec §14 Q30):** a public, reproducible case study — the example order
    agent — showing: lint catches the seeded defects; ReplaySafe survives the duplicate-webhook
    and crash chaos scenarios with the payment invariant proven; the whole story runs offline in
    one `make demo`.

---

## 37. Validation gates

Every component beyond the committed execution wave proceeds through a gate: a measurable,
publicly tracked demand signal. Gates are **decision aids, not scientific laws** — and they must
not become permanent vetoes (see the override rule below). Gate status is tracked on the public
roadmap page; the E14-style evidence review (recurring after every wave) scores each gate and
publishes the decision as an ADR. `EXECUTION.md` carries the same gates operationally; this
section is normative.

| Gate | Opens when | Notes |
|---|---|---|
| **ReplaySafe** (Milestone F) | *Standard:* ≥5 distinct retry/resume/duplicate-side-effect failure reports, from ≥3 independent users/teams/orgs, with ≥2 reproducible as fixtures or minimal examples. *Severe-event exception:* one severe, reproducible incident — payment duplication, destructive duplicate action, high-cost runaway retry, or compliance-impacting uncertain execution — may open the milestone via ADR | AR002/AR011 findings link the "did this bite you?" template — the gate's primary instrument |
| **Agent Chaos** (Milestone H) | ≥3 independent users/teams request reproducible fault testing; ≥2 requested scenarios representable as deterministic fixtures; ReplaySafe or agent-lint has already exposed concrete failure classes worth testing | |
| **Agent Contract** (Milestone I) | ≥3 distinct schema-drift/parameter-drift/tool-contract regression cases reported; ≥2 with before/after schemas, code, or fixtures; plain JSON Schema validation shown insufficient | |
| **MCP** (Milestone K) | A user or maintainer provides a concrete MCP integration target; a reproducible fixture/manifest/test server exists; the need is clearly differentiated from existing MCP security scanners | ADR-022 scope doctrine still applies |
| **n8n** (Milestone L) | Any of: ≥3 real exported workflows available as sanitized fixtures; a contributor commits to maintaining n8n fixtures; a repeated reliability failure appears across multiple workflows | |
| **Plugin entry-point loading** (catalog PR-024) | A third-party adapter is proposed; it must ship outside the main distribution; the Frontend/Rule contracts have survived ≥2 public releases | Until then, first-party integrations are internal modules behind the same contracts |
| **PostgreSQL/Redis backends** (Milestone G) | ≥2 ReplaySafe users require multi-process/multi-host coordination; SQLite limitations reproduced and documented; Ledger/Lock contracts stable | Requires F open |
| **VS Code** (Milestone J) | CLI output and rule IDs stable for ≥2 public releases; ≥10 explicit requests/confirmations that editor integration would materially help; the extension reuses the engine with zero duplicated analysis logic | |
| **Model advisor** (Milestone M) | Users explicitly request model-assisted explanation/patch generation; deterministic explain/remediation already mature; the Egress Broker exists; payload preview, redaction, allowlisting, approval implemented | **Optional forever. Can never become a security or authorization authority** |
| **Governance expansion** | 5+ non-maintainer contributors, recurring review conflicts, multiple maintainers/release owners, or security-sensitive external plugins | Do not front-load governance bureaucracy |
| **Package split** (`agent-reliability-core` as own distribution) | ReplaySafe needs a runtime-neutral core, a third-party plugin needs a stable dependency, or products need independent release cycles | Never split merely because a version number was reached |

**Gate override rule.** Maintainers may open a gated milestone without meeting the numeric
threshold when one of these applies: severe reproducible failure; strategic integration; funded
or committed contributor; ecosystem change; security incident; strong maintainer evidence. Every
override requires a **public ADR** with the evidence, explicit trade-offs, a review date, and
success/failure criteria.

---

## 38. Open-source strategy

The community model, designed alongside the architecture rather than after it. `EXECUTION.md`
carries the short practical form; this section is the full version.

### 38.1 Contributor onboarding

The path from stranger to first merged PR is designed to take **under 30 minutes**: clone →
`uv sync` → `pytest` (green on first run, no services) → `agent-lint scan fixtures/rules/AR001/unsafe`
(see a finding) → copy an existing rule directory and modify it. CONTRIBUTING.md is written as
exactly this walkthrough, and a maintainer re-validates it (with a stopwatch) each release.

### 38.2 How to add a rule

A rule is one directory: `rule.py` (logic + metadata), `docs.md` (catalog page + explain
content), `fixtures/` with **at least one true positive, one safe control, one edge case**, and
`expected.json` (exact expected output). The `art-rule-test` harness enforces the contract
mechanically — including the cross-rule false-positive net (no rule may fire on any safe control
repo-wide). Rules cannot perform I/O by construction (the `RuleContext` API exposes none), so a
rule PR needs only ordinary review. The add-a-rule guide walks through AR003 as the reference.

### 38.3 How to contribute a failure fixture

Users can contribute: sanitized code, a simplified reproduction, a workflow fragment, a trace
excerpt, the expected safe/unsafe behavior, and tool/framework versions. A dedicated issue
template collects these; maintainers (or the contributor) convert them into fixture directories.
**Fixtures become part of the permanent regression suite** — they are never deleted, only
superseded, and each carries provenance metadata (source issue, versions).

### 38.4 Good-first-issue design

Good-first issues are **bounded by construction**: add a safe-control fixture; add an SDK
call-pattern/known-tool table entry (with a documentation citation); improve a rule explanation;
add a malformed-input case; document a false positive; add a secret-format redaction case.
Architecture changes, security boundaries, parser internals, and fingerprint/redaction logic are
**never** labeled good-first. Each seeded issue names the exact files to touch and the test that
proves completion.

### 38.5 Maintainer review boundaries

Two review tiers. **Maintainer-gated** (stronger review, CODEOWNERS once volume justifies it):
engine internals, parser safety, fingerprint algorithm, redaction, network policy and the socket
guard, security boundaries, ReplaySafe state semantics (when gated open), plugin loading.
**Open path** (any maintainer approval): rules, fixtures, table entries with citations, docs,
examples. The boundary is documented in CONTRIBUTING.md so external contributors know which
lane they're in before writing code.

### 38.6 Plugin compatibility

A stable contract version (`CORE_API_VERSION`), explicit compatibility metadata in plugin
distributions (`core_api_version_required`), a public deprecation policy (≥1 minor release of
warning), **no silent plugin activation** (installed ≠ enabled for third-party plugins), and
third-party plugins treated as trusted dependencies the *user* chose — the same trust model as
any package in their environment (TB8). First-party integrations remain internal modules until
the plugin-loading gate opens, behind the same contracts.

### 38.7 Public RFC process

Major changes — new components, schema changes, security-boundary changes, gate overrides —
start as a **GitHub Discussion with an RFC document**: motivation, design, alternatives
considered, security/privacy impact, migration plan. After a comment window, the decision is
recorded as an ADR (superseding the lightweight `docs/DECISIONS.md` log from launch onward).
Rule additions and fixtures do not need RFCs.

### 38.8 Release communication

Every release ships notes answering: what problem was solved; a demo (recording or transcript);
the install command; breaking changes; known limitations (honest, specific); contribution
requests ("we need SDK table entries for X"); and **open validation questions** ("does AR011's
posture match your codebase? tell us here"). Releases are announced in the same channels every
time so the community knows where to look.

### 38.9 Community feedback loops

Instruments, not vibes: issue templates (bug report, false positive, **"did this catch a real
bug?"**, **"did this bite you?"** on retry-safety findings); GitHub Discussions categories (Q&A,
rule ideas, failure stories, roadmap); public roadmap voting (reactions on gate-tracking
issues); release feedback threads. Every instrument feeds the recurring E14-style evidence
review that scores validation gates.

### 38.10 Bug report → regression fixture pipeline

1. User reports (any template).
2. Maintainer or contributor reproduces.
3. Reproduction is sanitized (secrets/identifiers stripped, minimal form).
4. Converted into a fixture directory with provenance metadata.
5. A failing regression test lands *first*.
6. The fix lands, turning the test green.
7. The fixture is kept permanently (false-negative corpus or rule fixtures).
8. The contributor is credited in the changelog when they permit it.

### 38.11 Adoption data without telemetry

The project ships **no phone-home telemetry, no repository fingerprinting, no hidden analytics —
permanently** (§3.4 is unchanged by community needs). Adoption evidence uses only public or
user-supplied signals: GitHub stars/forks (weak awareness signal only); issues and discussions;
contributor counts; the public dependency graph; public GitHub Action usage visible in
consumers' workflows; **PyPI downloads as a trend only — explicitly not proof of active use**;
fixture submissions; explicit confirmations of caught bugs (the strongest signal — each becomes
a case study with permission); repeat participants in discussions. The E14 scorecard evaluates
every gate against these signals and says which were used.

---

## Appendix A — Explicit answers to the 30 required questions (spec §14)

1. **Smallest useful first release?** v0.1.0 is the walking skeleton; **v0.2.0 is the smallest
   *useful* release**: `agent-lint` with 12+ deterministic rules, SARIF/JSON, baselines,
   suppressions, explain — standalone value with zero infrastructure (§32).
2. **First three rules?** AR001, AR003, AR014 — highest frequency, pure-AST detectable, high
   confidence, low FP risk, and together they exercise loop analysis, call-site analysis, and
   retry lowering (§14).
3. **Reliable without executing user code?** Parsing (`ast`), import/call-shape matching, graph
   topology from literal builder calls, retry/timeout policy lowering from known libraries,
   annotation/contract reading, intra-file explicit dataflow, workflow-JSON structure analysis
   (§13–15). Everything else degrades to `UNKNOWN`.
4. **How is LangGraph code recognized?** Import match + construction-shape match
   (`StateGraph`, `add_node/add_edge/compile`, `@tool`, `create_react_agent`), declared
   version range, untested-version diagnostics (§15).
5. **How are custom tools classified?** Layered: explicit annotations/contracts (authoritative) →
   known-SDK table (stripe/boto3/smtplib… ) → deterministic name+callsite heuristics (low
   confidence) → optional advisor classification (can only raise scrutiny, `source=classifier`);
   `unknown` is a legitimate terminal state (§11, §24).
6. **How are side effects represented?** `SideEffect` IR nodes with class
   (`read/notify/write/destructive/financial`), idempotency/audit evidence, and provenance of the
   classification (§11).
7. **How are unsafe retries detected statically?** RetryPolicy lowering (tenacity/stamina/loops/
   framework config) intersected with wrapped call graphs containing non-idempotent SideEffects
   without idempotency evidence (AR002), unbounded policies (AR014), and uncertain-success
   failure modes without verify steps (AR011) (§14).
8. **What cannot be detected statically?** Dynamic graph construction, runtime config, actual
   endpoint idempotency, checkpoint durability, cross-module dynamic dispatch, real
   concurrency schedules — enumerated normatively in §15 and per-rule docs; IR encodes them as
   `UNKNOWN` rather than guessing.
9. **Uncertain success in ReplaySafe?** Intent-before-effect ordering makes uncertainty explicit
   (`uncertain` status); verify hooks resolve it; without a verifier, policy blocks/compensates/
   escalates — never silent retry (§16).
10. **Idempotency keys?** Developer-supplied key function, namespaced per action, validated
    (size/charset), args-hash guarded against reuse-with-different-args (`KeyReuseError`);
    `AUTO` mode documented with caveats (§16).
11. **Ledger unavailable?** Fail closed for effectful actions; configurable fail-open for reads
    only; never buffer effects in memory (§16).
12. **Concurrent execution?** Atomic single-transaction claims with leases; losers get
    `ActionAlreadyClaimed`/await; fencing tokens at receipt write; cross-node honesty per
    backend (§16, ADR-014).
13. **Compensation actions?** `compensate=` hooks per action, executed under policy from
    `uncertain`/`failed`, bounded retries, `compensation_failed` escalation to approval;
    compensation is itself audited (§16).
14. **Chaos vs production?** No production mode exists; `simulation` (all I/O through doubles,
    socket-guard aborts on real connections) or `sandbox` (explicit local allowlist) only (§17).
15. **Invariant evaluation?** Compiled deterministic evaluators over persisted trace stream +
    ledger + counters, post-run, evidence-linked; custom invariants are project Python callables
    on a read-only view (§17).
16. **Report stability?** Schema-versioned JSON (findings/chaos/contract), N/N-1 reader policy,
    golden-file CI, documented field deprecation (§26, §28).
17. **SARIF fingerprint stability?** `partialFingerprints["art/v1"]` from structural AST hash
    excluding positions; algorithm versioned; `baseline migrate` on algorithm change (§13).
18. **Suppressions vs blind spots?** Mandatory justification, default expiry with reactivation,
    `suppressions report` for periodic review, unjustified suppression is itself a finding,
    criticals not baselineable by default (§13).
19. **Plugin compatibility?** `core_api_version_required` SemVer range handshake at load,
    visible skip diagnostics, matrix CI for first-party plugins (§12).
20. **Useful without an LLM?** Every engine is deterministic; explain/remediation content is
    authored, offline; the advisor adds commentary only — offline mode is the default and the
    complete product (§9, §24).
21. **Remote-model isolation/audit?** Separate package, broker-only egress, allowlist, redaction,
    preview, per-request approval, audit metadata records, import-linter enforcement, canary
    tests (§9, §24, T19).
22. **Core vs plugins?** Core: domain model, engines, generic Python frontend, generic AR-rules,
    broker, trace. Plugins: anything framework-specific (frontends, rules, enrichers, adapters)
    (§12).
23. **Overlapping tools?** LangSmith/Langfuse/AgentOps, Semgrep/Bandit/CodeQL/Ruff, Guardrails/
    NeMo, mcp-scan, Temporal/Restate/DBOS, tenacity/stamina, promptfoo/DeepEval/Giskard,
    pact/schemathesis — positions and boundaries in §6.
24. **Exact gap owned?** Deterministic, local-first reliability enforcement at the agent
    execution layer: agent-domain static rules + serverless retry/idempotency runtime +
    agent-specific fault injection + tool-contract regression — no existing tool covers two of
    these locally (§6).
25. **Not built before v1?** The spec §15 list verbatim, plus: no rule DSL, no MCP proxy, no
    TS analyzer, no in-process OTLP exporter, no distributed sagas (§3, §22, ADRs).
26. **External contributors adding rules safely?** One-directory contribution (rule + fixtures +
    docs + goldens), harness that forbids I/O and enforces fixture coverage, cross-rule FP net,
    CODEOWNERS keeping engine paths reviewed (§13, §26, T26).
27. **Avoiding execution of malicious repo code?** Parse-only pipeline, no import of scanned
    code, no eval of scanned config, repo config privilege-restricted (TB7), resource caps,
    malicious-repo fixtures in CI (T1–T5, §25).
28. **Air-gapped support?** Offline is the default config; offline install procedure + docs
    bundle + `art doctor --assert-offline`; no feature degrades except the optional advisor
    (§9 example 6, §36.2).
29. **Upgrade/migration strategy?** Versioned schemas everywhere, N/N-1 readers, migration
    commands per artifact, migration notes as a required PR field, populated-store migration
    tests (§28).
30. **Production credibility?** §36's readiness definition: external audit, per-threat tests,
    at-most-once demonstrated under crash/concurrency in CI, honest semantics documentation,
    reproducible public case study, supply-chain attestations (§36).
