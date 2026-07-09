# AR001 — Agent loop has no maximum step count

- **Severity:** high
- **Confidence:** high
- **Category:** loop-safety
- **Framework:** generic (Python)

## What it means

This finding fires on an agentic loop — an unconditional `while True:`/`while 1:` loop that
calls something, or a function that calls itself directly — where no statically visible upper
bound on the number of iterations was found.

## Why it matters

An agent loop with no visible step bound can run indefinitely: a model that never produces a
stopping condition, a tool that never signals completion, or a bug in the loop's own exit logic
will not be caught by anything in this code. In production this shows up as a hung process,
runaway API cost, or an unbounded bill if the loop drives a paid external call.

## What this rule looks for (and doesn't)

See [`docs/architecture/what-the-analyzer-sees.md`](../../../../../../docs/architecture/what-the-analyzer-sees.md)
for the full, honest capability statement. In short:

- **Recognized as an agent loop:** an unconditional `while True:`/`while 1:` loop containing at
  least one call, or a function that calls itself directly and contains at least one call.
- **Recognized as a step bound:** an `if` comparing a value with `>=`, `>`, or `==` whose body
  contains a `break` or `return` — the `if step_count >= MAX_STEPS: break` shape.
- **Not recognized:** loops driven by a variable condition, mutual recursion, indirect
  recursion through an alias, or a bound expressed any other way. These produce no finding —
  silence, not a false positive and not a guess.

Because the recognition heuristic is intentionally broad (any unconditional loop that calls
something), this rule will fire on non-agent code too (e.g. a generic polling loop). That is an
accepted trade-off, not a bug: narrowing the heuristic to specific "agent-sounding" call names
would risk missing real agent loops that don't happen to match a keyword list.

## Remediation

Add an explicit, checked upper bound on the number of iterations: a counter compared against a
maximum with a break or return, a bounded range, or (for LangGraph, once framework-aware rules
land) a `recursion_limit` passed at invocation.

```python
# Before
def run_agent(client):
    while True:
        client.step()

# After
def run_agent(client, max_steps: int = 25):
    for _ in range(max_steps):
        client.step()

# Or, with an explicit counter:
def run_agent(client, max_steps: int = 25):
    step_count = 0
    while True:
        client.step()
        step_count += 1
        if step_count >= max_steps:
            break
```

## Suppressing this finding

Inline suppressions (`# art: ignore[AR001] reason="..."`) are not implemented yet — they land in
`EXECUTION.md` E07. Until then, the only way to silence a finding you've reviewed and accepted is
to add the bound the rule is looking for.
