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

**Performance: a reused ``--serve`` worker, not one process per file.** A fresh Node process pays
for its own startup plus ``require('typescript')`` (a large module) every time -- measured at
~290ms/file, which dominates real parse time for typical files and was enough to make a
full-repo scan of real HarnessKit code hit the whole-scan wall-clock budget from spawn overhead
alone (see ``docs/ts-js-frontend-harnesskit-dogfood.md``, finding F6). ``_TsJsWorker`` amortizes
that cost by keeping ONE ``node parse_one_file.mjs --serve`` subprocess alive for the lifetime of
this ``TsJsFrontend`` instance and sending it one newline-delimited JSON request per file,
instead of spawning fresh each time. Detection logic is unchanged -- the server-mode script path
calls the exact same ``parseOne()`` function the single-shot path always used, so results are
identical either way; only the process-spawn overhead is amortized. If the worker is ever
unavailable (Node missing, script crashes, request times out, malformed response), ``lower()``
falls straight back to the original one-process-per-file ``subprocess.run()`` path below,
unchanged since before the worker existed -- that path's error handling (including the
``SCAN_LIMIT_PREFIX`` fixes from the earlier independent review) is the single source of truth
for every failure diagnostic; the worker never re-derives or duplicates that wording.
"""

from __future__ import annotations

import atexit
import contextlib
import json
import queue
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

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


def _span_from(span_dict: dict[str, Any], *, relative_path: str) -> SourceSpan:
    return SourceSpan(
        file=relative_path,
        start_line=span_dict["start_line"],
        start_col=span_dict["start_col"],
        end_line=span_dict["end_line"],
        end_col=span_dict["end_col"],
    )


def _agent_from(item: dict[str, Any], *, relative_path: str) -> Agent:
    return Agent(
        span=_span_from(item["span"], relative_path=relative_path),
        name=item["name"],
        has_step_bound=item["has_step_bound"],
        structural_hash=item["structural_hash"],
        step_bound_source=item["step_bound_source"],
    )


def _tool_call_from(item: dict[str, Any], *, relative_path: str) -> ToolCall:
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


def _retry_policy_from(item: dict[str, Any], *, relative_path: str) -> RetryPolicy:
    bound = RetryBound.UNBOUNDED if item["bound"] == "unbounded" else RetryBound.BOUNDED
    return RetryPolicy(
        span=_span_from(item["span"], relative_path=relative_path),
        bound=bound,
        source=item["source"],
        structural_hash=item["structural_hash"],
        max_attempts=item["max_attempts"],
    )


class _TsJsWorker:
    """Manages one persistent ``node parse_one_file.mjs --serve`` subprocess. See the
    "Performance" section of this module's docstring for why this exists.

    Every method fails soft: any problem starting, writing to, or reading from the worker
    returns ``None`` rather than raising, so ``TsJsFrontend.lower()`` can unconditionally fall
    back to the original per-file ``subprocess.run()`` path. This class never invents a
    diagnostic message of its own -- that stays the single-shot path's job.
    """

    def __init__(self, node_executable: str, script_path: Path, max_ast_nodes: int) -> None:
        self._node_executable = node_executable
        self._script_path = script_path
        self._max_ast_nodes = max_ast_nodes
        self._proc: subprocess.Popen[str] | None = None
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._next_id = 0
        self._atexit_registered = False

    def _ensure_started(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            return
        try:
            proc = subprocess.Popen(
                [
                    self._node_executable,
                    str(self._script_path),
                    "--serve",
                    str(self._max_ast_nodes),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
        except OSError:
            # Node not on PATH (or similarly unable to start) -- lower() falls back to
            # subprocess.run(), which reproduces the exact same failure and emits the real
            # SCAN_LIMIT_PREFIX diagnostic for it. This class stays silent about why.
            self._proc = None
            return

        self._proc = proc
        self._queue = queue.Queue()
        out_queue = self._queue

        def _read_lines() -> None:
            try:
                assert proc.stdout is not None
                for line in proc.stdout:
                    out_queue.put(line)
            except Exception:
                pass
            finally:
                # Sentinel: stdout closed (process exited or the pipe broke). Lets a blocked
                # request() return immediately instead of waiting out the full per-file timeout
                # for a worker that has already died.
                out_queue.put(None)

        threading.Thread(target=_read_lines, daemon=True).start()

        if not self._atexit_registered:
            # Registered once per worker instance, not once per respawn: self._terminate()
            # always operates on whatever self._proc currently is, so one registration is
            # enough to guarantee cleanup at interpreter exit no matter how many times the
            # underlying process gets respawned in between.
            atexit.register(self._terminate)
            self._atexit_registered = True

    def request(self, script_kind: str, source: str, *, timeout: float) -> dict[str, Any] | None:
        self._ensure_started()
        proc = self._proc
        if proc is None:
            return None

        self._next_id += 1
        req_id = self._next_id
        request = {"id": req_id, "script_kind": script_kind, "source": source}
        request_line = json.dumps(request) + "\n"
        try:
            assert proc.stdin is not None
            proc.stdin.write(request_line)
            proc.stdin.flush()
        except Exception:
            # Broken pipe, closed stdin, or any other platform-specific write failure -- the
            # worker is dead or dying either way.
            self._terminate()
            return None

        try:
            line = self._queue.get(timeout=timeout)
        except queue.Empty:
            # Hung or genuinely over budget -- can't distinguish, and don't need to: kill it
            # (mirrors subprocess.run(timeout=...)'s own TimeoutExpired semantics) and let the
            # caller fall back for this file; the next file gets a fresh worker.
            self._terminate()
            return None

        if line is None:
            # Worker's stdout closed without ever answering this request.
            self._terminate()
            return None

        try:
            result: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError:
            self._terminate()
            return None

        if result.get("id") != req_id:
            # Protocol desync should never happen given the strictly sequential request pattern
            # (one in-flight request at a time), but fail safe rather than return a mismatched
            # result silently.
            self._terminate()
            return None

        return result

    def _terminate(self) -> None:
        proc, self._proc = self._proc, None
        if proc is None:
            return
        with contextlib.suppress(Exception):
            if proc.stdin:
                proc.stdin.close()
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            with contextlib.suppress(Exception):
                proc.kill()


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
        self._worker: _TsJsWorker | None = None

    def supports(self, path: Path) -> bool:
        if path.name.endswith(".d.ts"):
            # Type-declaration files carry no executable logic (no loops, no calls, no retries)
            # -- scanning them would only ever produce empty IRFragments. Excluded explicitly
            # rather than silently producing zero findings for an unexplained reason.
            return False
        return path.suffix in (".ts", ".js")

    def lower(self, path: Path, *, root: Path) -> IRFragment:
        relative_path = path.relative_to(root).as_posix()

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

        result = self._parse_via_worker(path, source)
        if result is not None:
            return self._finish(result, relative_path=relative_path, start=start)

        # Worker unavailable or failed for this file (Node missing, crashed, timed out,
        # malformed response): fall back to the original one-process-per-file path, unchanged
        # since before the worker existed. Its error handling is the single source of truth for
        # every toolchain-failure diagnostic (including the SCAN_LIMIT_PREFIX fixes from the
        # earlier independent review) -- the worker never re-derives that wording.
        #
        # Caught by independent review: `start` must NOT be reused here. It was captured before
        # the worker attempt, which may itself have consumed real wall time (a timeout is the
        # documented case) before falling back -- reusing it would charge the fallback's own,
        # genuinely fast completion against a budget that already includes the failed worker
        # attempt's time, producing a spurious `SCAN_LIMIT_PREFIX` diagnostic on a file that
        # actually completed well within budget. `_lower_single_shot` captures its own fresh
        # `start` instead.
        return self._lower_single_shot(path, source, relative_path=relative_path)

    def _parse_via_worker(self, path: Path, source: str) -> dict[str, Any] | None:
        if self._worker is None:
            self._worker = _TsJsWorker(
                self._node_executable, self._script_path, self._limits.max_ast_nodes
            )
        return self._worker.request(
            _script_kind_for(path), source, timeout=self._limits.per_file_time_budget_seconds
        )

    def _lower_single_shot(self, path: Path, source: str, *, relative_path: str) -> IRFragment:
        # Fresh start time for this attempt only -- see the caller's comment in lower() for why
        # reusing a pre-worker-attempt timestamp here was a real, independent-review-caught bug.
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

        return self._finish(result, relative_path=relative_path, start=start)

    def _finish(self, result: dict[str, Any], *, relative_path: str, start: float) -> IRFragment:
        """Turns a ``parseOne()``-shaped result dict into an ``IRFragment``. Shared by both the
        worker path and the single-shot fallback path -- identical result shape either way, so
        this is the one place that ever builds the final IRFragment from it."""
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
                    Diagnostic(
                        level=DiagnosticLevel.WARNING, message=diag_message, file=relative_path
                    ),
                ),
            )

        diagnostics: list[Diagnostic] = []
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
        tool_calls = tuple(
            _tool_call_from(c, relative_path=relative_path) for c in result["tool_calls"]
        )
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
