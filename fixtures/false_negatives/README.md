# False-negative regression corpus

This directory is empty by design — it is where real-world missed bugs go once they've been
reported and reproduced. It exists from day one (`EXECUTION.md` E04) so the pipeline is ready
before the first report arrives, not bolted on afterward.

## The pipeline (`PLAN.md` section 38.10)

1. A user reports that agent-lint missed something (or flagged something incorrectly — see
   `fixtures/rules/*/` for the false-positive side of this, covered by each rule's own `safe/`
   and `edge/` fixtures).
2. A maintainer or the reporter reproduces it.
3. The reproduction is sanitized: real secrets and proprietary logic stripped, reduced to the
   smallest shape that still reproduces the miss.
4. It's added here as `<RULE_ID_or_area>/<short-description>/` with the minimal reproduction
   and a short `README.md` explaining what was missed and why.
5. A failing regression test is added first (it should fail against the current rule/frontend
   behavior).
6. The fix lands, turning the test green.
7. The fixture stays here permanently — it is never deleted, only superseded.
8. The reporter is credited in `CHANGELOG.md` when they permit it.

## What goes here versus `fixtures/rules/<RULE_ID>/`

`fixtures/rules/<RULE_ID>/{unsafe,safe,edge}/` are the rule author's own designed test cases,
written before or alongside the rule. This directory is for cases nobody designed for —
real-world code that exposed a gap. Once a false-negative fixture here starts passing (the fix
landed), it is usually *also* promoted into the owning rule's `edge/` fixtures so the harness in
`tools/art_rule_test.py` keeps enforcing it as part of the rule's normal contract; the copy here
stays as the permanent historical record of the original report.
