# Fable Planning Prompt — Agent Reliability Toolkit

## Role

Act as a principal software architect, staff security engineer, open-source maintainer, and agentic-systems reliability specialist.

Your task is to produce a **complete implementation plan** for an open-source, local-first reliability and security toolkit for AI agents, agent loops, workflows, pipelines, and tool-calling systems.

Do **not** write production code yet.

The output must be detailed enough that another coding agent can execute the work PR by PR without having to redesign the system during implementation.

---

# 1. Product Goal

Design a complete open-source system tentatively called:

**Agent Reliability Toolkit**

The toolkit should help developers detect, test, prevent, explain, and recover from failures in agentic systems.

It must integrate with existing frameworks instead of replacing them.

Initial ecosystem focus:

1. Python
2. LangGraph
3. CLI usage
4. GitHub Actions
5. VS Code
6. MCP tools
7. pytest
8. Later: TypeScript and n8n

The system should eventually contain these product areas:

- Static reliability and security analysis
- Runtime protection for tool calls and side effects
- Retry and idempotency safety
- Workflow and agent-loop guardrails
- Fault injection and chaos testing
- Tool-contract testing
- Local execution tracing and audit records
- Optional model-assisted explanations and fixes
- Plugin support for frameworks and workflow platforms
- CI and IDE integrations

The project must be useful to developers as a collection of standalone tools, while also forming one coherent reliability harness.

---

# 2. Core Product Thesis

The system is based on this thesis:

> Agent failures often happen at the execution and harness layer, not only at the model layer.

Typical failures include:

- Non-idempotent tools running twice after retry or resume
- Infinite or silent retry loops
- Unbounded agent loops
- Runaway token or API costs
- Tool schema drift
- Missing timeouts
- Duplicate webhooks
- Process crashes after a side effect completed
- Uncertain execution state
- Context growth and memory exhaustion
- Prompt injection through tool output or external content
- Overly broad permissions
- Sensitive data flowing back into a model
- Missing approval gates for high-risk actions
- Missing audit identifiers
- Concurrent agents modifying the same resource
- Incorrect rollback assumptions
- Workflows that appear valid but fail under realistic conditions

The toolkit should focus on making agent behavior:

- Detectable
- Testable
- Bounded
- Auditable
- Recoverable
- Safe to retry
- Safe to run locally
- Easier to understand

---

# 3. Non-Negotiable Architecture Principles

These constraints are mandatory unless you identify a serious technical contradiction and document it clearly.

## 3.1 Local-first

All core analysis must run locally.

The toolkit must not require:

- A cloud account
- A hosted control plane
- External telemetry
- An API key
- A remote database
- A model provider

The default network policy must be:

```yaml
network:
  mode: deny
```

## 3.2 Deterministic-first

Security and reliability decisions must be deterministic whenever possible.

Use:

- AST analysis
- Graph analysis
- Schema validation
- Policy rules
- Static type information
- Runtime state
- Recorded execution receipts
- Explicit invariants

Do not make an LLM the authority for:

- Whether code is safe
- Whether a tool call should be allowed
- Whether a finding can be ignored
- Whether a retry is safe
- Whether a destructive action is permitted
- Whether sensitive data may leave the machine

## 3.3 Model-optional

An optional model advisor may later:

- Explain findings
- Suggest patches
- Generate tests
- Generate chaos scenarios
- Classify an unknown custom tool
- Summarize a trace

It may not:

- Override deterministic findings
- Access secrets
- Send the repository automatically
- perform external actions without explicit approval
- make final authorization decisions

Support three privacy modes:

```yaml
privacy:
  mode: offline
```

```yaml
privacy:
  mode: local-model
```

```yaml
privacy:
  mode: controlled-egress
```

In controlled-egress mode, the user must see and approve exactly what leaves the machine.

## 3.4 No telemetry by default

- No hidden analytics
- No automatic crash reporting
- No repository fingerprinting
- No outbound calls during installation or runtime
- Any future telemetry must be explicit opt-in

