# TS/JS Frontend — Real Dogfood Run Against HarnessKit

Real `agent-lint scan` run (not a fixture, not simulated) against
`C:/Dev/hk-worktrees/phase-a-v1-integration/scripts` — HarnessKit's own real, production
JavaScript source tree (~100+ files), using the new `TsJsFrontend`. Zero code was written, run,
or modified in HarnessKit's repo by this scan — read-only static analysis only, matching this
package's own "never execute scanned code" contract (`ts.createSourceFile` only parses).

## Result

**8 findings, all AR001 (unbounded agent loop).** Zero AR003 or AR014 findings against this
target — accurate: HarnessKit's own JS scripts don't call any of the recognized HTTP/SDK call
shapes without a timeout, and the manual-retry-loop patterns they do have (see
`review-independence/run-json-atomic.js`) already pass a bound through, just not in the shape
this frontend's narrow heuristic recognizes (see below).

## Accuracy review (manual, ahead of the independent review)

**7 of 8 findings: genuine true positives, matching the rule's own honest scope.** Each is a
recursive directory-tree-walker function (`walk`, `listJsFilesRecursive`,
`validateAgainstSchema`, ...) with no statically visible depth/counter guard — e.g.
`scripts/cce-receipts.js:218`'s `walk(d)` genuinely recurses on every subdirectory with no depth
limit in source. In practice these are safe (Node's `Dirent.isDirectory()` does not follow
symlinks, so a real symlink cycle can't actually trigger unbounded recursion) — but that safety
property is not visible to static analysis, and the rule's own module docstring says exactly
this is expected: "False positives on non-agent `while True:`-shaped loops are expected and are
a rule-confidence question, not a frontend-recognition question." Working as designed, not a
TS/JS-specific defect.

**1 of 8 findings: a real, disclosed false positive relative to the code's actual safety —
`review-independence/run-json-atomic.js:97`'s `for (;;) { try { return fn(); } catch (e) { if
(!isContendedLockError(e) || Date.now() >= deadline) throw e; ... } }`.** This loop IS genuinely
bounded (`deadline` is checked every iteration, and `throw e` really does exit the loop by
propagating out of the function) -- but the bound-detection heuristic
(`hasVisibleStepBound`/`_has_visible_step_bound`) only recognizes a bare `if <comparison>: break`/
`return`-shaped exit, not a compound `||` condition or a `throw`-based exit. **This is not a
JS/TS-specific gap**: the identical Python shape (`while True: try: return fn() except
Exception as e: if not is_contended(e) or time.time() >= deadline: raise; ...`) would be missed
by `loops.py`'s own `_has_visible_step_bound` for the exact same reason (compound condition,
`raise` not recognized as an exit) — this is a real, pre-existing, honestly-documented limitation
of the *shared* heuristic, reproduced here rather than introduced by this frontend. Not fixed in
this slice: widening the bound-detection heuristic (to look inside compound boolean expressions,
or to recognize `throw`/`raise` as a valid exit) is a real, separate improvement to the shared
rule logic, out of scope for "smallest real slice, no new rules/frameworks."

## Bug found and fixed during this dogfood run

`AR001`'s own evidence-text formatting (`rule.py#_evidence_for`) hardcoded Python's `def` keyword
and the literal Python spelling `while True:` — factually wrong when the underlying `Agent` (a
language-neutral IR entity) came from a JS/TS file, whose source never says `def`. Found by
reading this run's real output (`def walk(...)` shown next to a `.js` file path) rather than
inferred abstractly. Fixed: both strings are now language-neutral (`"walk(...) calls itself..."`,
`"unconditional loop (no counter check + break/return...)"`). One test
(`test_anonymous_agent_evidence_mentions_while_true`) asserted the old, now-incorrect literal
text; updated to assert the corrected, language-neutral wording instead
(`test_anonymous_agent_evidence_mentions_unconditional_loop`). This fix applies to Python findings
too (the text is shared, not duplicated per-language) — a real accuracy improvement discovered by
extending scan coverage to a second language, not something either language's fixtures alone
would have surfaced.

