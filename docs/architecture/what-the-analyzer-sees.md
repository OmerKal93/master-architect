# What the analyzer sees (and doesn't)

This page is the honest capability statement for the Python frontend
(`agent_reliability.lint.frontend`, landed in E03 — see `EXECUTION.md`). It exists because
static analysis cannot achieve complete semantic understanding of a program, and the project's
stance (`PLAN.md` section 3.2, section 15) is to say so plainly rather than overclaim.

## What is guaranteed, always

- **Nothing is ever imported or executed.** The frontend parses source text with
  `ast.parse` and inspects the resulting syntax tree. It never runs the file, never imports it
  as a module, and never evaluates any expression in it — including expressions inside strings,
  f-strings, or `eval`/`exec` calls that the scanned code itself might contain (those are just
  more `Call` nodes to us, not instructions we follow).
- **Resource limits are enforced honestly.** Files over 2 MB, ASTs over 200,000 nodes, and
  per-file/whole-scan time budgets all produce a `scan-limit:`-prefixed diagnostic and a graceful
  skip — never a hang, never an unhandled exception, never a silent truncation presented as a
  complete scan.
- **Symlinks are never followed**, and every discovered path is verified to resolve strictly
  under the scan root before it is ever opened.

## Agent-loop recognition (`Agent`)

Recognized: an unconditional `while True:`/`while 1:` loop whose body contains at least one
call, or a function that directly calls itself by name whose body contains at least one call.

**Not recognized:** loops driven by a variable condition that happens to always be true at
runtime (`while running:` where `running` is never reassigned); mutual recursion (`f` calling
`g` calling `f`); recursion through an alias or higher-order function; any loop shape that
doesn't syntactically match `while True`/`while 1`. These produce *no* `Agent` entity at all —
not a false one with weaker confidence. Silence, not a guess, is the deliberate choice whenever
the heuristic can't tell.

**Step-bound evidence** (`has_step_bound`) is recognized only as an `if` comparing a name with
`>=`, `>`, or `==` whose body contains a `break` or `return` — the canonical
`if step_count >= MAX: break` shape. A bound expressed any other way (a `while` loop condition
itself carrying the bound, a bound enforced by an external framework parameter, a bound checked
via a helper function call) is not detected, and the loop is reported as `has_step_bound=False`
— which is the safer failure direction for a reliability tool than inventing a bound that isn't
really there.

## Tool-call recognition (`ToolCall`)

Recognized: any call whose target is an attribute chain (`obj.method(...)`,
`obj.attr.method(...)`). This intentionally is not yet a judgment about whether the call is
"really" an external tool call — that classification (against a known-SDK table or explicit
annotations) is a rule-level concern, not a frontend one, and arrives in a later PR.

**Not recognized:** bare-name calls (`len(...)`, `my_helper(...)`, or a callable imported
directly by name like `from openai import chat; chat(...)`). This is a stated trade-off to keep
the IR proportional to plausible tool-call sites; it is not a claim that no legitimate tool call
is ever missed this way.

**Timeout evidence** looks only for a keyword argument literally named `timeout`. A timeout
passed positionally, or under a differently-named parameter, is not detected.

## Retry-pattern recognition (`RetryPolicy`)

Recognized, each with an explicit `UNKNOWN` fallback when confidence is insufficient:

- **tenacity** `@retry(...)`/`@tenacity.retry(...)`: an omitted `stop=` is `UNBOUNDED`
  (tenacity's documented default is "never stop"); a literal `stop=stop_after_attempt(N)` is
  `BOUNDED(N)`; anything else assigned to `stop=` is `UNKNOWN`.
- **stamina** `@stamina.retry(...)`: a literal `attempts=N` is `BOUNDED(N)`; `attempts=None` is
  `UNBOUNDED`; an omitted `attempts=` is `UNKNOWN` — deliberately, since stamina's exact default
  has differed across versions and asserting one here with confidence would risk being wrong.
- **Manual loops**: `for _ in range(N):` (literal `N`) wrapping a `try`/`except` is `BOUNDED(N)`;
  `while True:`/`while 1:` wrapping a `try`/`except` with a `break` inside the `try` body is
  `UNBOUNDED`. More elaborate hand-rolled counters are not detected.

`@retry(...)` without any disambiguating keyword (neither tenacity's `stop`/`wait`/`reraise` nor
stamina's `attempts`/`timeout`) is not attributed to either library and produces no
`RetryPolicy` at all, since guessing which library is in play would be worse than silence.

## What this means for rules built on top

Rules (starting in E04) receive this IR as-is. A rule that fires because `has_step_bound is
False` is asserting "no step bound was *found*," not "no step bound *exists*" — that distinction
is exactly why the finding model carries a `Confidence` field, calibrated per rule, independent
of this frontend's own honesty about what it did and didn't look for.