## 3.5 Secure defaults

- Deny network by default
- Redact secrets by default
- Do not collect source code unnecessarily
- Prefer local SQLite for first-run persistence
- Require explicit configuration for external services
- Treat tool outputs as untrusted input
- Treat workflow files as untrusted input
- Do not execute scanned user code during static analysis

## 3.6 Open source

Use:

**Apache License 2.0**

The repository must be ready for external contributors.

Include:

- LICENSE
- NOTICE if needed
- CONTRIBUTING.md
- SECURITY.md
- CODE_OF_CONDUCT.md
- Governance notes
- Issue templates
- Pull request template
- Release process
- Versioning strategy
- Supported Python versions
- Dependency policy
- Security disclosure process

## 3.7 Incremental delivery

The complete system must be planned up front, but implemented through small PRs.

Every PR must:

- Complete a coherent unit of value
- Leave the repository passing all tests
- Leave the repository releasable
- Avoid half-wired architecture
- Avoid dead abstractions
- Avoid “temporary” code with no removal plan
- Include documentation
- Include tests
- Include acceptance criteria
- Include security impact notes
- Include migration notes when relevant

A PR may be small, but it must not leave an unfinished feature on the main branch.

---

# 4. Target Product Components

Design the full architecture around the following components.

You may rename packages if you can justify a better naming system.

## 4.1 `agent-core`

Shared domain and infrastructure layer.

Expected responsibilities:

- Intermediate representation for:
  - Agent
  - Workflow
  - Node
  - Edge
  - Tool
  - Tool call
  - Side effect
  - Retry policy
  - Timeout policy
  - Approval gate
  - Risk classification
  - Execution receipt
  - Finding
  - Rule
  - Suppression
  - Invariant
- Rule engine
- Plugin contracts
- Finding lifecycle
- Severity and confidence model
- Text, JSON, and SARIF output models
- Redaction utilities
- Secret detection hooks
- Configuration loading
- Stable internal IDs
- File and source-location mapping
- Error taxonomy
- Compatibility/version metadata

Avoid turning `agent-core` into an unbounded utility package.

Define strict package boundaries.

## 4.2 `agent-lint`

Local static analyzer and CLI.

Initial focus:

- Python
- LangGraph applications
- Tool wrappers
- Agent loops
- Retry patterns
- Side-effect safety

Example commands:

```bash
agent-lint scan .
agent-lint scan . --format json
agent-lint scan . --format sarif
agent-lint explain AR002
agent-lint rules list
agent-lint baseline create
```

Initial rule candidates:

- AR001: Agent loop has no maximum step count
- AR002: Retry surrounds a non-idempotent action
- AR003: Tool call has no timeout
- AR004: Side effect has no idempotency key
- AR005: High-risk action has no approval gate
- AR006: Side effect occurs before a durable checkpoint
- AR007: Tool output enters context without a size bound
- AR008: MCP or tool permission scope is overly broad
- AR009: Sensitive tool output may be returned to the model
- AR010: External write has no audit identifier
- AR011: Retry may run after uncertain success
- AR012: Concurrent runs may modify the same resource
- AR013: Catch-all exception hides tool failure
- AR014: Retry policy has no upper bound
- AR015: Destructive action has no verification or compensation path

The plan must define:

- How rules are authored
- How rules are tested
- How rules map to framework adapters
- How false positives are suppressed
- How baselines work
- How custom organization rules work
- How rule versioning works
- How auto-fix support may be added safely
- How analysis remains local and does not execute user code

## 4.3 LangGraph Python plugin

The first framework adapter.

It should understand, where statically possible:

- Graph definitions
- Nodes
- Edges
- Conditional routing
- Recursion or step limits
- Tools
- Retry policies
- Checkpoint configuration
- Interrupts
- Human approval points
- Side effects
- State updates
- Resume behavior
- Durable execution assumptions

Specify what can be detected reliably and what cannot.

