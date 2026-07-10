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
5. `CONTRIBUTING.md` — contributor workflow and review