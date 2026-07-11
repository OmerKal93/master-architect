# AR014 — Retry policy without an upper bound

- **Severity:** high
- **Confidence:** high
- **Category:** retry-safety
- **Framework:** generic (Python)

## What it means

This finding fires on a retry construct — a `tenacity`/`stamina` decorator or a manual retry
loop — whose upper bound on the number of attempts could not just be determined, but was
**provably shown to be absent** (`RetryBound.UNBOUNDED`, distinct from `RetryBound.UNKNOWN` —
see below).

## Why it matters

A retry construct with no upper bound will keep re-attempting a failing action forever if the
failure is persistent (a downstream outage, a permanently invalid request, a revoked credential)
rather than transient. In production this shows up as a stuck worker, a runaway bill on a paid
external call, or a request that silently never completes and never surfaces as a failure
anywhere.

## What this rule looks for (and doesn't)

This rule trusts the frontend's `RetryPolicy.bound` classification exactly as produced (see
`agent_reliability.lint.frontend.retries` for the full, honest capability statement). In short:

- **Recognized as UNBOUNDED (fires):**
  - `@retry(...)` / `@tenacity.retry(...)` where the `stop=` keyword is omitted entirely, or
    explicitly set to the literal `None` — tenacity's documented default `stop` strategy is
    "never stop", and `stop=None` states that explicitly. The bare, qualified `@tenacity.retry`
    form (no parentheses) counts too — same all-defaults config.
  - `@stamina.retry(attempts=None)` — stamina's documented "retry forever" value.
  - A `while True:` / `while 1:` loop whose body contains a `try`/`except` with a `break` inside
    the `try` body (the "keep retrying until it succeeds" shape).
- **Recognized as BOUNDED (never fires):** `stop=stop_after_attempt(N)` with a literal `N` (bare
  or fully-qualified `tenacity.stop_after_attempt(N)`); `attempts=N` with a literal `N`; a
  `for _ in range(N):` loop (literal `N`) with a `try`/`except` in its body.
- **Recognized as UNKNOWN (never fires — silence, not a guess):** any `stop=`/`attempts=` value
  the frontend isn't confident interpreting (a variable, a composed strategy, a custom callable),
  and `attempts=` omitted entirely for stamina (its exact default has changed across versions, so
  no default is assumed).
- **Not detected at all (no `RetryPolicy` produced, so no finding either way):** a hand-rolled
  counter compared against a variable limit (`while attempts < max_attempts:`), mutual/indirect
  retry helpers, a bare **unqualified** `@retry` (no parens, no `tenacity.` prefix — could be
  stamina or an unrelated local decorator, no evidence to disambiguate), and any retry pattern
  outside the shapes above.
- **Named gap, not silently dropped:** a bare `max_retries=None` keyword is named in E05's
  required scope but is deliberately not detected. An earlier version of this rule matched it as
  `UNBOUNDED` unconditionally; independent review challenged that with real upstream source and
  was right to — `requests.adapters.HTTPAdapter(max_retries=None)` resolves to urllib3's
  *default* (bounded) retry policy, not "unlimited", and the OpenAI Python SDK rejects
  `max_retries=None` outright. Recognizing this pattern correctly would require knowing which
  specific library's `max_retries` is being set, which this frontend's dotted-name-only evidence
  cannot establish — so it stays undetected rather than asserting a claim that's false for the
  concrete libraries this scope names.

This rule does not classify whether the retried action is safe to repeat (idempotent vs. not) —
that is AR002/AR011/AR013 territory and explicitly out of scope for AR014.

## Remediation

Add an explicit, finite upper bound: `stop=stop_after_attempt(N)` for tenacity, a literal
`attempts=N` for stamina, or a counted loop (`for _ in range(N):`) for a manual retry loop.

```python
# Before
@retry(wait=wait_fixed(2))
def call_flaky_service():
    ...

# After
@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def call_flaky_service():
    ...
```

```python
# Before
while True:
    try:
        upload(path)
        break
    except IOError:
        continue

# After
for _ in range(5):
    try:
        upload(path)
        break
    except IOError:
        continue
```

## Suppressing this finding

Inline suppressions (`# art: ignore[AR014] reason="..."`) are not implemented yet — they land in
`EXECUTION.md` E07. Until then, the only way to silence a finding you've reviewed and accepted is
to add the bound the rule is looking for.