Do not claim complete semantic understanding where static analysis cannot provide it.

## 4.4 `ReplaySafe`

Runtime protection for external side effects.

Primary goal:

> Make agent actions safe under retry, resume, duplicate delivery, timeout, crash, and concurrency.

Expected capabilities:

- Idempotency keys
- Execution ledger
- Action claims
- Deduplication
- Per-resource locking
- Status model:
  - pending
  - started
  - completed
  - failed
  - uncertain
  - compensated
- Pre-action checkpoint
- Post-action receipt
- Verify-before-retry
- Bounded retry
- Concurrent execution protection
- Compensation hooks
- Approval hooks
- Audit trail
- Local SQLite backend first
- PostgreSQL backend later
- Redis locking adapter later

Example API:

```python
@replaysafe.action(
    key=lambda order_id: f"charge:{order_id}",
    effect="financial",
    retry="verify-before-retry",
)
def charge_customer(order_id: str):
    ...
```

Design the API so it can later wrap:

- LangGraph tools
- MCP tools
- Normal Python functions
- HTTP client actions
- Queue consumers
- n8n community nodes

The plan must carefully define failure semantics, especially:

- Action completed but response was lost
- Process crashed before receipt persisted
- Two workers claim the same action
- Verification endpoint unavailable
- Compensation fails
- Idempotency key collision
- Ledger unavailable
- User requests force retry
- Action result is non-serializable

## 4.5 `agent-chaos`

Fault-injection and resilience testing tool.

Interfaces:

- CLI
- pytest plugin
- Python library

Fault scenarios should eventually include:

- 429 rate limit
- Timeout before an action
- Timeout after an action may have succeeded
- Malformed JSON
- Invalid tool schema
- Partial response
- Duplicate webhook
- Process crash
- Stale checkpoint
- Missing memory store
- Context growth
- Tool result prompt injection
- Two concurrent workers
- Delayed success response
- Database lock
- Ledger outage
- Approval timeout
- Model returns repeated tool call
- Model changes tool arguments between retries

Developers should define invariants such as:

```yaml
invariants:
  - payment_occurs_at_most_once
  - maximum_steps: 12
  - maximum_cost_usd: 0.50
  - uncertain_payment_requires_human: true
  - no_secret_is_returned_to_model: true
```

The plan must define:

- Scenario format
- Invariant engine
- Fault adapters
- Reproducibility
- Seeds
- Test isolation
- Deterministic and model-backed test modes
- Trace and result formats
- Integration with ReplaySafe
- Integration with pytest
- Safe handling of real external systems
- Mandatory simulation/dry-run boundaries

## 4.6 `agent-contract`

Contract testing for tools and MCP.

Expected capabilities:

- Validate tool schemas
- Detect breaking schema changes
- Verify required fields
- Verify enum behavior
- Verify response shape
- Test timeouts
- Test error contracts
- Test side-effect annotations
- Test idempotency expectations
- Test approval requirements
- Test permission scopes
- Fuzz tool inputs
- Generate compatibility reports
- Compare tool versions
- Export CI-friendly results

Example:

```bash
agent-contract init
agent-contract test ./tools
agent-contract diff tools-v1.json tools-v2.json
agent-contract fuzz mcp://localhost:3000
```

Design a human-readable contract format.

## 4.7 Local trace and audit layer

The toolkit should not attempt to replace full observability platforms.

It should provide the minimum local data needed for:

- Explaining findings
- Reproducing failures
- Showing execution timelines
- Tracking ReplaySafe decisions
- Chaos-test evidence
- Auditing policy decisions
- Exporting to OpenTelemetry-compatible formats where practical

Define:

- What is recorded
- What is never recorded
- Retention defaults
- Redaction
- Local storage
- Export
- Trace IDs
- Correlation IDs
- Tool-call IDs
- Action IDs
- Finding IDs
- Privacy boundaries

## 4.8 GitHub Action

The CI integration should:

