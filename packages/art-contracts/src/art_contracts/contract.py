"""ART-0 vertical slice: the `at_most_once` behavioral contract.

Plain trace assertion, no DSL (per ART-0-plan.md section 4/8, batch 3: "no DSL yet"). Checked
against the REAL side-effect ledger a tool records when it actually executes -- not against what
the LLM/agent believes happened, and not against agent-chaos's mutated tool_result content (that
mutation only affects what the MODEL sees on its next turn; whether the real operation actually
ran twice is a separate, ground-truth question this contract answers).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ContractViolation(AssertionError):
    """Raised when a contract check fails. Subclasses AssertionError so pytest reports it as a
    normal assertion failure (readable message, no custom pytest machinery needed for AT5)."""

    def __init__(self, contract_name: str, tool_name: str, detail: str, call_index: int | None = None):
        self.contract_name = contract_name
        self.tool_name = tool_name
        self.detail = detail
        self.call_index = call_index
        message = f"[{contract_name}] violated by tool '{tool_name}': {detail}"
        if call_index is not None:
            message += f" (offending call index: {call_index})"
        super().__init__(message)


@dataclass
class ToolInvocation:
    """One REAL, ground-truth execution of a side-effecting tool -- recorded by the tool's own
    code, not derived from any LLM-visible trace."""

    tool_name: str
    args: dict[str, Any]
    call_index: int


@dataclass
class LedgerRecorder:
    """Real side-effect ledger a tool function appends to on every genuine execution. Shared,
    mutable, injected into sample agents -- this is the ground truth `at_most_once` checks."""

    invocations: list[ToolInvocation] = field(default_factory=list)

    def record(self, tool_name: str, args: dict[str, Any]) -> None:
        self.invocations.append(ToolInvocation(tool_name=tool_name, args=dict(args), call_index=len(self.invocations) + 1))

    def clear(self) -> None:
        self.invocations.clear()


class MissingKeyFieldError(ValueError):
    """Raised when a recorded invocation's args don't include one of the configured key_fields.
    Independent-review fix: this used to fall through silently -- `.get(f)` returned `None` for
    a missing field, so two DIFFERENT real invocations of a tool with no `request_id` (or whatever
    key_fields names) collapsed onto the identical key `(tool_name, (None,))` and were reported as
    a false-positive `at_most_once` violation. Reproduced directly by a reviewer with two distinct
    `send_email` calls carrying no `request_id` field at all. Fixed by failing loudly and
    immediately with a clear, actionable error instead of silently miscomparing on `None`."""


def check_at_most_once(ledger: LedgerRecorder, key_fields: tuple[str, ...] = ("request_id",)) -> None:
    """Raises ContractViolation if any tool was invoked more than once with an identical
    key_fields-derived identity. Passes silently (returns None) otherwise. Raises
    MissingKeyFieldError (not a silent None-collision) if a recorded invocation's args don't
    actually contain every field in key_fields.
    """
    seen: dict[tuple, ToolInvocation] = {}
    for inv in ledger.invocations:
        missing = [f for f in key_fields if f not in inv.args]
        if missing:
            raise MissingKeyFieldError(
                f"tool '{inv.tool_name}' invocation (call #{inv.call_index}) is missing "
                f"key_fields {missing} in its recorded args {inv.args!r} -- cannot check "
                f"at_most_once without a real identity key; refusing to guess via a None collision"
            )
        key = (inv.tool_name, tuple(inv.args[f] for f in key_fields))
        if key in seen:
            raise ContractViolation(
                contract_name="at_most_once",
                tool_name=inv.tool_name,
                detail=(
                    f"invoked more than once with identical {key_fields}={key[1]!r} "
                    f"(first at call #{seen[key].call_index}, again at call #{inv.call_index})"
                ),
                call_index=inv.call_index,
            )
        seen[key] = inv
