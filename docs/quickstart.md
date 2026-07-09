# Quickstart

```bash
pip install agent-lint
agent-lint scan .
```

That's it — no account, no API key, no network access. `agent-lint` parses your Python code
locally and never executes it.

## What you get today

At this stage (`EXECUTION.md` E04, on the way to the `v0.1.0` release), `agent-lint` ships one
rule: **AR001 — Agent loop has no maximum step count**. It looks for agentic loops (an
unconditional `while True:` that calls something, or a directly self-recursive function) with no
statically visible bound on how many times they can run.

```python
# agent.py
def run_agent(client):
    while True:
        client.step()
```

```console
$ agent-lint scan agent.py
[HIGH] AR001 agent.py:2
  Agent loop has no maximum step count
  evidence: while True: ... (no counter check + break/return found in the loop body)
  why: An agent loop with no visible step bound can run indefinitely: a model that never
  produces a stopping condition, a tool that never signals completion, or a bug in the loop's
  own exit logic will not be caught by anything in this code. In production this shows up as
  a hung process, runaway API cost, or an unbounded bill if the loop drives a paid external
  call.
  fix:  Add an explicit, checked upper bound on the number of iterations: a counter compared
  against a maximum with a break or return, a bounded range, or (for LangGraph) a
  recursion_limit passed at invocation.

1 finding.
```

Add the bound and the finding goes away:

```python
def run_agent(client, max_steps: int = 25):
    step_count = 0
    while True:
        client.step()
        step_count += 1
        if step_count >= max_steps:
            break
```

```console
$ agent-lint scan agent.py
No findings.
```

## Exit codes

`agent-lint scan` uses a stable, scriptable exit-code contract:

| Code | Meaning |
|---|---|
| 0 | Clean scan, no findings |
| 1 | Scan completed, at least one finding |
| 2 | Usage error (bad path or arguments) |
| 3 | Internal error (a bug in agent-lint itself) |
| 4 | Partial scan (a resource limit was hit; results may be incomplete) |

## What's next

More rules, JSON/SARIF output, LangGraph awareness, suppressions, and a GitHub Action are all
planned — see [`EXECUTION.md`](../EXECUTION.md) for the committed roadmap and
[`PLAN.md`](../PLAN.md) for the complete architecture. Rule catalog pages live alongside each
rule's implementation, e.g. [AR001](../packages/agent-lint/src/agent_reliability/lint/rules/ar001/docs.md).