- Run `agent-lint`
- Produce SARIF
- Support PR annotations
- Support baseline mode
- Fail only on configured severities
- Work without external services
- Pin dependencies safely
- Avoid leaking source code
- Support monorepos
- Support changed-files mode
- Support rule allowlists and denylists

## 4.9 VS Code extension

The VS Code extension must reuse the CLI or language service.

Do not duplicate analysis logic.

Expected capabilities:

- Inline diagnostics
- Rule explanations
- Links to documentation
- Safe quick fixes where deterministic
- Local-only operation
- Workspace privacy notice
- Configuration UI
- Suppression insertion
- Run scan command
- View finding details

Plan this only after the CLI and rule engine are stable.

## 4.10 MCP support

Later support should include:

- MCP server manifest/schema inspection
- Tool contract testing
- Permission-scope analysis
- Side-effect classification
- Tool-output trust boundaries
- Prompt-injection test cases
- Tool wrapping with ReplaySafe
- Local proxy mode if justified
- Explicit egress controls

Do not build a general MCP security scanner if existing tools already solve the same problem better.

Identify the narrow gap this toolkit should own.

## 4.11 n8n support

Later support should include:

- Workflow JSON ingestion
- Static reliability rules
- Retry and error-path analysis
- Side-effect node detection
- Idempotency community node
- ReplaySafe node
- Circuit-breaker node
- Chaos simulation against exported workflows
- Local workflow reports

Do not build a replacement workflow editor.

## 4.12 Optional model advisor

Design this as a separate optional package and security boundary.

Possible providers:

- Local models
- Ollama-compatible endpoints
- Explicitly configured remote providers

Requirements:

- No source code sent by default
- Preview before remote send
- Redaction
- Minimal-context extraction
- Audit record of outbound payload metadata
- Per-request approval option
- Provider allowlist
- Offline mode must remain fully functional

---

# 5. Repository Strategy

Start as a monorepo.

Propose a concrete repository structure.

Expected direction:

```text
agent-reliability-toolkit/
├── packages/
│   ├── agent-core/
│   ├── agent-lint/
│   ├── replaysafe/
│   ├── agent-chaos/
│   ├── agent-contract/
│   └── model-advisor/
├── plugins/
│   ├── langgraph-python/
│   ├── mcp/
│   └── n8n/
├── integrations/
│   ├── github-action/
│   └── vscode/
├── examples/
├── docs/
├── tests/
├── tools/
├── pyproject.toml
├── LICENSE
├── SECURITY.md
└── README.md
```

Challenge this structure if needed.

Specify:

- Python packaging strategy
- Workspace tooling
- Dependency management
- Build system
- Test organization
- Release process
- Independent package versioning versus unified versioning
- API stability policy
- Internal versus public packages
- Generated files policy
- Documentation tooling
- Changelog strategy
- Conventional commits or alternative
- Semantic versioning policy
- Supported OSes
- Supported Python versions
- Optional TypeScript workspace strategy for later plugins

Prefer boring, maintainable technology.

Avoid unnecessary infrastructure.

---

# 6. Threat Model

Produce a serious threat model for the toolkit itself.

At minimum cover:

- Malicious repository content
- Malicious Python syntax or generated code
- Malicious workflow JSON
- Symlink/path traversal
- Config injection
- Secret leakage
- Prompt injection inside source or tool output
- Dependency compromise
- Plugin compromise
- Arbitrary code execution during scanning
- Unsafe deserialization
- SARIF or report injection
- Terminal escape injection
- Malicious filenames
- Ledger tampering
- Idempotency-key collision
- Race conditions
- Lock bypass
- Local privilege boundaries
- Model provider data exfiltration
- CI log leakage
- GitHub Actions supply-chain risk
- VS Code extension trust boundaries
- MCP proxy risks
- n8n credential exposure
- Denial of service from huge repositories or graphs

For each threat define:

- Asset
- Attacker
- Entry point
- Impact
- Mitigation
- Residual risk
- Tests
- Relevant PR or milestone

