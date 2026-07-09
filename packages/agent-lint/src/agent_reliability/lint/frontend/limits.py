"""Resource limits that bound what one scan can be made to do.

These exist because the analyzer must remain safe to run on a repository it does not trust
(PLAN.md threats T2 "malicious Python syntax / pathological code" and T25 "DoS via huge
repos/graphs"). Every limit here produces a ``Diagnostic`` and a graceful skip — never an
unhandled exception, and never an unbounded hang.

Honest limitation (documented, not hidden): the per-file time budget is enforced *between*
processing steps (after parse, after node counting, before lowering), not by preemptively
interrupting a single call such as ``ast.parse`` itself. CPython's PEG parser is near-linear for
syntactically valid input, and the file-size cap bounds how much input it ever sees, so this is
judged sufficient without adding subprocess-per-file isolation (a heavier mechanism deferred
until evidence shows it's needed).
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB, per PLAN.md section 14
DEFAULT_MAX_AST_NODES = 200_000
DEFAULT_PER_FILE_TIME_BUDGET_SECONDS = 5.0
DEFAULT_WALL_CLOCK_BUDGET_SECONDS = 60.0

# Directory names never descended into, regardless of .gitignore or config. Keeps discovery
# from wasting the resource budget on VCS internals, caches, and dependency trees.
DEFAULT_EXCLUDED_DIR_NAMES = frozenset(
    {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".art",
    }
)


@dataclass(frozen=True, slots=True)
class ScanLimits:
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES
    max_ast_nodes: int = DEFAULT_MAX_AST_NODES
    per_file_time_budget_seconds: float = DEFAULT_PER_FILE_TIME_BUDGET_SECONDS
    wall_clock_budget_seconds: float = DEFAULT_WALL_CLOCK_BUDGET_SECONDS


DEFAULT_SCAN_LIMITS = ScanLimits()

# Message prefix convention for diagnostics that represent a resource limit being hit, as
# opposed to an ordinary parse error or config warning. The CLI (E04) maps the presence of any
# such diagnostic to exit code 4 ("partial scan") by checking for this prefix — a lightweight,
# additive convention rather than a new core-model field, until real usage shows a field is
# warranted.
SCAN_LIMIT_PREFIX = "scan-limit:"
