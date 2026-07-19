# art-contracts (ART-0 vertical slice)

Local-only spike implementing ART-0-plan.md's contracts-first vertical slice: one `at_most_once`
behavioral contract, checked against a LangGraph agent's real tool-call trace, under a
`timeout_after_commit` fault injected via `deepankarm/agent-chaos` (pinned, unmodified,
`agent-chaos==0.1.3`).

Not published. Not a general framework. See `docs/` in this package for the acceptance-test
evidence this slice produced.
