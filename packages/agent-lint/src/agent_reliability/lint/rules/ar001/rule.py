"""AR001: Agent loop has no maximum step count.

The first rule (`EXECUTION.md` E04) and the reference implementation every later rule's
module layout follows: this file (the logic + metadata), `docs.md` (the catalog page and
`agent-lint explain AR001` content, added in E07), and fixtures + `expected.json` under
`fixtures/rules/AR001/` at the repo root (the shared, security-sensitive fixture library — see
`PLAN.md` section 10).

Detection: fires once per `Agent` entity in the micro-IR (an unconditional `while True:`/
`while 1:` loop containing a call, or a directly self-recursive function) that has
``has_step_bound is False``. See ``docs/architecture/what-the-analyzer-sees.md`` for exactly
what counts as a step bound and the honest limits of this heuristic — this rule trusts the
frontend's evidence as-is and does not re-derive it.
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
from agent_reliability.core.model.ir import Agent

META = RuleMeta(
    id="AR001",
    version=1,
    title="Agent loop has no maximum step count",
    default_severity=Severity.HIGH,
    default_confidence=Confidence.HIGH,
    category=Category.LOOP_SAFETY,
)

WHY_IT_MATTERS = (
    "An agent loop with no visible step bound can run indefinitely: a model that never "
    "produces a stopping condition, a tool that never signals completion, or a bug in the "
    "loop's own exit logic will not be caught by anything in this code. In production this "
    "shows up as a hung process, runaway API cost, or an unbounded bill if the loop drives a "
    "paid external call."
)

REMEDIATION = (
    "Add an explicit, checked upper bound on the number of iterations: a counter compared "
    "against a maximum with a break or return, a bounded range, or (for LangGraph) a "
    "recursion_limit passed at invocation."
)


def _evidence_for(agent: Agent) -> str:
    # TS/JS parity fix (E-ts01): this text used to hardcode Python's `def` keyword
    # (f"def {agent.name}(...): ...") and the literal Python spelling `while True:` --
    # factually wrong when the underlying Agent came from a JS/TS file (whose source never says
    # `def`), found during real dogfooding of this frontend against HarnessKit's own JS code.
    # Language-neutral phrasing now, since Agent itself is a language-neutral IR entity.
    if agent.name:
        return f"{agent.name}(...) calls itself with no visible depth/counter guard"
    return "unconditional loop (no counter check + break/return found in the loop body)"


def _description_for(agent: Agent) -> str:
    name_part = f" ({agent.name})" if agent.name else ""
    return f"This agent loop{name_part} has no statically visible maximum step count."


class AR001Rule:
    """See module docstring."""

    meta = META

    def evaluate(self, ctx: RuleContext) -> Iterable[Finding]:
        # Disambiguates multiple structurally-identical unbounded loops in the same file (e.g.
        # the same unsafe pattern copy-pasted twice) per the fp_v1 occurrence_index contract —
        # see agent_reliability.core.model.fingerprint.
        occurrence_counts: dict[str, int] = {}

        for agent in ctx.agents():
            if agent.has_step_bound:
                continue

            occurrence_index = occurrence_counts.get(agent.structural_hash, 0)
            occurrence_counts[agent.structural_hash] = occurrence_index + 1

            fingerprint = compute_fingerprint(
                rule_id=self.meta.id,
                rule_major_version=self.meta.version,
                normalized_path=agent.span.file,
                structural_hash=agent.structural_hash,
                occurrence_index=occurrence_index,
            )

            yield Finding(
                rule_id=self.meta.id,
                rule_version=self.meta.version,
                title=self.meta.title,
                description=_description_for(agent),
                severity=self.meta.default_severity,
                confidence=self.meta.default_confidence,
                category=self.meta.category,
                span=agent.span,
                evidence=_evidence_for(agent),
                why_it_matters=WHY_IT_MATTERS,
                remediation=REMEDIATION,
                fingerprint=fingerprint,
                finding_id=derive_finding_id(fingerprint),
            )


RULE = AR001Rule()
