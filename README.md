# Agent Reliability Toolkit

The **Agent Reliability Toolkit (ART)** is a planned open-source (Apache-2.0), local-first
reliability and security toolkit for AI agents, agent loops, workflows, and tool-calling systems.
Its thesis: agent failures happen predominantly at the **execution and harness layer** —
non-idempotent tools retried, unbounded loops, duplicate webhooks, crashes after a side effect,
uncertain execution state — not only at the model layer. ART makes agent behavior detectable,
testable, bounded, auditable, recoverable, and safe to retry, with everything running locally:
no cloud account, no telemetry, no API key, `network: deny` by default.

## Status

**Planning phase.** No production code exists yet, by design.

## Planning documents

The plan has **two layers**: the complete architecture is fully designed (Layer 1), but only the
first execution wave is committed work (Layer 2) — later components open through evidence-based
validation gates. Principle: **build a serious core, release a narrow surface.**

| Document | Purpose | Authoritative for |
|---|---|---|
| [`PLAN.md`](PLAN.md) | **Master Architecture Roadmap (Layer 1)** — the complete system vision through v1.0: all components (agent-core, agent-lint, ReplaySafe, agent-chaos, agent-contract, LangGraph/MCP/n8n/GitHub Actions/VS Code integrations, trace/audit, optional model advisor), trust boundaries, privacy/egress model, threat model, testing strategy, ADRs, validation gates (§37), open-source strategy (§38) | Architecture, security/privacy invariants, product scope, v1.0 direction |
| [`PLAN-PRS.md`](PLAN-PRS.md) | **Architectural PR Catalog** — 95 PRs (PR-001…095) proving the full system decomposes to reviewable granularity; later milestones carry validation-gate banners | Reference decomposition of later work (subject to gate-driven resequencing) |
| [`EXECUTION.md`](EXECUTION.md) | **Open-Source Execution Roadmap (Layer 2)** — the committed first wave: 14 detailed E-PRs (E01–E14), releases v0.1.0 → v0.5.x, validation gates, gate-override rule, deferred-architecture ledger, contribution surfaces | The active implementation sequence |
| [`docs/planning-prompt.md`](docs/planning-prompt.md), [`docs/execution-revision-prompt.md`](docs/execution-revision-prompt.md) | Source specifications this plan answers | — |

If `EXECUTION.md` and `PLAN-PRS.md` differ in sequencing, `EXECUTION.md` wins. If execution
pressure conflicts with a security or privacy invariant in `PLAN.md`, the invariant wins.

## Where implementation starts

- **E01** starts the repository foundation (license, minimal governance, one CI workflow, a
  single `agent-lint` distribution with the permanent `agent_reliability.{core,lint}` namespace).
- **E04** ships the first product value: `agent-lint scan` finds a real unbounded agent loop
  (AR001), offline.
- **v0.1.0** is the first installable proof (CLI + safe parsing + AR001).
- **v0.2.0** is the first useful standalone linter (AR001/AR003/AR014 + JSON/SARIF + explain +
  suppressions); **v0.3.0** adds LangGraph-aware rules.
- **v0.4.0** is the planned **public launch**: hardened against malicious repositories, GitHub
  Action, docs site, and open contribution paths.
- Later products — ReplaySafe, agent-chaos, agent-contract, MCP, n8n, VS Code, the optional
  model advisor — are fully designed in `PLAN.md` and open through the validation gates in
  `PLAN.md` §37 / `EXECUTION.md`, based on real adoption evidence collected without telemetry.
