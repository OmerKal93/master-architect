# Execution Prompt — Revise the Agent Reliability Toolkit Plan

## Mission

Revise the existing Agent Reliability Toolkit planning documents on branch:

```text
claude/read-and-plan-2an34e
```

The repository already contains:

- `PLAN.md`
- `PLAN-PRS.md`
- `README.md`

The full architecture must remain ambitious and intact.

The goal is **not** to shrink the system into a portfolio toy.

The goal is to restructure the plan around this principle:

> Build a serious core, release a narrow surface.

The revised plan must separate:

1. **Master Architecture Roadmap** — the complete system vision through v1.0.
2. **Open-Source Execution Roadmap** — the first committed implementation wave, optimized for early user value, evidence, community feedback, and release quality.

Do not write production code.

Do not scaffold packages.

This task is planning-document work only.

---

# 1. Deliverables

Create or revise the following files at the repository root.

## 1.1 New file: `EXECUTION.md`

This is the authoritative implementation sequence for the first public execution wave.

It must contain:

- The execution principles.
- The first 14 detailed execution PRs.
- Release checkpoints.
- Validation gates for later components.
- A reassessment procedure.
- Explicitly deferred architecture.
- Evidence and adoption collection strategy.
- Contribution surfaces.
- Evolution seams into the full architecture.

## 1.2 Revised file: `PLAN.md`

`PLAN.md` becomes **Layer 1: the Master Architecture Roadmap**.

Preserve:

- The complete system vision.
- All components.
- All architecture.
- All security and privacy decisions.
- Threat model.
- ADRs.
- Testing strategy.
- v1.0 target.
- Package boundaries.
- Runtime semantics.

Reframe:

- The 95 PRs are an **architectural implementation catalog**, not an immutable execution sequence.
- `EXECUTION.md` has precedence for committed implementation order.
- Later milestones proceed through validation gates.

Add:

- A “Two planning layers” section near the top.
- A full “Validation gates” section.
- A full “Open-source strategy” section.

## 1.3 Revised file: `PLAN-PRS.md`

Keep all 95 PRs.

Do not delete or renumber them.

Reframe the document as:

> Architectural PR Catalog

It must prove that the full system has been thought through, but it must not claim that all 95 PRs are already committed in this order.

Add:

- A rewritten header.
- A mapping from `EXECUTION.md` E-PRs to the architectural PR catalog.
- Validation-gate banners for Milestones F–N.
- A statement that `EXECUTION.md` controls the active sequence.
- A statement that later catalog PRs may be reordered, merged, split, or deferred after validation.

## 1.4 Revised file: `README.md`

Explain:

- The project.
- The two planning layers.
- Which document is authoritative for what.
- Where implementation starts.
- The first real finding release.
- The planned public launch release.
- Current status: planning phase.

---

# 2. Non-Negotiable Direction

Preserve the complete ART vision:

- `agent-core`
- `agent-lint`
- ReplaySafe
- `agent-chaos`
- `agent-contract`
- LangGraph support
- MCP support
- n8n support
- GitHub Actions
- VS Code
- local trace and audit capabilities
- optional model advisor
- local-first privacy
- deterministic-first security decisions
- offline operation
- plugin extensibility
- stable schemas
- malicious-repository hardening
- Apache-2.0 licensing

Do not remove difficult components merely to simplify execution.

Do not reduce the long-term architecture.

Instead:

- Commit deeply only to the first wave.
- Keep later components architecturally designed.
- Open later components only when evidence supports them.
- Ensure the first wave creates reusable seams, not throwaway code.

---

# 3. Planning Precedence

Document the following precedence clearly:

1. `EXECUTION.md` controls the active implementation sequence.
2. `PLAN.md` controls architectural boundaries, security principles, product scope, and v1 direction.
3. `PLAN-PRS.md` is the detailed architectural catalog for later work.
4. If `EXECUTION.md` and `PLAN-PRS.md` differ in sequencing, `EXECUTION.md` wins.
5. If execution pressure conflicts with a security or privacy invariant in `PLAN.md`, the security/privacy invariant wins.
6. Any exception to a validation gate or major architecture boundary requires a documented ADR.

