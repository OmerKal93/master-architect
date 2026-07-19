# ART-0 — Acceptance-Test Evidence

Real, executed proof for every acceptance test in `docs/ART-0-plan.md` section 6. All 29 tests pass (24 original + 5 regression tests added during independent-review remediation). Full raw pytest output below.

## Dependency pin (Batch 2)

`agent-chaos==0.1.3` — exact pin, confirmed via `pip list`:
```
agent-chaos          0.1.3
langgraph            0.2.76
```
Unmodified: no fork, no monkeypatch of `agent_chaos` internals, no vendoring — confirmed by independent review (import-time integrity check, no `sys.path` tricks, no `agent_chaos.__init__` override anywhere in this package).

License: Apache-2.0 (confirmed in ART-0-plan.md section 3 via direct LICENSE fetch during planning). No fork means no NOTICE-passthrough obligation is triggered.

## AT1 — go/no-go gate (`tests/test_at1_go_no_go_spike.py`)

Real `langgraph.graph.StateGraph` + real `langchain_anthropic.ChatAnthropic` + real, unmodified, pinned `agent_chaos`. Only the outbound Anthropic transport is stubbed (installed before `agent_chaos` captures a reference to it — zero real network calls, zero API key required or used for anything beyond an inert placeholder string).

Result: **PASS**. `ToolTimeoutChaos.on_call(2)` correctly mutated the second real request's `tool_result` content to a timeout message; the real tool executed exactly once (the commit); the control run (no chaos configured) delivered the real, unmutated result.

Corrected twice before landing here — see the test file's own header for the full history: the original plan's framing (Anthropic-through-LangChain) was right; an independent plan review redirected it based on an inaccurate claim from an earlier research pass; reading `agent_chaos/patch/providers/anthropic.py`'s actual source during implementation proved the original framing correct and reverted the redirect. Disclosed, not silently fixed.

## AT2-AT4 — broken/fixed sample pair (10 runs each)

`tests/test_at_most_once_broken_sample.py` — **10/10 runs fail** (real double-charge: 2 ledger entries for `request_id=req-1`, contract correctly raises `ContractViolation`).

`tests/test_at_most_once_fixed_sample.py` — **10/10 runs pass** (idempotency guard holds: 1 ledger entry, contract raises nothing).

Identical agent retry script and identical fault configuration in both — only the tool's idempotency handling differs (confirmed by independent review). Deterministic by construction (scripted stub, no real model call, no randomness) — all 10 runs per sample are byte-identical, which is itself the AT2 proof (call-index trigger, not probabilistic).

Sample AT5 failure message (captured directly, not paraphrased):
```
art_contracts.contract.ContractViolation: [at_most_once] violated by tool 'process_refund': invoked more than once with identical ('request_id',)=('req-1',) (first at call #1, again at call #2) (offending call index: 2)
```

## AT6 — AO-1 mutation dogfood (`tests/test_ao1_dedup_mutation_dogfood.py`)

Real `node` subprocess calls. The "real" case requires HarnessKit's own, unmodified, already-merged `claimDecisionDispatch` (`scripts/manager-advisor/ao1-dispatch.js`) by path — read-only, never edited. The "mutant" is a standalone reimplementation with BOTH real dedup layers removed (existing-file pre-check AND the exclusive-create `wx` flag — corrected from an earlier, incomplete "one check removed" claim after independent review proved removing only the pre-check would still be caught by the `wx` flag).

- Real, unmodified AO-1: 1 successful claim out of 2 attempts → `at_most_once` **passes**.
- Mutant: 2 successful claims out of 2 attempts (bug reproduced) → `at_most_once` **fails**, correctly caught.

HarnessKit repo (`C:/Dev/hk-worktrees/phase-a-v1-integration`) confirmed untouched (`git status --short` empty) before and after every test run in this package, including this one. Fresh `preflight.js` (14/14) and full `local-ci.js` (58/58) both re-run clean from that repo after this work.

## Independent review — findings and disposition

A fresh-context adversarial reviewer read all 18 original files, ran the real 24-test suite, and wrote standalone probe scripts to mechanically attack each design claim rather than trust the docstrings. Verdict: all four central claims held (no live network calls, contract correctness on the happy path, broken/fixed isolation, AO-1 mutant fidelity, exact pin with no fork, clean scope). Six real, mechanically-reproduced findings at the edges, all fixed:

| Severity | Finding | Fix |
|---|---|---|
| Medium | Async Anthropic transport (`AsyncMessages.create`) was never stubbed — reviewer proved `.ainvoke()` reaches the real `httpx` async transport | `patched_anthropic_with_chaos` now also installs a loud-failure guard (`AsyncPathNotStubbedError`) on the async path; both AT1 tests refactored to use the shared, now-fixed helper instead of duplicated inline patching |
| Medium | `check_at_most_once` silently collided two genuinely different tool calls with no `request_id` onto the same `(tool, None)` key — false-positive violation | Raises `MissingKeyFieldError` immediately if a key field is absent from an invocation's args, instead of silently comparing `None` |
| Medium | `_run_node_fixture` decoded subprocess stdout with the OS locale codepage, not UTF-8 — reviewer reproduced a silent decode failure with a non-ASCII path | `subprocess.run(..., encoding="utf-8")` explicit |
| Low | Mutant fixture's header comment claimed "one `if` block removed" but that alone wouldn't reproduce the bug (the `wx` exclusive-create flag also had to go) | Header corrected to name both removed layers; test itself was already valid, only the comment was wrong |
| Low | AO-1 dogfood test hardcoded an external repo path with no skip guard — would fail with a raw Node stack trace if the worktree is ever cleaned up | `@pytest.mark.skipif` with a clear reason |
| Low | `ingest_ao1_claim_log` raised a raw `KeyError` on a differently-shaped `ok:true` line | Raises `MalformedClaimLogEntryError` with the log path, line number, and the actual entry |

Every fix has a dedicated regression test (`test_langgraph_adapter_async_guard.py`, `test_contract_edge_cases.py`, `test_ao1_adapter_edge_cases.py`, plus the corrected mutant-header comment and skipif guard verified by the existing AT6 tests still passing).

## Full raw pytest output (this run)

```
29 passed, 1 warning in 19.01s
```

Full verbose transcript captured at implementation time; category counts: `test_ao1_adapter_edge_cases.py` (2), `test_ao1_dedup_mutation_dogfood.py` (2), `test_at1_go_no_go_spike.py` (2), `test_at_most_once_broken_sample.py` (10), `test_at_most_once_fixed_sample.py` (10), `test_contract_edge_cases.py` (2), `test_langgraph_adapter_async_guard.py` (1).
