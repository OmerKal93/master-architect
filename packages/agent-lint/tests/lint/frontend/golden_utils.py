"""Test-only helpers for turning an ``IRFragment`` into a stable, comparable golden shape.

Deliberately omits line/column numbers: goldens should stay stable across minor fixture
whitespace edits and across OSes, mirroring the same "exclude positions" discipline the fp_v1
fingerprint algorithm uses (agent_reliability.core.model.fingerprint).
"""

from __future__ import annotations

from typing import Any

from agent_reliability.core.model.ir import IRFragment


def fragment_to_golden(fragment: IRFragment) -> dict[str, Any]:
    return {
        "agents": sorted(
            (
                {
                    "name": a.name,
                    "has_step_bound": a.has_step_bound,
                    "step_bound_source": a.step_bound_source,
                }
                for a in fragment.agents
            ),
            key=lambda d: (d["name"] or "", d["has_step_bound"]),
        ),
        "tool_calls": sorted(
            (
                {
                    "callee": c.callee,
                    "timeout_present": c.timeout.present if c.timeout else None,
                    "timeout_seconds": c.timeout.seconds if c.timeout else None,
                }
                for c in fragment.tool_calls
            ),
            key=lambda d: d["callee"],
        ),
        "retry_policies": sorted(
            (
                {
                    "bound": r.bound.value,
                    "source": r.source,
                    "max_attempts": r.max_attempts,
                }
                for r in fragment.retry_policies
            ),
            key=lambda d: (d["source"], d["bound"]),
        ),
        "diagnostic_count": len(fragment.diagnostics),
    }