---

# 4. Required First Execution Wave

Create exactly 14 detailed execution PRs:

```text
E01 ... E14
```

Each E-PR must be a complete, reviewable vertical slice.

Each E-PR must include all of these fields:

1. E-PR ID
2. Title
3. Product area
4. User-visible value
5. Exact scope
6. Explicit non-goals
7. Files/packages affected
8. Public APIs introduced or changed
9. Data models introduced or changed
10. Dependencies added
11. Security considerations
12. Privacy and egress considerations
13. Tests required
14. Documentation required
15. Acceptance criteria
16. Release impact
17. Migration impact
18. Rollback plan
19. Dependencies on earlier E-PRs
20. Later work enabled
21. Complexity: small / medium / large
22. External-contributor suitability
23. Publishable artifact
24. Demo scenario
25. Definition of done
26. Contribution surface
27. Evolution seam

The **contribution surface** field must explain what a community member can contribute after this PR.

The **evolution seam** field must explain how the code grows into the full architecture without rework.

---

# 5. Corrected E-PR Sequence

Use this sequence.

## E01 — Minimal OSS bootstrap

Scope:

- Apache-2.0 license.
- Short README.
- Minimal SECURITY.md.
- Minimal CONTRIBUTING.md.
- Basic `.gitignore` and editor config.
- One CI workflow.
- One Python distribution: `agent-lint`.
- Internal namespace:
  - `agent_reliability.core`
  - `agent_reliability.lint`
- Minimal lint and test matrix.

Do not add:

- Full governance.
- Towncrier.
- Release automation.
- Plugin loading.
- Multi-package workspace.
- Extensive docs framework.

The namespace must make future package splitting mechanical.

---

## E02 — Final-shaped minimal contracts and finding model

Create a minimal subset using the final intended field names and contract shapes.

Include:

- `SourceSpan`
- `Finding`
- `Severity`
- `Confidence`
- stable finding ID
- `fp_v1` fingerprint contract
- minimal `Rule`
- minimal `RuleContext`
- minimal `Frontend` contract
- micro-IR:
  - agent loop
  - retry policy
  - tool call
  - timeout evidence

Do not implement the complete generic IR.

The micro-IR must grow only when a real rule requires a new concept.

Document the evolution path into the full IR from `PLAN.md`.

---

## E03 — Safe local Python frontend

Include:

- parse-only analysis using Python stdlib AST.
- no import or execution of scanned code.
- file-size limits.
- AST node-count limits.
- time budget.
- repository-root containment.
- symlinks not followed by default.
- safe path normalization.
- partial-scan diagnostics.

This PR must not add any rules.

It must prove the scanner can safely turn Python files into the micro-IR.

---

## E04 — Working CLI + AR001

This is the first user-visible product slice.

Include:

- `agent-lint scan`
- text reporter
- stable exit-code contract
- AR001: unbounded agent loop
- rule-module structure
- rule fixture harness
- one true-positive fixture
- one safe fixture
- one edge-case fixture
- quickstart
- README demo

Release:

```text
v0.1.0
```

A clean installation must produce one real finding offline.

---

## E05 — AR003 + AR014

Add:

- AR003: tool or external call without timeout.
- AR014: retry policy without an upper bound.

Keep:

- pure AST.
- high-confidence patterns.
- no side-effect classification.
- low false-positive posture.

Each rule must include:

- true positive.
- safe control.
- edge case.
- documentation.
- exact expected output.

---

## E06 — JSON + SARIF + stable schemas

Add:

- JSON reporter.
- SARIF 2.1.0 reporter.
- stable fingerprints.
- published schemas.
- schema validation in CI.
- hostile-string sanitization.
- line-drift stability tests.

No GitHub Action yet.

---

## E07 — Explain, rule docs, and minimal suppressions

Add:

- `agent-lint explain AR###`
- generated rule catalog.
- `agent-lint rules list`
- minimal inline suppression:

