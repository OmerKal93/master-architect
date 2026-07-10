# Contributing to the Agent Reliability Toolkit

Thanks for your interest. This project is early — see `README.md` for the two-layer plan and
`EXECUTION.md` for what is actually being built right now. This guide covers what exists today.

## Contributor onboarding (should take under 30 minutes)

```bash
git clone https://github.com/OmerKal93/agent-reliability-toolkit.git
cd agent-reliability-toolkit/packages/agent-lint
uv sync                      # installs the package + dev dependencies
uv run pytest                # should be green with zero network access
uv run agent-lint scan fixtures/rules/AR001/unsafe   # once AR001 exists (E04+)
```

If any step above fails on a clean clone, that's a bug — please open an issue.

## Ways to contribute right now

The contribution surface widens as the project progresses (see `EXECUTION.md`, each E-PR names
what opens after it). Early on, the most valuable and best-reviewed contributions are:

- **Fixtures** — safe-control examples, edge cases, or hostile/malformed input samples under
  `fixtures/`. See "Contributing a failure fixture" below.
- **Documentation** — rule pages, clarifications, typo fixes.
- **Bug reports** — including false positives on rules, using the issue templates once they
  exist (`EXECUTION.md` E12).

Rule contributions open once the rule-module pattern and fixture harness exist (E04 onward) —
see "Adding a rule" below, which will be kept current as the harness lands.

## Adding a rule

A rule lives in one directory and consists of:

1. `rule.py` — the rule logic and metadata (id, title, severity, confidence, categories).
2. `docs.md` — the rule's catalog page and the content shown by `agent-lint explain <ID>`.
3. `fixtures/` — at minimum: one true-positive case, one safe control (code that must **not**
   trigger the rule), and one edge case.
4. `expected.json` — the exact expected finding output for the fixtures above.

The `art-rule-test` harness runs every rule against every fixture in the repository and fails
the build if any rule fires on any safe control anywhere (not just its own fixtures) — this is
what keeps false positives from creeping in as rules accumulate. Because the `RuleContext` API a
rule receives has no I/O capability by construction, rule PRs do not require security-team
review — any maintainer can approve one that passes the harness.

## Contributing a failure fixture

If agent-lint missed a real bug, or a framework pattern we don't recognize broke your scan,
please share (via issue or PR) a **sanitized** reproduction: simplified code with the same
shape as the real failure, no real secrets or proprietary logic, plus the tool/framework
versions involved and what you expected to happen. These become permanent regression fixtures
credited to you (unless you'd rather stay anonymous).

## Review boundaries

Two tiers, so you know what to expect:

- **Maintainer-gated** (higher bar, may take longer): the parser/frontend safety guarantees,
  the finding/fingerprint model, redaction, the CLI's network posture, and anything touching how
  scanned code is handled. These are the security-critical seams described in `PLAN.md`'s threat
  model.
- **Open path** (any maintainer can approve): rules, fixtures, documentation, examples.

## Development

- Python 3.10–3.13, managed with [`uv`](https://docs.astral.sh/uv/).
- `ruff` for linting/formatting, `mypy` for type checking, `pytest` for tests — all run in CI on
  Linux, macOS, and Windows.
- We use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages where
  practical, though this isn't yet enforced by tooling.
- Sign off your commits per the [Developer Certificate of Origin](https://developercertificate.org/)
  (`git commit -s`) — this is how we track that contributions can be included under Apache-2.0
  without a separate CLA.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).

## Security issues

Do not file regular issues for security vulnerabilities — see `SECURITY.md`.
