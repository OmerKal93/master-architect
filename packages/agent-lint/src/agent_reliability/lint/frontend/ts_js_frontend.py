"""``TsJsFrontend``: the ``Frontend`` implementation for ``.ts``/``.js`` files.

Additive only -- ``PythonFrontend`` (and every ``.py`` behavior) is untouched by this module.
Matches the ``agent_reliability.core.contracts.Frontend`` protocol exactly, and reuses the same
language-neutral IR (``Agent``/``ToolCall``/``RetryPolicy``/``Diagnostic``/``IRFragment``) and the
same resource-limit conventions (``limits.py``) ``PythonFrontend`` already uses -- no parallel
model, no parallel scan-limit vocabulary.

Real, non-executing TypeScript AST parsing: this module never parses JS/TS itself in Python (no
such thing as a real TypeScript AST library in the Python ecosystem) -- it shells out, per file,
to ``tools/ts_frontend/parse_one_file.mjs``, a small Node script that uses the REAL, installed
``typescript`` npm package's ``ts.createSourceFile`` to build a syntax tree. ``createSourceFile``
only parses; it never runs, imports, or transpiles the scanned source to executable output --
the same "parse, never execute" contract ``ast_utils.py`` documents for Python's ``ast.parse``.

The subprocess is handed ONLY the source text (via stdin, after this module's own size check
already ran) -- it never opens the file itself, so every resource-limit decision Python already
makes for ``.py`` files (max file size, subprocess timeout as the per-file time budget, AST node
count) applies identically here, enforced from the Python side, with the subprocess itself as an
additional, stronger backstop (a real process kill on timeout, not just an elapsed-time check).
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from agent_reliability.core.model.ir import (
    Agent,
    Diagnostic,
    DiagnosticLevel,
    IRFragment,
    RetryBound,
    RetryPolicy,
    TimeoutPolicy,
    ToolCall,
)
from agent_reliability.core.model.span import SourceSpan
from agent_reliability.lint.frontend.limits import (
    DEFAULT_SCAN_LIMITS,
    SCAN_LIMIT_PREFIX,
    ScanLimits,
)

_SCRIPT_PATH = Path(__file__).resolve().parents[4] / "tools" / "ts_frontend" / "parse_one_file.mjs"


def _script_kind_for(path: Path) -> str:
    return "ts" if path.suffix == ".ts" else "js"


def _span_from(span_dict: dict, *, relative_path: str) -> SourceSpan:
    return SourceSpan(
        file=relative_path,
        start_line=span_dict["start_line"],
        start_col=span_dict["start_col"],
        end_line=span_dict["end_line"],
        end_col=span_dict["end_col"],
    )


def _agent_from(item: dict, *, relative_path: str) -> Agent:
    return Agent(
        span=_span_from(item["span"], relative_path=relative_path),
        name=item["name"],
        has_step_bound=item["has_step_bound"],
        structural_hash=item["structural_hash"],
        step_bound_source=item["step_bound_source"],
    )


def _tool_call_from(item: dict, *, relative_path: str) -> ToolCall:
    span = _span_from(item["span"], relative_path=relative_path)
    t = item["timeout"]
    return ToolCall(
        span=span,
        callee=item["callee"],
        structural_hash=item["structural_hash"],
        timeout=TimeoutPolicy(
            span=span,
            present=t["present"],
            seconds=t["seconds"],
            explicit_none=t["explicit_none"],
        ),
    )


def _retry_policy_from(item: dict, *, relative_path: str) -> RetryPolicy:
    bound = RetryBound.UNBOUNDED if item["bound"] == "unbounded" else RetryBound.BOUNDED
    return RetryPolicy(
        span=_span_from(item["span"], relative_path=relative_path),
        bound=bound,
        source=item["source"],
        structural_hash=item["structural_hash"],
        max_attempts=item["max_attempts"],
    )


class TsJsFrontend:
    """Turns a TypeScript/JavaScript source file into an ``IRFragment``. See module docstring."""

    name = "typescript_javascript"

    def __init__(
        self,
        *,
        limits: ScanLimits = DEFAULT_SCAN_LIMITS,
        node_executable: str = "node",
        script_path: Path = _SCRIPT_PATH,
    ) -> None:
        self._limits = limits
        self._node_executable = node_executable
        self._script_path = script_path

    def supports(self, path: Path) -> bool:
        if path.name.endswith(".d.ts"):
            # Type-declaration files carry no executable logic (no loops, no calls, no retries)
            # -- scanning them would only ever produce empty IRFragments. Excluded explicitly
            # rather than silently producing zero findings for an unexplained reason.
            return False
        return path.suffix in (".ts", ".js")

    def lower(self, path: Path, *, root: Path) -> IRFragment:
        relative_path = path.relative_to(root).as_posix()
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

        start = time.monotonic()
        try:
            proc = subprocess.run(
                [
                    self._node_executable,
                    str(self._script_path),
                    _script_kind_for(path),
                    str(self._limits.max_ast_nodes),
                ],
                input=source,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self._limits.per_file_time_budget_seconds,
                check=False,
            )
        except FileNotFoundError:
            # Toolchain unavailable, not an ordinary per-file parse error: results are just as
            # incomplete as any other scan-limit condition, so this must count toward exit 4
            # (EXIT_PARTIAL_SCAN) rather than silently reporting exit 0 ("clean scan") on a repo
            # full of unscanned, potentially-unsafe TS/JS files. Found via independent review.
            return IRFragment(
                file=relative_path,
                diagnostics=(
                    Diagnostic(
                        level=DiagnosticLevel.WARNING,
                        message=(
                            f"{SCAN_LIMIT_PREFIX} '{self._node_executable}' was not found on "
                            "PATH: TypeScript/JavaScript scanning requires Node.js; file skipped"
                        ),
                        file=relative_path,
                    ),
                ),
            )
        except subprocess.TimeoutExpired:
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

        if proc.returncode != 0 or not proc.stdout:
            # Same reasoning as the FileNotFoundError branch above: a crashed/missing parser
            # process (e.g. the `typescript` npm package not installed) is a scan-limit
            # condition, not an ordinary per-file parse error -- must drive exit 4, never exit 0.
            return IRFragment(
                file=relative_path,
                diagnostics=(
                    Diagnostic(
                        level=DiagnosticLevel.WARNING,
                        message=(
                            f"{SCAN_LIMIT_PREFIX} TypeScript/JavaScript parser process failed "
                            f"(exit {proc.returncode}): "
                            f"{(proc.stderr or '').strip()[:300] or 'no output'}"
                        ),
                        file=relative_path,
                    ),
                ),
            )

        try:
            result = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            return IRFragment(
                file=relative_path,
                diagnostics=(
                    Diagnostic(
                        level=DiagnosticLevel.WARNING,
                        message=(
                            f"{SCAN_LIMIT_PREFIX} TypeScript/JavaScript parser returned "
                            f"malformed JSON: {exc}"
                        ),
                        file=relative_path,
                    ),
                ),
            )

        if not result.get("ok"):
            error_kind = result.get("error_kind", "unknown_error")
            message = result.get("message", "")
            line = result.get("line")
            location = f" (line {line})" if line is not None else ""
            if error_kind == "node_limit_exceeded":
                diag_message = f"{SCAN_LIMIT_PREFIX} {message}: file skipped"
            else:
                diag_message = f"could not parse as TypeScript/JavaScript: {message}{location}"
            return IRFragment(
                file=relative_path,
                diagnostics=(
                    Diagnostic(level=DiagnosticLevel.WARNING, message=diag_message, file=relative_path),
                ),
            )

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

        agents = tuple(_agent_from(a, relative_path=relative_path) for a in result["agents"])
        tool_calls = tuple(_tool_call_from(c, relative_path=relative_path) for c in result["tool_calls"])
        retry_policies = tuple(
            _retry_policy_from(r, relative_path=relative_path) for r in result["retry_policies"]
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