---

# 7. Privacy and Egress Model

Design a centralized `Egress Broker`.

All future outbound communication must use it.

Requirements:

- Deny by default
- Destination allowlist
- Payload preview
- Redaction
- Purpose declaration
- User approval
- Provider-specific adapters
- Local audit metadata
- Payload-size limits
- Timeout
- Retry policy
- No hidden fallback to remote providers
- Clear offline failure behavior

Define configuration examples for:

- Fully offline
- Local model
- Controlled Anthropic/OpenAI-compatible provider
- CI environment with no network
- Corporate proxy environment
- Air-gapped environment

---

# 8. Rule and Finding Design

Design a stable finding schema.

Each finding should include at least:

- Rule ID
- Rule version
- Title
- Description
- Severity
- Confidence
- Category
- Framework
- File
- Source span
- Evidence
- Why it matters
- Suggested remediation
- Auto-fix availability
- References
- Suppression key
- Fingerprint
- Baseline status
- Data-flow path when applicable

Define:

- Severity scale
- Confidence scale
- Categories
- Stable fingerprints
- Duplicate merging
- Multi-file findings
- Framework-specific evidence
- Rule metadata
- Deprecation
- False-positive reporting
- Suppression policy
- Expiring suppressions
- Organization-specific policies

Do not use arbitrary numerical “risk scores” without a clear decision model.

---

# 9. Testing Strategy

Create a complete testing strategy.

Include:

- Unit tests
- Parser tests
- AST fixture tests
- Golden-file tests
- Rule tests
- False-positive tests
- False-negative regression tests
- Property-based tests
- Fuzzing
- Concurrency tests
- Crash-recovery tests
- Filesystem safety tests
- Security tests
- Plugin compatibility tests
- CLI integration tests
- SARIF validation
- JSON schema validation
- SQLite migration tests
- PostgreSQL adapter tests
- Redis adapter tests
- pytest plugin tests
- GitHub Action tests
- VS Code extension tests
- Offline-mode tests
- Egress denial tests
- Redaction tests
- Malicious-repository fixtures
- Performance tests
- Large-repository tests
- Reproducible chaos tests

Define a fixture library containing both safe and unsafe examples.

Every rule PR must include:

- At least one true-positive fixture
- At least one safe control
- At least one edge case
- Rule documentation
- Stable expected output

---

# 10. Documentation Strategy

Plan documentation for both users and contributors.

Expected documents:

- README
- Quickstart
- Architecture
- Threat model
- Privacy and egress
- Rule catalog
- Writing custom rules
- Plugin author guide
- ReplaySafe semantics
- Chaos testing guide
- Contract format
- CI integration
- VS Code integration
- MCP integration
- n8n integration
- Security policy
- Contributing
- Governance
- Release guide
- Compatibility policy
- FAQ
- Troubleshooting
- Design decisions / ADRs

Every major architecture decision should have an ADR.

---

# 11. PR Planning Requirements

This is the most important section.

Produce a **complete ordered PR plan** for implementing the full system.

The plan may contain many PRs.

Do not optimize for a small number of PRs.

Optimize for:

- Reviewability
- Safety
- Independent value
- Clear acceptance
- Minimal merge risk
- Releasable main branch
- Easy rollback
- External contributor friendliness

## 11.1 Every PR must include

For each PR provide:

1. PR ID
2. PR title
3. Product area
4. User-visible value
5. Exact scope
6. Explicit non-goals
7. Files/packages affected
8. Public APIs introduced or changed
9. Data models introduced or changed
10. Dependencies added
11. Security considerations
12. Privacy/egress considerations
13. Tests required
14. Documentation required
15. Acceptance criteria
16. Release impact
17. Migration impact
18. Rollback plan
19. Dependencies on earlier PRs
20. Follow-up PRs enabled
21. Estimated implementation complexity:
   - small
   - medium
   - large
