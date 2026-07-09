# Agent Reliability Toolkit — Planning Repository

**Status: planning phase.** No production code exists yet, by design.

The **Agent Reliability Toolkit (ART)** is a planned open-source (Apache-2.0), local-first
reliability and security toolkit for AI agents, agent loops, workflows, and tool-calling systems.
Its thesis: agent failures happen predominantly at the **execution and harness layer** —
non-idempotent tools retried, unbounded loops, duplicate webhooks, crashes after a side effect,
uncertain execution state — not only at the model layer. ART makes agent behavior detectable,
testable, bounded, auditable, recoverable, and safe to retry, with everything running locally:
no cloud account, no telemetry, no API key, `network: deny` by default.

## Documents

| Document | Contents |
|---|---|
| [`PLAN.md`](PLAN.md) | The master implementation plan: product definition, architecture, trust boundaries, privacy/egress model, per-component designs (agent-lint, LangGraph plugin, ReplaySafe, agent-chaos, agent-contract, trace/audit, GitHub Action, VS Code, MCP, n8n, model advisor), threat model, testing and documentation strategy, ADR list, milestone plan, release checkpoints, risks, and explicit answers to the specification's 30 required questions. |
| [`PLAN-PRS.md`](PLAN-PRS.md) | The complete ordered PR plan: **95 PRs** (PR-001 → PR-095) across milestones A–N, each with scope, non-goals, APIs, security and privacy notes, tests, docs, acceptance criteria, rollback, dependencies, and definition of done. Release boundaries v0.1.0 → v1.0.0 are flagged inline. |
| [`docs/planning-prompt.md`](docs/planning-prompt.md) | The source specification this plan answers. |

## Where implementation starts

PR-001 (repository bootstrap) is the first PR to merge; PR-009 is the first user-visible payoff —
`agent-lint scan` producing a real finding (AR001: agent loop has no maximum step count) fully
offline. The first genuinely useful release is **v0.2.0** (PR-023): a standalone static analyzer
for agent code with 12+ deterministic rules, SARIF output, baselines, and suppressions.
