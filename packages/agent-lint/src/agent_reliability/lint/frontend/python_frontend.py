"""``PythonFrontend``: the ``Frontend`` implementation for ``.py`` files.

Ties together safe parsing (``ast_utils.safe_parse``), resource limits (``limits.py``), and the
three micro-IR lowering passes (``loops``, ``calls``, ``retries``) into one per-file
``lower()`` call, matching the ``agent_reliability.core.contracts.Frontend`` protocol from E02.

Never imports, executes, or compiles-to-bytecode the scanned file — only reads its text and
parses it to a syntax tree.
"""

from __future__ import annotations

import time
from pathlib import Path

from agent_reliability.core.model.ir import Diagnostic, DiagnosticLevel, IRFragment
from agent_reliability.lint.frontend.ast_utils import exceeds_node_limit, safe_parse
from agent_reliability.lint.frontend.calls import detect_tool_calls
from agent_reliability.lint.frontend.limits import (
    DEFAULT_SCAN_LIMITS,
    SCAN_LIMIT_PREFIX,
    ScanLimits,
)
from agent_reliability.lint.frontend.loops import detect_agents
from agent_reliability.lint.frontend.retries import detect_retry_policies


class PythonFrontend:
    """Turns a Python source file into an ``IRFragment``. See module docstring."""

    name = "python"

    def __init__(self, *, limits: ScanLimits = DEFAULT_SCAN_LIMITS) -> None:
        self._limits = limits

    def supports(self, path: Path) -> bool:
        return path.suffix == ".py"

    def lower(self, path: Path, *, root: Path) -> IRFragment:
        relative_path = path.relative_to(root).as_posix()
        start = time.monotonic()
        diagnostics: list[Diagnostic] = []

        size_diagnostic = self._check_size(path, relative_path=relative_path)
        if size_diagnostic is not None:
            return IRFragment(file=relative_path, diagnostics=(size_diagnostic,))

        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return IRFragment(
                file=relative_path,
                diagnostics=(
                    Diagnostic(
                        level=DiagnosticLevel.WARNING,
                        message=f"could not read file ({type(exc).__name__}): file skipped",
                        file=relative_path,
                    ),
                ),
            )

        tree, parse_diagnostic = safe_parse(source, relative_path=relative_path)
        if tree is None:
            assert parse_diagnostic is not None
            return IRFragment(file=relative_path, diagnostics=(parse_diagnostic,))

        if exceeds_node_limit(tree, limit=self._limits.max_ast_nodes):
            return IRFragment(
                file=relative_path,
                diagnostics=(
                    Diagnostic(
                        level=DiagnosticLevel.WARNING,
                        message=(
                            f"{SCAN_LIMIT_PREFIX} exceeded max AST node count "
                            f"({self._limits.max_ast_nodes}); file skipped"
                        ),
                        file=relative_path,
                    ),
                ),
            )

        elapsed = time.monotonic() - start
        if elapsed > self._limits.per_file_time_budget_seconds:
            return IRFragment(
                file=relative_path,
                diagnostics=(
                    Diagnostic(
                        level=DiagnosticLevel.WARNING,
                        message=(
                            f"{SCAN_LIMIT_PREFIX} exceeded per-file time budget "
                            f"({self._limits.per_file_time_budget_seconds}s) during parsing; "
                            "file skipped"
                        ),
                        file=relative_path,
                    ),
                ),
            )

        agents = detect_agents(tree, relative_path=relative_path)
        tool_calls = detect_tool_calls(tree, relative_path=relative_path)
        retry_policies = detect_retry_policies(tree, relative_path=relative_path)

        elapsed = time.monotonic() - start
        if elapsed > self._limits.per_file_time_budget_seconds:
            diagnostics.append(
                Diagnostic(
                    level=DiagnosticLevel.WARNING,
                    message=(
                        f"{SCAN_LIMIT_PREFIX} exceeded per-file time budget "
                        f"({self._limits.per_file_time_budget_seconds}s) during lowering; "
                        "results may be incomplete"
                    ),
                    file=relative_path,
                )
            )

        return IRFragment(
            file=relative_path,
            agents=agents,
            tool_calls=tool_calls,
            retry_policies=retry_policies,
            diagnostics=tuple(diagnostics),
        )

    def _check_size(self, path: Path, *, relative_path: str) -> Diagnostic | None:
        try:
            size = path.stat().st_size
        except OSError as exc:
            return Diagnostic(
                level=DiagnosticLevel.WARNING,
                message=f"could not stat file ({type(exc).__name__}): file skipped",
                file=relative_path,
            )
        if size > self._limits.max_file_size_bytes:
            return Diagnostic(
                level=DiagnosticLevel.WARNING,
                message=(
                    f"{SCAN_LIMIT_PREFIX} file exceeds max size "
                    f"({self._limits.max_file_size_bytes} bytes); file skipped"
                ),
                file=relative_path,
            )
        return None