## What this dogfood run does NOT show

This target (HarnessKit's `scripts/`) has no AR003 or AR014-shaped code, so this run alone does
not exercise those two rules' TS/JS parity end-to-end against a real, independently-written
codebase — that proof lives in the fixture corpus (`fixtures/rules/AR003/`,
`fixtures/rules/AR014/`), not in this dogfood run. Named explicitly rather than left implicit.

## Independent review (fresh-context adversarial reviewer)

A fresh-context `ce-adversarial-reviewer` agent reviewed the full staged diff (no authorship
context, told to independently verify every safety/parity/scope claim above, not take it on
faith). It empirically reproduced its findings rather than reading code and guessing. 7 findings,
2 fixed as critical, 1 fixed as high, 2 fixed as medium, 2 left as disclosed advisory (out of
"smallest real slice" scope):

- **F1 (critical, fixed).** A missing/broken `typescript` npm dependency (e.g. `node_modules`
  never installed) made three `ts_js_frontend.py` failure paths — Node not on PATH, parser
  subprocess exiting non-zero, malformed JSON on stdout — emit an un-prefixed diagnostic. The
  CLI's exit-code contract (`cli.py`) only maps `SCAN_LIMIT_PREFIX`-prefixed diagnostics to exit
  4 ("partial scan"); anything else with zero findings is exit 0 ("clean scan"). Net effect: a
  broken TS/JS toolchain made `agent-lint scan` report a *clean* scan on a directory full of real
  AR001/AR014 violations. Fixed: all three diagnostics now carry `SCAN_LIMIT_PREFIX`. (An
  ordinary per-file syntax error is deliberately left un-prefixed, matching Python's own
  `ast.parse` `SyntaxError` precedent — that's a real, isolated parse failure, not a broken
  toolchain.) Regression tests added in `tests/lint/frontend/test_ts_js_frontend.py`
  (`TestToolchainFailuresAreScanLimitConditions`).
- **F2 (critical, fixed).** `.github/workflows/ci.yml` never installed Node or the new
  `tools/ts_frontend` npm dependency — a fresh CI checkout would fail 12 of 54 fixture cases
  (every unsafe TS/JS fixture silently reporting zero findings). Fixed: added a pinned
  `actions/setup-node@v4.4.0` step plus `npm ci --prefix packages/agent-lint/tools/ts_frontend`
  before the pytest step, on all three OS matrix legs.
- **F3 (high, fixed).** `detectRetryPolicies()` in `parse_one_file.mjs` never recognized
  `for(;;)` as an unconditional loop for AR014, even though AR001's own detector in the same file
  already treats `for(;;)` and `while(true)` as the same concept. Root cause on closer read: the
  `if (ts.isForStatement(node))` branch matched *every* for-statement first, so the `else if`
  unbounded-loop branch was structurally unreachable for any for-statement. Fixed by nesting the
  infinite-for check inside the for-statement branch instead of chaining it as a sibling
  `else if`. Regression fixture added: `fixtures/rules/AR014/unsafe/manual_for_infinite_retry.js`
  (mirrors `manual_while_true_retry.js`, spelled with `for(;;)`), plus a unit test in
  `test_ts_js_frontend.py`.
- **F4 (medium, fixed).** AR001's evidence text was de-Pythonified during the dogfood run above,
  but AR003's evidence/remediation ("no `timeout=` keyword argument") and AR014's remediation
  ("`for _ in range(N):`") still asserted Python-only syntax on JS/TS-sourced findings. Fixed:
  AR003's strings are now language-neutral ("no visible timeout configuration"); AR014's
  remediation is now conditional on `retry_policy.source` — language-neutral wording for the
  shared `"manual-loop"` source, Python-library-specific wording preserved for the genuinely
  Python-only `"tenacity"`/`"stamina"` sources.
- **F5 (medium, documented not fixed).** Adding `"axios"` to the shared, language-neutral
  `_HTTP_LIBRARY_CALLEES` allowlist means a `.py` file with a local object literally named
  `axios` calling `.post(...)` with no timeout now also fires AR003 — a real, verified behavioral
  change on `.py` files this task asked to keep unchanged, though the realistic blast radius is
  a Python identifier that happens to share a name with a JS HTTP library. Documented as an
  accepted, disclosed trade-off in `ar003/rule.py`'s allowlist comment rather than special-cased,
  since special-casing would require the IR to carry source-language metadata it does not
  currently have — out of scope for this slice.
- **F6 (low, disclosed, not fixed).** Node subprocess startup (~290ms/file measured) is roughly
  2-3 orders of magnitude slower than Python's in-process `ast.parse`, sharing the same 60s
  scan-wide wall-clock budget — a JS/TS-heavy repo hits the budget around ~200 files. Handled
  honestly today (a real `SCAN_LIMIT_PREFIX`-prefixed diagnostic, exit 4, no silent truncation);
  a per-frontend budget tuning pass is a separate future improvement, not in this slice.
- **F7 (low, disclosed, not fixed).** `literalForLoopBound()` derives a bounded `for` loop's
  `max_attempts` from the comparison operand only, without checking the loop counter's starting
  value (e.g. `for (let i = 5; i <= 10; i++)` reports 11 instead of 6). Verified this has zero
  effect on any finding — AR014's gating logic never reads `max_attempts`, only `bound`. Left as
  a known cosmetic gap in unused metadata.

The reviewer also independently re-verified (no changes needed): the non-execution safety
contract (no `eval`/`Function`/`require`/`child_process` on scanned content), that all three
resource limits are genuinely enforced (not cosmetic), the argv-list subprocess invocation (no
shell-injection surface), Windows-specific path/encoding handling, graceful degradation on empty/
syntax-error/non-UTF8 files, and the dogfood run's own false-positive claim about
`review-independence/run-json-atomic.js:97` (confirmed accurate — and confirmed to be a distinct
gap from F3, since that file's loop exits via `return`/`throw`, not `break`, so F3's fix does not
change its classification). It also corrected one factual detail in this document's premise: the
`typescript` npm package is Apache-2.0 licensed (matching this repo's own license), not MIT as
originally assumed when scoping the dependency addition — a trivially compatible correction, not
a licensing concern.

All 54 fixture cases and the full pytest suite (218 passed, plus the 2 pre-existing,
diff-unrelated failures already disclosed above) were re-verified green after applying the F1-F4
fixes.

## Gap closure (2026-07-20): the confirmed FP and F6 are both fixed

The two open items this doc named above -- the `run-json-atomic.js:97` false positive and F6's
scan-limit truncation risk -- were both real bugs, not permanent limitations, and are now fixed.

**1. AR001 compound-condition + `throw`-as-exit false positive -- FIXED.** Root cause:
`_has_visible_step_bound` (`loops.py`) / `hasVisibleStepBound` (`parse_one_file.mjs`) only
recognized a bare `if <comparison>: break/return` -- a compound condition
(`if not is_contended(e) or time.time() >= deadline: raise`) was invisible to it on two counts:
the comparison was nested inside a `BoolOp`/`||`-expression rather than being the `if` test
directly, and the exit was a `raise`/`throw`, not a `break`/`return`. Fixed in both languages
identically: the test-expression check now searches the whole condition tree for a qualifying
comparison (`_test_contains_bound_comparison` / `testContainsBoundComparison`), and `raise`/
`throw` are now accepted exits alongside `break`/`return`. Verified the fix does NOT overcorrect:
a compound condition with no relational comparison anywhere (e.g. `if flagA || flagB: log(...)`)
is still correctly reported as unbounded -- covered by a dedicated negative test in both
languages. Regression fixtures added:
`fixtures/rules/AR001/safe/harnesskit_pattern_retry_on_contention.{py,js}` (real HarnessKit
shape, inspired by `run-json-atomic.js`'s `retryOnContention`), plus unit tests in
`test_python_frontend.py` and `test_ts_js_frontend.py`. Full fixture harness: **56/56** (was 54).
Full pytest: **224 passed** (was 219), same 2 pre-existing, diff-unrelated failures, zero
regressions.

**2. F6 (full-repo scan hitting the wall-clock budget) -- FIXED.** Root cause was architectural,
not a tuning problem: a fresh `node parse_one_file.mjs` process was spawned per file, and Node
startup + `require('typescript')` (a large module) measured at ~290ms/file dominates real parse
time for a typical file -- on a repo with hundreds of JS/TS files that overhead alone exceeded
the 60s whole-scan budget. Fixed without touching any detection logic: `parse_one_file.mjs`
gained an additive `--serve` mode (a persistent process that reads newline-delimited JSON
requests from stdin and writes one newline-delimited JSON response per file, reusing its already
-loaded `typescript` module across the whole scan; the pre-existing single-shot mode is
byte-for-byte unchanged and both modes share the same `parseOne()` parsing function, so results
are identical either way). `ts_js_frontend.py` gained a `_TsJsWorker` that lazily starts and
reuses one `--serve` subprocess per `TsJsFrontend` instance, with a background reader thread and
a timeout matching the existing per-file time budget; on ANY worker failure (missing Node,
crashed process, timeout, malformed response, protocol desync) it returns `None` and `lower()`
falls straight back to the original one-process-per-file `subprocess.run()` path, which is
unchanged since before the worker existed and remains the single source of truth for every
toolchain-failure diagnostic (including the F1 `SCAN_LIMIT_PREFIX` fixes). Real before/after,
same target used to find F6 originally (`hk-worktrees/phase-a-v1-integration`, full repo, no
scoping): **before, hit the 60s scan-limit budget with files left unscanned; after, completes
cleanly in ~6.1s.** Verified reuse is real, not assumed: a new regression test
(`TestWorkerReuse`) monkeypatches `subprocess.Popen` and asserts exactly one process is spawned
across 5 `lower()` calls on one `TsJsFrontend` instance, and exactly two across two separate
instances (reuse is per-instance, never a hidden global). Known, disclosed trade-off: pytest
itself constructs ~10 fresh `TsJsFrontend()` instances across the test suite, each lazily
spawning its own worker if it reaches real source content; these are cleaned up via `atexit`
(registered once per instance) rather than an explicit per-scan close, so in the worst case a few
worker processes linger until the pytest process itself exits -- acceptable given the real
(single-instance-per-scan) usage in `scan.py` and `art_rule_test.py` never hits this at all, and
not worth a more elaborate lifecycle-management mechanism for ~10 test-only processes.

**3. Full re-scan after both fixes, both real HarnessKit trees:**

- `hk-worktrees/phase-a-v1-integration` (full repo, untruncated this time): **13 findings**, down
  from the prior truncated run's 11 (which had already missed files) and the scoped
  `scripts/`+`evals/` run's 14 (which included the now-fixed false positive). All 13 are AR001,
  all the same already-documented true-positive class (unguarded recursive directory-walkers/
  validators -- `walk`, `copyDirRecursive`, `rmRecursive`, `listFilesRecursive`,
  `validateAgainstSchema`). `run-json-atomic.js` no longer appears anywhere in the results --
  confirmed fixed, not just fixed-in-isolation. **Zero false positives remain in this scan.**
- `C:/Dev/HarnessKit` (`hk/batch1-integration`, full repo): **9 findings**, unchanged from the
  original run (this branch's `run-json-atomic.js` never had the compound-condition shape to
  begin with -- its bound check is the simpler `if (Date.now() >= deadline) return` form, which
  was already correctly classified as bounded before this fix). Consistency check, not a new
  finding.

No new rules were added; both fixes widened/repaired existing AR001 logic and existing-frontend
process-spawn overhead respectively. No routing/enablement changes anywhere in this pass.