```python
# art: ignore[AR003] reason="..."
```

Requirements:

- reason required.
- no suppression expiry yet.
- offline behavior.
- one-source rule metadata/docs.
- contributor guide for adding a rule.

Release:

```text
v0.2.0
```

This is the first useful standalone linter release.

---

## E08 — LangGraph recognition

Add LangGraph support inside the current distribution, behind the existing `Frontend` contract.

Do not create a separate plugin distribution yet.

Recognize, where statically visible:

- imports.
- `StateGraph`.
- `add_node`.
- `add_edge`.
- `add_conditional_edges`.
- `compile`.
- recursion-limit evidence.
- `MemorySaver`.
- interrupt/approval evidence.
- tool-node bindings.
- terminal paths.

Explicitly document unsupported dynamic patterns.

No framework-specific rules in this PR.

---

## E09 — Minimal side-effect classification + first LangGraph rules

This PR must resolve the dependency issue between framework rules and side-effect classification.

Add a deliberately narrow classifier:

1. explicit ART annotations.
2. a small curated known-tool table.
3. conservative name heuristics at low confidence.

Add only the highest-value framework rules that this classifier can support credibly:

- LG002: non-durable or in-memory checkpointing with risky tools.
- LG003: high-risk action without visible approval/interrupt.
- LG006: router or graph path with no reachable terminal.
- AR001 enrichment: silence when a visible recursion limit exists.

If one of the above cannot meet an acceptable false-positive threshold, replace it with another rule that is fully supported by the available IR and explain why.

Release:

```text
v0.3.0
```

---

## E10 — Malicious-repository and offline hardening

This must land before the public GitHub Action.

Include:

- complete T1/T2/T4/T11/T12/T13 fixture coverage.
- malicious source fixtures.
- path traversal.
- symlink containment.
- terminal escapes.
- SARIF/report injection.
- malicious filenames.
- huge/pathological inputs.
- redaction before reporting.
- no-network socket-guard CI job.
- tests proving scanner commands do not open sockets.

This is the first enforcement half of the future egress design.

Do not build the full Egress Broker object yet.

---

## E11 — GitHub Action

Add:

- composite GitHub Action.
- minimal inputs:
  - `path`
  - `format`
  - `fail-on`
- SARIF upload.
- forced offline/no-network mode.
- SHA-pinned third-party actions.
- minimal permissions.
- self-test workflow.

The Action may claim forced offline behavior only because E10 already proves and enforces it.

---

## E12 — Public launch and contribution surfaces

Add:

- canonical unsafe example.
- canonical safe example.
- minimal docs site.
- public release notes.
- public roadmap.
- seeded good-first-issues.
- “add a rule” guide.
- “contribute a failure fixture” guide.
- bug-report issue template.
- false-positive issue template.
- “did this catch a real bug?” issue template.
- launch-ready README.
- community feedback process.

Release:

```text
v0.4.0
```

This is the first deliberate public launch.

---

## E13 — Adoption features + retry-safety headline

This PR may be split into E13a/E13b in implementation only if review size requires it, but keep it as one execution-wave commitment in `EXECUTION.md`.

Include:

### Adoption features

- baseline creation.
- classification of new vs existing findings.
- changed-files mode.
- suppression expiry.
- suppression report.

### Retry-safety headline

- expanded side-effect classification.
- AR002: retry wraps a non-idempotent action.
- AR011: retry may occur after uncertain success.
- remediation links.
- “did this bite you?” issue template linked from findings/docs.

Release:

```text
v0.5.0 or v0.5.x
```

Clearly state that the exact patch/minor split may be determined after E12 feedback.

This PR is also the primary demand instrument for ReplaySafe.

---

## E14 — Evidence review and next-wave decision

This is not a code PR.

It is a release/process decision checkpoint.

Create:

- adoption report template.
- validation-gate scorecard.
- issue/fixture summary.
- false-positive summary.
- rule-usage summary.
- contributor summary.
- next-wave ADR.

Possible outcomes:

