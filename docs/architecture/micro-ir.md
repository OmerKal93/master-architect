# The micro-IR, and how it grows into the full IR

`agent_reliability.core.model.ir` currently defines four entities: `Agent`, `RetryPolicy`,
`ToolCall`, and `TimeoutPolicy`, plus the plumbing (`IRFragment`, `Diagnostic`) that carries them
out of a `Frontend`. This is deliberately small. It is **not** a simplified stand-in for a
"real" IR that will replace it later — it is the first, smallest instantiation of the complete
intermediate representation described in [`PLAN.md` section 11](../../PLAN.md#11-domain-model),
which additionally specifies `Workflow`, `Node`, `Edge`, `Tool`, `SideEffect`, `ApprovalGate`,
`Checkpoint`, and `RiskClassification`.

## The growth rule

**A new IR type is added only when a real rule needs it.** There is no speculative type
inventory sitting unused in this codebase. Each addition traces to a specific `EXECUTION.md`
E-PR:

| Type | Added in | Needed for |
|---|---|---|
| `Agent`, `RetryPolicy`, `ToolCall`, `TimeoutPolicy` | E02 | AR001, AR003, AR014 |
| `Workflow`, `Node`, `Edge`, `ApprovalGate`, `Checkpoint` | E08 | LangGraph recognition |
| `SideEffect`, `RiskClassification` | E09 | LG002/LG003/LG006, and later AR002/AR004/AR005 |
| Everything else in `PLAN.md` section 11 | gated (see `PLAN.md` section 37) | whichever component's validation gate opens it |

## Why this doesn't create rework

Every field name and shape already matches the full design in `PLAN.md` section 11 — this PR
(E02) doesn't invent a different, smaller vocabulary that later gets translated into the "real"
one. Growth is purely additive:

- New dataclasses are added to `ir.py` (or a new module, for a large enough addition like
  LangGraph's `Workflow`/`Node`/`Edge` family) without touching existing ones.
- `IRFragment` gains new optional tuple fields with empty-tuple defaults, so existing frontends
  and rules that don't populate them keep working unchanged.
- `RuleContext` (in `agent_reliability.core.contracts`) gains new read accessors the same way.

`UNKNOWN`-shaped values (see `RetryBound.UNKNOWN` vs `RetryBound.UNBOUNDED`) are part of this
discipline too: when a future IR type needs the same "we don't know" vs "we know it's absent"
distinction, it follows the same pattern rather than inventing a new one.
