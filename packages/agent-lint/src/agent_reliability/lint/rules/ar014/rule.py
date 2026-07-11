"""AR014: Retry policy without an upper bound.

Follows the AR001 reference layout (see ``agent_reliability.lint.rules.ar001.rule``): this file
(logic + metadata), ``docs.md`` (catalog page), and fixtures + ``expected.json`` under
``fixtures/rules/AR014/`` at the repo root.

Detection: fires once per ``RetryPolicy`` in the micro-IR whose ``bound`` is
``RetryBound.UNBOUNDED`` -- the frontend's own UNBOUNDED classification *is* the detection
signal here (tenacity `stop=` omitted, stamina `attempts=None`, or a recognized
``while True:``/``while 1:`` manual retry loop with a `try`/`except`/`break` inside — see
``agent_reliability.lint.frontend.retries`` for the exact, honest rules it applies). This rule
does not re-derive or second-guess that classification; unlike AR003 it needs no allowlist of
its own, since ``RetryBound.UNBOUNDED`` already means "provably no upper bound" (see
``agent_reliability.core.model.ir.RetryBound``) rather than merely "unknown". A ``RetryBound.
UNKNOWN`` policy (e.g. a non-literal ``stop=`` value) never fires -- silence, not a guess, per
this repo's stated philosophy.

Side-effect classification (is the retried action safe to repeat?) is explicitly out of scope --
that is AR002/AR011/AR013 territory (deferred per `EXECUTION.md` E05's own non-goals).
"""

from __future__ import annotations

from collections.abc import Iterable

from agent_reliability.core.contracts import RuleContext, RuleMeta
from agent_reliability.core.model import (
    Category,
    Confidence,
    Finding,
    Severity,
    compute_fingerprint,
    derive_finding_id,
)
from agent_reliability.core.model.ir import RetryBound, RetryPolicy

# PLAN.md's rule catalog (section 14) records AR014 as high-severity/high-confidence: an
# UNBOUNDED retry construct is provably present in the source, not a guess.
META = RuleMeta(
    id="AR014",
    version=1,
    title="Retry policy without an upper bound",
    default_severity=Severity.HIGH,
    default_confidence=Confidence.HIGH,
    category=Category.RETRY_SAFETY,
)

WHY_IT_MATTERS = (
    "A retry construct with no upper bound will keep re-attempting a failing action forever if "
    "the failure is persistent (a downstream outage, a permanently invalid request, a revoked "
    "credential) rather than transient. In production this shows up as a stuck worker, a runaway "
    "bill on a paid external call, or a request that silently never completes and never surfaces "
    "as a failure anywhere."
)

REMEDIATION = (
    "Add an explicit, finite upper bound: `stop=stop_after_attempt(N)` for tenacity, a literal "
    "`attempts=N` for stamina, or a counted loop (`for _ in range(N):`) for a manual retry loop."
)


def _evidence_for(retry_policy: RetryPolicy) -> str:
    return f"retry policy ({retry_policy.source}) has no statically visible upper bound on attempts"


def _description_for(retry_policy: RetryPolicy) -> str:
    return (
        f"This retry policy ({retry_policy.source}) has no statically visible upper bound on "
        "the number of attempts."
    )


class AR014Rule:
    """See module docstring."""

    meta = META

    def evaluate(self, ctx: RuleContext) -> Iterable[Finding]:
        # Same occurrence_index disambiguation strategy as AR001 -- see that rule's evaluate().
        occurrence_counts: dict[str, int] = {}

        for retry_policy in ctx.retry_policies():
            if retry_policy.bound is not RetryBound.UNBOUNDED:
                continue

            occurrence_index = occurrence_counts.get(retry_policy.structural_hash, 0)
            occurrence_counts[retry_policy.structural_hash] = occurrence_index + 1

            fingerprint = compute_fingerprint(
                rule_id=self.meta.id,
                rule_major_version=self.meta.version,
                normalized_path=retry_policy.span.file,
                structural_hash=retry_policy.structural_hash,
                occurrence_index=occurrence_index,
            )

            yield Finding(
                rule_id=self.meta.id,
                rule_version=self.meta.version,
                title=self.meta.title,
                description=_description_for(retry_policy),
                severity=self.meta.default_severity,
                confidence=self.meta.default_confidence,
                category=self.meta.category,
                span=retry_policy.span,
                evidence=_evidence_for(retry_policy),
                why_it_matters=WHY_IT_MATTERS,
                remediation=REMEDIATION,
                fingerprint=fingerprint,
                finding_id=derive_finding_id(fingerprint),
            )


RULE = AR014Rule()