- ReplaySafe opens.
- Agent Chaos opens.
- Agent Contract opens.
- More lint depth first.
- MCP or n8n integration opens.
- Continue feedback collection.
- Stop or narrow a weak component.

No later milestone becomes committed automatically.

---

# 6. Release Checkpoints

The first wave must use this release ladder:

| Release | Minimum content |
|---|---|
| v0.1.0 | CLI + safe parsing + AR001 |
| v0.2.0 | AR003 + AR014 + JSON/SARIF + explain/docs/suppressions |
| v0.3.0 | LangGraph recognition + first framework-aware rules |
| v0.4.0 | hardened scanner + GitHub Action + public launch |
| v0.5.x | adoption features + retry-safety headline rules |

After E14, releases become gate-driven.

---

# 7. Validation Gates

Add measurable gates.

These are decision aids, not scientific laws.

## 7.1 ReplaySafe gate

Open ReplaySafe implementation when one of the following is true:

### Standard gate

- At least 5 distinct retry/resume/duplicate-side-effect failure reports.
- Reports come from at least 3 independent users, teams, or organizations.
- At least 2 failures are reproducible as fixtures or minimal examples.

### Severe-event exception

A single severe, reproducible incident may open the milestone when it involves:

- payment duplication.
- destructive duplicate action.
- high-cost runaway retry.
- compliance-impacting uncertain execution.

The exception requires an ADR.

---

## 7.2 Agent Chaos gate

Open Agent Chaos when:

- At least 3 independent users or teams request reproducible fault testing.
- At least 2 requested scenarios can be represented as deterministic fixtures.
- ReplaySafe or agent-lint has already exposed concrete failure classes worth testing.

---

## 7.3 Agent Contract gate

Open Agent Contract when:

- At least 3 distinct schema-drift, parameter-drift, or tool-contract regression cases are reported.
- At least 2 come with before/after schemas, code, or fixtures.
- Existing JSON Schema validation alone is shown insufficient.

---

## 7.4 MCP gate

Open MCP work when:

- A user or maintainer provides a concrete MCP integration target.
- A reproducible fixture, manifest, or test server exists.
- The requested need is clearly differentiated from existing MCP security scanners.

---

## 7.5 n8n gate

Open n8n work when one of the following is true:

- At least 3 real exported workflows are available as sanitized fixtures.
- A contributor commits to maintaining n8n fixtures.
- A repeated reliability failure appears across multiple workflows.

---

## 7.6 Plugin-loading gate

Add entry-point plugin loading when:

- A third-party adapter is proposed.
- The adapter needs to ship outside the main distribution.
- The Frontend/Rule contracts have survived at least 2 public releases.

Until then, first-party integrations stay internal modules behind the same contracts.

---

## 7.7 PostgreSQL/Redis gate

Open production backends when:

- At least 2 ReplaySafe users require multi-process or multi-host coordination.
- SQLite limitations are reproduced and documented.
- The Ledger/Lock contracts are stable.

---

## 7.8 VS Code gate

Open the VS Code extension when:

- CLI output and rule IDs have remained stable for at least 2 public releases.
- There are at least 10 explicit requests, positive reactions, or user confirmations that editor integration would materially help.
- The extension can reuse the existing engine without duplicated analysis logic.

---

## 7.9 Model advisor gate

The model advisor remains optional forever.

It may proceed only when:

- users explicitly request model-assisted explanation or patch generation.
- deterministic explain/remediation is already mature.
- the Egress Broker exists.
- payload preview, redaction, allowlisting, and approval semantics are implemented.

It can never become a security or authorization authority.

---

## 7.10 Governance-expansion gate

Add heavier governance only when contributor volume justifies it.

Possible triggers:

- 5+ non-maintainer contributors.
- recurring review conflicts.
- multiple maintainers.
- multiple release owners.
- security-sensitive external plugins.

Do not front-load governance bureaucracy.

---

# 8. Gate Override Rule

Numeric gates must not become permanent vetoes.

Maintainers may open a gated milestone without meeting the numeric threshold when one of these applies:

