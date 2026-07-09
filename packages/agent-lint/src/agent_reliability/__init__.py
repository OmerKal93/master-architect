"""Agent Reliability Toolkit.

This distribution currently ships two subpackages:

- ``agent_reliability.core`` — shared domain model and engine contracts.
- ``agent_reliability.lint`` — the static analyzer and CLI.

The namespace is deliberately structured so that ``agent_reliability.core`` can later become its
own distribution (see ``docs/DECISIONS.md`` and ``PLAN.md`` section 37, "Package split") without
changing any import path.
"""

__version__ = "0.0.0.dev0"
