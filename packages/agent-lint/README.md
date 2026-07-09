# agent-lint

Local-first static analyzer for AI agent reliability and security anti-patterns — unbounded
agent loops, missing timeouts, unbounded retries, and (as the rule catalog grows) unsafe
retries around side effects, missing approval gates, and more.

```bash
pip install agent-lint
agent-lint scan .
```

Runs entirely offline: no account, no API key, no network access, `network: deny` by default.
Findings are deterministic (AST-based), not model-generated.

**Status:** early development. See the
[project root](https://github.com/OmerKal93/master-architect) for the full plan
(`PLAN.md`, `PLAN-PRS.md`, `EXECUTION.md`) and current progress.

Licensed under Apache-2.0.
