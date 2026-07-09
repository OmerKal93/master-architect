"""The rule registry.

``ALL_RULES`` is the single source of truth for "every rule this build of agent-lint runs" —
consumed by the CLI/engine to evaluate every scanned file, and by the rule fixture harness
(``tools/art_rule_test.py``) to run the cross-rule false-positive net (every rule against every
fixture, not just its own). A new rule is added to this tuple in the same PR that adds its
module.
"""

from __future__ import annotations

from agent_reliability.core.contracts import Rule
from agent_reliability.lint.rules.ar001 import RULE as AR001_RULE

ALL_RULES: tuple[Rule, ...] = (AR001_RULE,)

__all__ = ["ALL_RULES"]
