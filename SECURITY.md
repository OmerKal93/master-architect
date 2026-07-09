# Security Policy

The Agent Reliability Toolkit analyzes source code and, once ReplaySafe/agent-chaos/
agent-contract open, executes user-provided test/runtime configuration. Security issues in this
project can mean scanned code being executed, secrets leaking into output, or a sandbox boundary
being crossed. We take reports seriously.

## Supported versions

Pre-1.0: only the latest released minor version receives security fixes. There is no long-term
support branch yet — see `PLAN.md` §28 for the post-1.0 policy.

## Reporting a vulnerability

**Do not open a public issue for security reports.** Instead, use
[GitHub Security Advisories](../../security/advisories/new) on this repository ("Report a
vulnerability"), which opens a private disclosure channel with maintainers. This is the primary
and currently the only supported reporting channel; a dedicated security-contact email address
will be published here before the public launch (`EXECUTION.md` E12) if one is set up.

Please include:

- The affected version(s) and component (e.g. `agent-lint` frontend, CLI, CI Action).
- A minimal reproduction (a fixture-style example is ideal — see `CONTRIBUTING.md`).
- The impact you believe it has (e.g. arbitrary code execution during scan, secret leakage,
  sandbox escape, denial of service).

## Response process

We follow a **coordinated disclosure** model with a target of acknowledging reports within
5 business days and a 90-day disclosure window from acknowledgment, extendable by mutual
agreement if a fix needs more time. Confirmed vulnerabilities are fixed on a private branch,
released as a patch, and disclosed via a GitHub Security Advisory crediting the reporter
(unless they prefer to remain anonymous).

## What is in scope

- The scanner executing or importing scanned source code (it must never do either — this is a
  core invariant, see `PLAN.md` §3.5 and the threat model in `PLAN.md` §25).
- Secrets or source code leaking into findings, logs, reports, or CI artifacts.
- Path traversal, symlink escapes, or resource exhaustion via crafted input repositories.
- Any network call made outside the documented offline-by-default behavior.
- Supply-chain issues in this repository's own CI/release pipeline.

## What is explicitly out of scope (for now)

Findings about the *target* code a user chooses to scan (that's the product's job, not a
vulnerability in the toolkit) and issues in components that don't exist yet — see
`EXECUTION.md` and `PLAN.md` §37 for what is currently implemented versus planned.
