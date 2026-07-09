"""Shared domain model and engine contracts.

- ``agent_reliability.core.model`` — findings, the micro-IR, and minimal config (E02).
- ``agent_reliability.core.contracts`` — the ``Rule``/``RuleContext`` and ``Frontend``
  protocols every analyzer capability implements (E02).

The full rule engine (dedupe, baselines, suppressions), the trace/audit store, and the Egress
Broker are not part of this package yet — see ``EXECUTION.md`` for what is deferred and why.
"""
