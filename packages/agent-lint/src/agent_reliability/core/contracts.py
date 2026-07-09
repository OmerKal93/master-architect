"""The two permanent contracts: ``Rule``/``RuleContext`` and ``Frontend``.

Every future analyzer capability — every rule for the next fifteen AR-rules, every framework
(LangGraph, MCP, n8n), every plugin — implements one of these two protocols. Their shapes are
reviewed against the complete design in ``PLAN.md`` sections 12 and 13 before merge and are not
expected to change; what changes is how much of the IR a given rule or frontend chooses to use.

``RuleContext`` deliberately exposes no I/O capability at all: no filesystem access, no
subprocess, no network, no ``exec``/``eval``. This is a structural security property, not a
policy one — a ``Rule`` implementation *cannot* execute scanned code even if it wanted to,
because the API gives it nothing to execute with (see ``PLAN.md`` threat T26). A CI check that
greps rule modules for forbidden calls (``exec``, ``eval``, ``subprocess``, ``socket``, ...)
arrives in E05 once real rule modules exist to check.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from agent_reliability.core.model.config import Config
from agent_reliability.core.model.finding import Finding
from agent_reliability.core.model.ir import Agent, IRFragment, RetryPolicy, ToolCall
from agent_reliability.core.model.severity import Category, Confidence, Severity


@dataclass(frozen=True, slots=True)
class RuleMeta:
    """Static metadata about a rule, independent of any particular finding it produces."""

    id: str
    """e.g. ``"AR001"``."""
    version: int
    """Major version. Bumped only for behavior changes that should bust existing fingerprints
    (see ``agent_reliability.core.model.fingerprint``)."""
    title: str
    default_severity: Severity
    default_confidence: Confidence
    category: Category
    frameworks: tuple[str, ...] = ()
    """Empty means framework-agnostic/generic. Non-empty (e.g. ``("langgraph",)``) means the
    rule only makes sense when that framework was detected."""


@dataclass(frozen=True, slots=True)
class RuleContext:
    """A read-only view over one file's IR and the effective config, handed to a ``Rule``.

    Holds only data references and returns only read accessors — there is no method on this
    class that performs I/O of any kind.
    """

    _fragment: IRFragment
    _config: Config

    @property
    def file(self) -> str:
        return self._fragment.file

    @property
    def config(self) -> Config:
        return self._config

    def agents(self) -> Sequence[Agent]:
        return self._fragment.agents

    def tool_calls(self) -> Sequence[ToolCall]:
        return self._fragment.tool_calls

    def retry_policies(self) -> Sequence[RetryPolicy]:
        return self._fragment.retry_policies


@runtime_checkable
class Rule(Protocol):
    """Something that inspects a ``RuleContext`` and yields zero or more ``Finding``s.

    Implementations must not perform I/O (see module docstring) and must be deterministic: the
    same ``RuleContext`` must always yield the same findings.
    """

    meta: RuleMeta

    def evaluate(self, ctx: RuleContext) -> Iterable[Finding]: ...


@runtime_checkable
class Frontend(Protocol):
    """Turns one source file into an ``IRFragment``.

    Implementations must never import or execute the file's contents — only parse it (e.g. via
    ``ast.parse`` for Python) — and must respect the resource limits described in
    ``agent_reliability.lint.frontend`` (E03): bounded file size, bounded parse time, no
    following of symlinks outside the scan root.
    """

    name: str

    def supports(self, path: Path) -> bool: ...

    def lower(self, path: Path, *, root: Path) -> IRFragment: ...
