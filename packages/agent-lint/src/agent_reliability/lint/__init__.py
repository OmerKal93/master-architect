"""The static analyzer and CLI.

- ``agent_reliability.lint.frontend`` — the safe Python frontend (E03): discovery, resource
  limits, and micro-IR lowering.
- ``agent_reliability.lint.rules`` — the rule registry, starting with AR001 (E04).
- ``agent_reliability.lint.engine`` — ties the frontend scan and rule evaluation together.
- ``agent_reliability.lint.cli`` — the ``agent-lint`` command.

JSON/SARIF output, ``explain``, and suppressions land in later E-PRs. See ``EXECUTION.md``.
"""