- severe reproducible failure.
- strategic integration.
- funded or committed contributor.
- ecosystem change.
- security incident.
- strong maintainer evidence.

Every override requires:

- a public ADR.
- evidence.
- explicit trade-offs.
- a review date.
- success/failure criteria.

---

# 9. Deferred Architecture and Cheap Placeholders

Document these explicit deferrals.

## 9.1 Full generic IR

Deferred.

Placeholder:

- micro-IR with final-shaped contracts.
- add one concept only when a real rule needs it.
- no speculative type inventory in implementation.

## 9.2 Plugin entry-point loading

Deferred.

Placeholder:

- final `Frontend`, `Rule`, and metadata contracts.
- first-party adapters remain internal modules.
- loading arrives at the third-party-adapter gate.

## 9.3 Full Egress Broker

Deferred.

Placeholder:

- no-network socket guard.
- direct-network imports forbidden in scanner paths.
- full broker arrives before remote model support.

Do not force runtime datastore connections or user-owned test targets through a single god-object broker.

The future network capability model must distinguish:

- model egress.
- test-target access.
- runtime datastore access.
- user-tool access.
- telemetry.

## 9.4 Full release machinery

Deferred.

Placeholder:

- handwritten CHANGELOG.
- tagged releases.
- simple trusted publishing when first needed.

Add towncrier/automated release tooling when release cadence becomes painful.

## 9.5 Monorepo package split

Deferred.

Placeholder:

```text
agent-lint distribution
└── agent_reliability/
    ├── core/
    └── lint/
```

Split packages when one of these is true:

- ReplaySafe needs a runtime-neutral core.
- a third-party plugin needs a stable dependency.
- products require independent release cycles.

Do not split merely because a version number was reached.

---

# 10. ReplaySafe Claim Precision

Revise any overly strong promise.

Do not state:

> Same key guarantees the external effect ran at most once.

Use a precise claim such as:

> ReplaySafe deduplicates confirmed executions and blocks ambiguous re-execution by default.

Document that true protection depends on at least one of:

- service-side idempotency.
- authoritative verification.
- transactional outbox.
- compensating action.
- human resolution.

Uncertain execution must remain a first-class state.

No silent retry after ambiguous success.

---

# 11. Chaos Isolation Precision

Do not claim that a Python socket guard makes chaos “physically unable” to reach production.

Use an honest staged model:

## Before strong sandboxing

- application-level socket guard.
- mock transports.
- subprocess restrictions.
- explicit simulation-only targets.
- best-effort containment.
- visible limitations.

## Later strong isolation

- container boundary.
- network namespace.
- OS-level sandbox.
- explicit target allowlist.

The plan must distinguish:

- deterministic simulation.
- application-level fault injection.
- OS-level isolation.

---

# 12. Open-Source Strategy

Add a full section to `PLAN.md` and a shorter practical version to `EXECUTION.md`.

Cover all of the following.

## 12.1 Contributor onboarding

- install.
- run tests.
- run one fixture.
- add one rule.
- contributor path under 30 minutes.

## 12.2 Adding a rule

- rule module.
- metadata.
- true-positive fixture.
- safe control.
- edge case.
- documentation.
- expected finding output.

## 12.3 Contributing a failure fixture

Allow users to contribute:

- sanitized code.
- simplified reproduction.
- workflow fragment.
- trace excerpt.
- expected safe/unsafe behavior.
- tool/framework versions.

Fixtures become part of the permanent regression suite.

## 12.4 Good-first-issue design

Good-first issues should be bounded:

- add a safe fixture.
- add an SDK call pattern.
- improve a rule explanation.
- add a malformed-input case.
- document a false positive.
- add a known-tool entry with evidence.

Do not label architecture or security-boundary changes as good-first issues.

## 12.5 Maintainer review boundaries

Use stronger review requirements for:

- engine internals.
- parser safety.
- fingerprint algorithm.
- redaction.
- network policy.
- security boundaries.
- ReplaySafe state semantics.
- plugin loading.

