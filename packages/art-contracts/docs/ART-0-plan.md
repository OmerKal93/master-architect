# ART-0 — Corrected Product Decision + Contracts-First Vertical Slice Plan

Governance: real `ManagerDecision` `dec-97a7cd30350b` (AO1_READY) + real AO-1 dispatch `dispatch-444be3d3-cb51-4826-a67e-c199a020e66c` (COMPLETED). Isolated scratch root, Phase-A repo state untouched. This is a PLAN only — no product code implemented, no permanent agent created, no push, no routing change.

**Revision note**: this version incorporates an independent feasibility+scope review's findings (Section 9). Sections 3/5/6/8 below are the corrected versions.

## 1. Corrected product decision

Contracts-first (not injection-first). Delivery: pytest plugin (not CLI). Target segment: pre-prod blocker + double-send agents (not post-incident payments-only). Wedge: at-most-once contract + timeout-after-commit fault + LangGraph + pytest, per the verified (`modelUsage`-attested `claude-fable-5`) consultation. Full basis: `fable2-result-text.md`, `fable2-invocation-receipt.json` (this directory).

## 2. Temporary research agents — status

Both remain **TEMPORARY / PROMOTION_CANDIDATE only**. No permanent agent created, no `config/agent-identity-registry.json` entry added, no permissions expanded.
- Market/technical research agent (`dispatch-611ad912-...`, dec `dec-fb67b6086a6b`) — scored and recommended RETAIN as promotion candidate in the prior report.
- Technical due-diligence agent (`dispatch-444be3d3-...`, dec `dec-97a7cd30350b`) — evaluated `deepankarm/agent-chaos` source+license with file/line-cited findings. Independent review flagged that its raw-file citations aren't preserved as standalone evidence artifacts in the scratch directory (Finding D/evidence-trail note, Section 9) — the citations exist in this session's transcript but not as separately fetchable files. Recommend RETAIN as promotion candidate for a future permanent "technical due-diligence" role, **conditional on**: future dispatches of this role persist raw source citations as durable evidence files, not just transcript content. Decision on permanent promotion deferred, not made here.

## 3. Build-vs-adopt decision: **ADOPT (v1) — ADAPT deferred, not needed for the vertical slice**

**Corrected from the original ADAPT verdict** (independent review Finding C): the vertical slice's fault (`ToolTimeoutChaos`, Section 4) is a **tool-level** fault. The technical due-diligence agent's own findings state tool-level chaos classes (`tool_error`, `tool_timeout`, `tool_mutate`) are "provider-agnostic, operate on tool results not the LLM client" — they never touch `chaos/llm.py`'s `to_exception()` method, which is the only place the Anthropic-only limitation exists. **The OpenAI `to_exception()` gap is irrelevant to this vertical slice** and forking it now is scope creep with no v1 consumer — dropped entirely from ART-0.