22. Whether the PR can be assigned to an external contributor
23. Whether the PR produces a publishable artifact
24. Demo scenario
25. Definition of done

## 11.2 Vertical-completeness rule

A PR must not merely add an interface that nothing uses.

Whenever possible, a PR should deliver a vertical slice such as:

- Parser + rule + CLI output + tests + docs
- Runtime decorator + SQLite ledger + tests + example
- Chaos scenario + invariant + CLI + report + docs
- GitHub Action + sample workflow + SARIF upload + docs

Infrastructure-only PRs are allowed only when:

- They are genuinely required
- Their scope is narrow
- They are independently validated
- They do not create speculative abstractions
- The plan explains exactly which next PR consumes them

## 11.3 Release checkpoints

Mark specific PRs as release boundaries.

At minimum plan:

- `v0.1.0`: Walking skeleton
- `v0.2.0`: Useful standalone `agent-lint`
- `v0.3.0`: LangGraph-aware rules
- `v0.4.0`: GitHub Action
- `v0.5.0`: ReplaySafe SQLite runtime
- `v0.6.0`: Agent Chaos MVP
- `v0.7.0`: Tool contracts MVP
- `v0.8.0`: VS Code integration
- `v0.9.0`: MCP support
- `v1.0.0`: Stable local-first toolkit

You may recommend a different release sequence, but justify it.

## 11.4 Expected planning depth

The PR plan must cover the complete path from empty repository to stable v1.0.

Do not stop at the first MVP.

Do not merge all later work into vague “future” epics.

Break later work down enough that implementation can continue without redesign.

---

# 12. Required Milestones

At minimum, organize the PR plan into these milestones.

## Milestone A — Repository and governance foundation

Complete open-source repository foundation.

## Milestone B — Core domain and CLI walking skeleton

A real CLI that scans a fixture and returns one real finding.

## Milestone C — Static analyzer MVP

A useful Python analyzer with multiple deterministic rules.

## Milestone D — LangGraph plugin

Framework-aware findings.

## Milestone E — CI integration

GitHub Action and SARIF.

## Milestone F — ReplaySafe MVP

Runtime idempotency and side-effect safety with SQLite.

## Milestone G — ReplaySafe production adapters

PostgreSQL, locking, concurrency, migrations, verification semantics.

## Milestone H — Agent Chaos MVP

Fault injection and invariants.

## Milestone I — Agent Contract MVP

Tool and MCP contract tests.

## Milestone J — VS Code integration

Local developer experience.

## Milestone K — MCP reliability support

Narrow, differentiated MCP functionality.

## Milestone L — n8n support

Workflow analysis and runtime nodes.

## Milestone M — Optional model advisor

Strictly isolated, opt-in, egress-controlled.

## Milestone N — v1 hardening

Security audit, performance, API stability, compatibility, migration, docs, release.

---

# 13. Architecture Decision Records

Identify all ADRs that should exist before or during implementation.

At minimum consider:

- Monorepo versus multi-repo
- Apache-2.0 license
- Python-first
- AST strategy
- Intermediate representation
- Plugin system
- Local-first policy
- No telemetry default
- Egress broker
- SARIF support
- SQLite first
- ReplaySafe state model
- Idempotency semantics
- Locking strategy
- OpenTelemetry compatibility
- Rule versioning
- Baseline design
- Suppression design
- Release/versioning strategy
- Model advisor isolation
- TypeScript/n8n workspace
- MCP scope boundaries

For each ADR specify:

- Decision
- Context
- Options considered
- Trade-offs
- Consequences
- Revisit trigger

---

# 14. Questions the Plan Must Answer

The final plan must explicitly answer:

1. What is the smallest useful first release?
2. Which three rules should be implemented first, and why?
3. What analysis can be done reliably without executing user code?
4. How will LangGraph code be recognized?
5. How will custom tools be classified?
6. How will side effects be represented?
7. How will unsafe retries be detected statically?
8. What cannot be detected statically?
9. How will ReplaySafe handle uncertain success?
10. How will idempotency keys be generated and validated?
11. What happens if the ledger is unavailable?
12. What happens during concurrent execution?
13. How are compensation actions defined?
14. How are chaos tests prevented from touching production?
15. How are invariants evaluated?
16. How will reports remain stable across versions?
17. How will SARIF fingerprints remain stable?
18. How will suppressions avoid becoming permanent blind spots?
19. How will plugins declare compatibility?
20. How will the project remain useful without an LLM?
21. How will remote-model use be isolated and auditable?
22. What belongs in the core versus plugins?
23. Which existing tools overlap with this project?
24. What exact gap should this toolkit own?
25. Which features should explicitly not be built before v1?
26. How can external contributors safely add new rules?
27. How will the system avoid executing malicious repository code?
28. How will the project support air-gapped users?
29. What is the upgrade and migration strategy?
30. What would make the project credible enough for real production use?

---

# 15. Explicit Non-Goals Before v1

Unless you provide a strong reason otherwise, the plan should keep these out of scope before v1:

- Hosted SaaS control plane
- Multi-tenant backend
- General agent orchestration framework
- Visual workflow editor
- Replacement for LangSmith or Langfuse
- General SIEM
- General-purpose MCP vulnerability scanner
- Custom model training
- Autonomous code modification
- Automatic remote repository upload
- Enterprise SSO
- Billing
- Team collaboration backend
- Cloud dashboard
- Marketplace
- Support for every agent framework
- Automatic execution of user repositories

---

# 16. Output Format

Return the planning result as a structured Markdown document with these sections:

1. Executive summary
2. Product definition
3. Scope and non-goals
4. User personas
5. Main use cases
6. Competitive and overlap analysis
7. Architecture overview
8. Trust boundaries
9. Privacy and egress architecture
10. Package and repository structure
11. Domain model
12. Plugin architecture
13. Rule engine design
14. `agent-lint` design
15. LangGraph plugin design
16. ReplaySafe design
17. Agent Chaos design
18. Agent Contract design
19. Trace and audit design
20. GitHub Action design
21. VS Code design
22. MCP plan
23. n8n plan
24. Optional model advisor
25. Threat model
26. Testing strategy
27. Documentation strategy
28. Release and versioning strategy
29. ADR list
30. Complete milestone plan
31. Complete ordered PR plan
32. Release checkpoints
33. Critical risks
34. Open questions and assumptions
35. Recommended first implementation PR
36. Definition of v1.0 readiness

Use tables where they improve clarity.

For the PR plan, use one detailed subsection or table per PR.

Do not compress multiple unrelated PRs into one row.

---

# 17. Planning Behavior

- Challenge weak assumptions.
- Prefer clear contracts over vague extensibility.
- Prefer local deterministic behavior.
- Prefer small public APIs.
- Prefer standard formats.
- Prefer testable failure semantics.
- Prefer boring infrastructure.
- Avoid architecture astronautics.
- Avoid premature distributed systems.
- Avoid speculative plugins.
- Avoid making the LLM a security boundary.
- Avoid adding a database server when SQLite is enough.
- Avoid hiding uncertainty.

If information is missing:

- Make a reasonable default assumption.
- Label it clearly.
- Continue the plan.
- Do not stop the work merely to ask a question unless the plan is impossible without the answer.

---

# 18. Final Quality Gate

Before completing the plan, verify that:

- Every product component appears in the architecture.
- Every product component has implementation PRs.
- Every PR has tests, docs, security notes, and acceptance criteria.
- Every milestone ends in a usable repository state.
- No PR leaves knowingly broken main.
- No core feature depends on a hosted service.
- Offline mode is complete.
- Remote model usage is optional and isolated.
- The first release is genuinely useful.
- The full plan reaches a credible v1.0.
- The plan does not quietly become another orchestration framework.
- The plan explains exactly where this project is differentiated.
- The plan is executable by coding agents without requiring architectural redesign.