Rules and fixtures should be easier for external contributors.

## 12.6 Plugin compatibility

- stable contract version.
- explicit compatibility metadata.
- public deprecation policy.
- no silent plugin activation.
- third-party plugins treated as trusted dependencies.

## 12.7 Public RFC process

Major changes require:

- GitHub Discussion.
- RFC document.
- ADR after decision.
- alternatives.
- security/privacy impact.
- migration plan.

## 12.8 Release communication

Each release should include:

- what problem was solved.
- demo.
- install command.
- breaking changes.
- known limitations.
- contribution requests.
- validation questions.

## 12.9 Feedback loops

Use:

- issue templates.
- GitHub Discussions.
- false-positive reports.
- “did this catch a real bug?” reports.
- fixture contributions.
- public roadmap voting.
- release feedback threads.

## 12.10 Bug report → regression fixture

Define the pipeline:

1. user report.
2. reproduce.
3. sanitize.
4. convert into fixture.
5. add failing regression test.
6. fix.
7. keep fixture permanently.
8. credit contributor when allowed.

## 12.11 Adoption without telemetry

Use only public or user-supplied signals:

- GitHub stars/forks as weak awareness signals.
- issues and discussions.
- contributors.
- public dependency graph.
- public GitHub Action usage.
- PyPI downloads as a trend only.
- fixture submissions.
- explicit confirmations of caught bugs.
- repeat users in discussions.

State clearly:

- no phone-home telemetry.
- no repository fingerprinting.
- no hidden analytics.
- PyPI downloads are not proof of active use.

---

# 13. PLAN.md Required Edits

Perform these exact reframes.

## 13.1 Intro

Add:

```text
Two planning layers
```

Explain:

- `PLAN.md` = architecture.
- `PLAN-PRS.md` = architectural PR catalog.
- `EXECUTION.md` = active execution.
- precedence rules.

## 13.2 Executive summary

Replace any claim that the 95 PRs are the committed path.

State:

- the complete architecture remains planned through v1.
- only the first wave is execution-committed.
- later work is gate-driven.
- the first finding ships at v0.1.
- the public launch is v0.4.

## 13.3 Milestones and releases

Reframe Milestones A–N as:

- architecture roadmap.
- not automatically committed.
- each later milestone has a gate status.

Add a “commitment status” column:

- committed.
- gated.
- optional.
- validation-only.

## 13.4 First implementation PR

Point to:

- E01 for repository start.
- E04 for first product value.

## 13.5 Risks

Update plan-stall risk.

Add:

```text
Risk: validation gates never open
```

Mitigation:

- findings and issue templates actively measure demand.
- gate overrides through ADR.
- periodic reassessment.
- maintainers may choose more lint depth instead of waiting.

## 13.6 New validation-gates section

Add the full measurable gates.

## 13.7 New open-source strategy section

Add all 11 topics from Section 12 of this prompt.

---

# 14. PLAN-PRS.md Required Edits

Do not delete or renumber existing PRs.

## 14.1 Header rewrite

State:

- 95 PRs are the full architectural catalog.
- the catalog proves coverage and implementation thought.
- it is not the current committed merge order.
- `EXECUTION.md` controls the active first wave.

## 14.2 Mapping table

Map E-PRs to catalog concepts.

Example:

| E-PR | Architectural catalog coverage |
|---|---|
| E01 | selected parts of PR-001, PR-002 |
| E02 | minimal subset of PR-005, PR-007 |
| E03 | selected parts of PR-008 |
| E04 | PR-009 |
| E05 | PR-012 |
| E06 | PR-013 |
| E07 | selected parts of PR-015, PR-021 |
| E08 | selected parts of PR-025–027 |
| E09 | selected parts of PR-016, PR-027–029 |
| E10 | selected parts of PR-006, PR-010, PR-022 |
| E11 | selected parts of PR-033–035 |
| E12 | selected parts of PR-004, PR-023, community docs |
| E13 | selected parts of PR-014–017, PR-032 |
| E14 | no code equivalent; gate review |