**v1 decision: ADOPT `deepankarm/agent-chaos` as a pinned dependency, unmodified**, for its `TriggerConfig`/`ChaosBuilder` deterministic `on_call(N)`/`after_calls(N)` trigger mechanism and its `ToolTimeoutChaos` class. No fork, no source modification, no NOTICE-passthrough obligation triggered (only applies to modified files under Apache-2.0 §4(b) — pinning/depending-on doesn't modify anything).

**ADAPT (forking `to_exception()` for OpenAI/Gemini) is deferred**, named here as a real, concrete future decision point: revisit only if/when ART needs LLM-client-level (not tool-level) fault injection for a non-Anthropic provider — not before.

License: Apache-2.0, confirmed via direct LICENSE fetch. No copyleft, no patent conflict. Fully compatible with a pinned-dependency ADOPT.

**Corrected go/no-go gate** (independent review Finding A — the original gate tested the wrong subsystem): the real, load-bearing unknown is whether `agent-chaos`'s `ToolTimeoutChaos` (tool-level chaos) correctly fires and is observable when the tool is invoked through **LangGraph's `ToolNode`** (LangGraph's own tool-execution mechanism), not whether the Anthropic-SDK-level monkeypatch works through `ChatAnthropic` (a different subsystem the vertical slice never calls). See corrected AT1, Section 6.

## 4. First contracts-first vertical slice

- **Contract**: `at_most_once` — the side-effecting tool (e.g. `process_refund`) must not be invoked more than once with the same idempotency-relevant arguments within one scenario run.
- **Fault**: `timeout_after_commit` — inject a timeout fault (via `agent-chaos`'s `ToolTimeoutChaos`, triggered with `on_call(N)` where N = the call index of the already-committing tool call) that fires AFTER the side-effecting call has already returned success server-side, forcing the agent's own retry/error-handling logic to run.
- **Framework**: LangGraph.
- **Delivery**: pytest plugin/fixture (`art_contracts` fixture, or a `@art.contract("at_most_once")` marker) — not a new CLI verb, per the verified consultation's explicit "pytest beats a new CLI verb" finding.
- **Seeded broken sample**: a small reference LangGraph refund-agent with a real, deliberately-included double-charge bug (no idempotency-key check before retrying after a tool timeout).
- **Seeded fixed sample**: the same agent with the idempotency-key check added — used to prove the contract check correctly flips FAIL→PASS, not just always-FAIL.

## 5. Two dogfood targets

**Target 1 — AO-1 mutation testing, narrowed to the one mutant that actually maps to the v1 contract** (independent review Finding B: the original 3-mutant scope required 2 contract types the vertical slice doesn't build, and an AO-1-trace ingestion adapter no batch budgeted). Corrected scope: **one mutant only**.

1. Remove/bypass `decision_id` sanitization in `ao1-dispatch.js#claimDecisionDispatch` (verified real, `scripts/manager-advisor/ao1-dispatch.js:136` in the HarnessKit repo) → the `at_most_once`-shaped contract (re-expressed as "at most one dispatch claim per decision_id") must catch the reintroduced dedup-bypass.

Explicitly deferred, not silently dropped: mutant 2 (`consumeApprovalEvidence`, real, `ao1-dispatch.js:220` — single-use grant consumption) and mutant 3 (`budgetEnforcer.isBudgetHalted`, real, `scripts/budget-enforcer.js:157` — pre-dispatch halt check) require contract types (`exactly_once_consumption`, `precondition_guard`) ART's v1 doesn't build. Revisit once ART supports more than one contract type.

**New, explicitly budgeted requirement** (independent review Finding B, "Related"): AO-1's dispatch-call trace shape (subprocess spawn/collect records) differs structurally from the LangGraph tool-call trace shape Target 2 produces. Target 1 needs its own minimal trace-ingestion adapter (reads AO-1's real dispatch/claim-registry records into the same `at_most_once` checker) — budgeted explicitly in Batch 5 below, not assumed to reuse Target 2's ingestion path.

Pass condition: ART's contract checker fails (detects) the mutant, AND passes clean on the real, unmutated AO-1 code. A checker that goes green on a broken mutant is itself broken — this tests ART's detection power, not AO-1's reliability (already independently proven via AO-1's own review-remediated self-tests/evals this session).

**Target 2 — external-shaped LangGraph sample** (external-validity proof; addresses the verified consultation's "AO-1's trace shape doesn't resemble a real user's agent" critique). The seeded broken/fixed refund-agent pair from Section 4 itself IS this target — genuine LLM tool-calling trace shape (LangGraph node/tool-call sequence), not a subprocess-dispatch trace.

## 6. Acceptance tests

- **AT1 (go/no-go gate, Batch 1 — corrected)**: `agent-chaos`'s `ToolTimeoutChaos`, triggered via `on_call(N)`, correctly fires and is observable when the target tool is invoked through **LangGraph's `ToolNode`** (LangGraph's own tool-execution path), verified via a real minimal LangGraph harness. **If this fails, ADOPT is voided; fall back to BUILD_NARROW (write the one tool-call interception path needed for LangGraph directly, reusing only `agent-chaos`'s fault taxonomy as reference).**
- **AT2 (reworded)**: `on_call(N)` fires on exactly the Nth tool call, deterministically, across all 10 repeated runs of the broken sample — no probabilistic/random-seed dependency (call-index-based, not clock-based; "timing variance" was an imprecise framing).
- **AT3 (reworded, drops rate-language)**: `at_most_once` contract check fails on all 10 runs of the broken sample (not framed as a "100% true-positive rate" — that implies a statistical guarantee 10 runs can't support, exactly the overclaim the verified Fable consultation warned against for `--runs 10`-style framing).
- **AT4 (reworded, drops rate-language)**: `at_most_once` contract check passes on all 10 runs of the fixed sample (not framed as "0% false-positive rate," same reasoning as AT3).
- **AT5 (message format specified)**: pytest plugin surfaces the result as a normal pytest pass/fail; on failure, the assertion message names the violated contract (`at_most_once`), the offending tool name, and the call index/arguments of the duplicate invocation.
- **AT6 (narrowed to Target 1's single mutant)**: the one deliberately-broken AO-1 mutant (`claimDecisionDispatch` dedup bypass) is caught by the AO-1 trace-ingestion adapter + `at_most_once` checker; the real, unmutated AO-1 passes clean.
- **AT7 — removed** (was conditional on the now-dropped OpenAI `to_exception()` fork; no longer applicable to v1).
- **AT8 — removed** (was NOTICE-passthrough for a fork that no longer exists in v1; ADOPT-as-pinned-dependency triggers no NOTICE obligation).

## 7. Evidence requirements

- Real trace files (not summaries) for every one of the 10 runs per sample, both broken and fixed (Target 2), plus the AO-1 mutant run (Target 1).
- Real, unparaphrased pytest output for every pass/fail claim.
- Real diff of the single AO-1 mutant used for Target 1 (auditable exactly what was broken and reverted).
- Real AO-1 trace-ingestion adapter code/output sample (proving Target 1 and Target 2 use genuinely different trace shapes, not a shared fiction).
- Independent review verdict recorded before ART-0 is declared implementation-ready.

## 8. Implementation batches (plan only — not implemented)

1. **Go/no-go spike (corrected)**: AT1 only — `ToolTimeoutChaos` through LangGraph's `ToolNode`. Resolves the ADOPT-vs-BUILD_NARROW fork before anything else proceeds. This is the real gate; nothing below assumes it passes.
2. **Adopt agent-chaos**: pin as a dependency (no fork), confirm license obligations (none beyond standard attribution for an unmodified dependency).
3. **Contract + pytest surface**: `at_most_once` as a plain trace assertion (no DSL yet), pytest plugin/fixture delivery, message format per AT5.
4. **External-shaped sample pair**: seeded broken + fixed LangGraph refund-agent (Target 2).
5. **AO-1 mutation dogfood (corrected scope)**: the one deliberate break (`claimDecisionDispatch`) + the AO-1 trace-ingestion adapter (new, explicitly budgeted per Section 5) + contract mapping (Target 1).
6. **Acceptance-test run + evidence packet + independent review**: run AT1-AT6 against both targets, assemble the evidence packet, get an independent review verdict before declaring ART-0 done.

Batch order: 1 gates everything for real (Batches 2-6 all depend on `ToolTimeoutChaos`+LangGraph working); 2-3 can run in parallel once 1 passes; 4 depends on 2-3; 5 depends on 2-3 plus its own new trace-ingestion-adapter sub-task; 6 depends on 4-5.

## 9. Independent review — findings and disposition

A fresh-context reviewer (feasibility + scope-guardian scope, no authorship knowledge) read this plan plus its cited evidence files. Verdict: NOT READY round 1 (three items needing rework, two minor wording fixes, one item that turned out to be a false alarm caused by searching the wrong repository). All six real findings are reflected in the corrected sections above.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| A | High | Original Batch 1 go/no-go gate (AT1) tested the Anthropic-SDK-through-LangChain monkeypatch — a subsystem the vertical slice's tool-level fault (`ToolTimeoutChaos`) never calls. The real load-bearing unknown (does tool-level chaos work through LangGraph's `ToolNode`) was untested by any acceptance test. | Fixed: AT1 and Batch 1 redefined to test `ToolTimeoutChaos` through `ToolNode` directly (Sections 3, 6, 8). |
| B | High | Target 1 (AO-1 mutation testing) required 3 contract types; only 1 (`at_most_once`) was scoped to be built anywhere in the plan. AT6 presupposed checkers 2 and 3 existed. Also: no batch budgeted the AO-1-trace-to-ART ingestion adapter Target 1 needs (AO-1's trace shape differs from LangGraph's). | Fixed: Target 1 narrowed to the one mutant (`claimDecisionDispatch`) that maps to `at_most_once`; mutants 2/3 explicitly deferred, not silently dropped; trace-ingestion adapter explicitly budgeted in Batch 5. |
| C | Medium-High | OpenAI `to_exception()` fork (original Batch 2) was scope creep — the vertical slice's tool-level fault never touches `to_exception()` at all (tool-level chaos is provider-agnostic per the technical agent's own findings). | Fixed: build-vs-adopt verdict corrected from ADAPT to ADOPT-as-pinned-dependency for v1; the fork work is dropped entirely, named as a deferred future decision point only. AT7/AT8 removed as no longer applicable. |
| D | (false alarm) | Reviewer reported `claimDecisionDispatch`, `consumeApprovalEvidence`, `budgetEnforcer.isBudgetHalted` as unverifiable/misnamed, having searched `omer-os`/`~/.claude` only. | **Not a defect** — independently re-verified directly against the real target repo (`C:/Dev/hk-worktrees/phase-a-v1-integration`): all three names exist exactly as cited (`scripts/manager-advisor/ao1-dispatch.js:136` and `:220`, `scripts/budget-enforcer.js:157`). The reviewer searched the wrong codebase (had no way to know about this session's separate HarnessKit work). Retained in Section 5 unchanged. The evidence-trail gap the same finding raised (technical agent's raw-source citations not persisted as standalone files in the scratch dir) is real and noted as a conditional in Section 2. |
| E | Low | AT2's "zero timing variance" was an imprecise category (call-index trigger, not a clock); AT5 lacked a message-format spec. | Fixed: AT2 reworded to "deterministic, call-index-based, not clock-based"; AT5 given a concrete message-format spec. |
| F | Low-Medium | AT3/AT4's "100% true-positive / 0% false-positive... from n=10" framing reintroduced the exact statistical overclaim the verified Fable consultation explicitly warned against (`fable2-result-text.md` §1, re: `--runs 10 ... "prove"`). | Fixed: reworded to "fails on all 10 runs / passes on all 10 runs" — states what was actually measured, no implied statistical guarantee. |