Complete and correct the mapping after inspecting the actual document.

## 14.3 Milestone banners

For Milestones F–N, add a banner such as:

```text
Status: Planned architecture — implementation requires the validation gate defined in PLAN.md and EXECUTION.md.
```

Also mark:

- plugin loading.
- PostgreSQL/Redis.
- VS Code.
- MCP.
- n8n.
- model advisor.

## 14.4 No stale sequencing claims

Remove or rewrite statements such as:

- “ordering is the merge order”
- “complete ordered execution sequence”
- “all PRs will be executed in this order”
- “immutable sequence”

Use:

- architectural dependency order.
- reference implementation decomposition.
- subject to gate-driven resequencing.

---

# 15. README.md Required Content

Keep it minimal.

Include:

# Agent Reliability Toolkit

One-paragraph thesis.

## Status

Planning phase.

## Planning documents

| Document | Purpose |
|---|---|
| `PLAN.md` | Master Architecture Roadmap |
| `PLAN-PRS.md` | Architectural PR Catalog |
| `EXECUTION.md` | Active Open-Source Execution Roadmap |
| planning prompt/source | source specification if retained |

## Where implementation starts

State:

- E01 starts repository foundation.
- E04 ships the first finding.
- v0.1.0 is the first installable proof.
- v0.4.0 is the planned public launch.
- later products open through validation gates.

---

# 16. Verification Requirements

Before committing, run scripted checks.

## 16.1 EXECUTION.md

Verify:

- exactly 14 E-PR sections.
- every E-PR has all 27 fields.
- release checkpoints present.
- all validation gates present.
- gate override rule present.
- contribution surface present in every E-PR.
- evolution seam present in every E-PR.
- no later product is described as automatically committed.

## 16.2 PLAN.md

Verify:

- two-layer intro exists.
- `EXECUTION.md` precedence exists.
- validation-gates section exists.
- open-source-strategy section exists.
- all 11 open-source topics are present.
- full architecture remains intact.
- threat model and security content are not removed.
- ReplaySafe language is precise.
- chaos isolation language is precise.
- release table has commitment status.

## 16.3 PLAN-PRS.md

Verify:

- all original PR IDs still exist.
- no PR was renumbered.
- mapping table exists.
- Milestones F–N have gate banners.
- stale immutable-order language is gone.
- `EXECUTION.md` is referenced as active sequence.

## 16.4 README.md

Verify:

- all three planning documents are referenced.
- status is planning phase.
- implementation start is explained.
- v0.1 and v0.4 meanings are correct.

## 16.5 Cross-document consistency

Verify:

- E-PR names and numbers match everywhere.
- release numbers match everywhere.
- validation thresholds match everywhere.
- every deferred component has a named gate.
- no document claims the 95 PRs are currently committed.
- no document says the system was made smaller.
- no document implies an LLM can authorize or override security.
- no document claims perfect exactly-once execution.
- no document claims Python socket guards provide complete OS-level isolation.

---

# 17. Git Instructions

Work on:

```text
claude/read-and-plan-2an34e
```

Steps:

1. Confirm the branch.
2. Read the existing documents fully before editing.
3. Create `EXECUTION.md`.
4. Revise `PLAN.md`.
5. Reframe `PLAN-PRS.md`.
6. Update `README.md`.
7. Run scripted verification.
8. Review `git diff`.
9. Commit with a descriptive Conventional Commit message, for example:

```text
docs: add evidence-driven open source execution roadmap
```

10. Push:

```bash
git push -u origin claude/read-and-plan-2an34e
```

Retry transient network failures with bounded backoff.

Do not create a pull request unless explicitly requested.

---

# 18. Final Response

Return:

- concise summary of changes.
- files created/edited.
- number of committed E-PRs.
- release checkpoints.
- validation gates added.
- verification results.
- commit hash.
- push status.
- any unresolved assumptions or contradictions.

Do not claim completion unless the commit and push succeed.

If push fails, state clearly that the documents were committed locally but not pushed, and include the exact error.
