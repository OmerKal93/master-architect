"""Safe AST parsing and the Python-specific structural hash used by ``fp_v1`` fingerprints.

``safe_parse`` never lets a malformed or pathological file crash the scan: every failure mode
(syntax errors, encoding errors, and the recursion/memory errors that sufficiently adversarial
nesting can trigger even in CPython's PEG parser) is caught and converted into a ``Diagnostic``.
Nothing here ever compiles or executes the parsed tree — ``ast.parse`` with the default mode
only builds a syntax tree; it does not run the code (PLAN.md threat T1).
"""

from __future__ import annotations

import ast
import hashlib

from agent_reliability.core.model.ir import Diagnostic, DiagnosticLevel
from agent_reliability.core.model.span import SourceSpan
from agent_reliability.lint.frontend.limits import SCAN_LIMIT_PREFIX

_NESTING_LIMIT_SYNTAXERROR_MARKERS = ("too many nested", "too many statically nested")


def safe_parse(source: str, *, relative_path: str) -> tuple[ast.Module | None, Diagnostic | None]:
    """Parse ``source`` as Python, never raising.

    Returns ``(tree, None)`` on success, or ``(None, diagnostic)`` if parsing failed for any
    reason. The tree is never executed, imported, or compiled to bytecode — only built.
    """
    try:
        tree = ast.parse(source, filename=relative_path)
    except SyntaxError as exc:
        message = exc.msg or ""
        # CPython's own parser rejects sufficiently deep nesting (e.g. "too many nested
        # parentheses") as a SyntaxError before our RecursionError/MemoryError guard below ever
        # gets a chance to fire. This is still a resource-limit rejection, not an ordinary typo
        # — categorize it the same way for a consistent scan-limit diagnostic.
        if any(marker in message for marker in _NESTING_LIMIT_SYNTAXERROR_MARKERS):
            return None, Diagnostic(
                level=DiagnosticLevel.WARNING,
                message=f"{SCAN_LIMIT_PREFIX} {message} (line {exc.lineno}): file skipped",
                file=relative_path,
            )
        return None, Diagnostic(
            level=DiagnosticLevel.WARNING,
            message=f"could not parse as Python: {message} (line {exc.lineno})",
            file=relative_path,
        )
    except (ValueError, RecursionError, MemoryError) as exc:
        # RecursionError/MemoryError are the pathological-input cases (T2): deeply nested
        # expressions or huge literals. ValueError covers null bytes and similar malformed
        # source that the tokenizer rejects outright.
        return None, Diagnostic(
            level=DiagnosticLevel.WARNING,
            message=f"{SCAN_LIMIT_PREFIX} could not parse ({type(exc).__name__}): file skipped",
            file=relative_path,
        )
    return tree, None


def exceeds_node_limit(tree: ast.AST, *, limit: int) -> bool:
    """True if ``tree`` has more than ``limit`` nodes.

    Uses ``ast.walk`` (an iterative, deque-based traversal — never recursive, so it cannot
    itself stack-overflow on a wide-but-shallow pathological tree) and exits as soon as the
    limit is crossed rather than always counting every node in a huge tree.
    """
    return any(count > limit for count, _ in enumerate(ast.walk(tree), start=1))


def structural_hash(node: ast.AST) -> str:
    """Hash the *shape* of ``node``, excluding source positions.

    This is the Python-specific implementation of the structural hash that
    ``agent_reliability.core.model.fingerprint.compute_fingerprint`` requires: two occurrences
    of the same code shape (identical node types, names, and literal values) hash identically
    regardless of which line they're on, which is what lets fingerprints survive reformatting.
    ``include_attributes=False`` is what excludes line/column information from ``ast.dump``.
    """
    dumped = ast.dump(node, annotate_fields=True, include_attributes=False)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def span_of(node: ast.AST, *, relative_path: str) -> SourceSpan:
    """Build a ``SourceSpan`` from an AST node's position attributes.

    ``end_lineno``/``end_col_offset`` are present on every node produced by ``ast.parse`` since
    Python 3.8; a defensive fallback to the start position keeps this total even for the rare
    node types that lack them (e.g. some synthetically-constructed nodes, which don't occur in
    output from ``ast.parse`` but this keeps the function honest about its assumptions).
    """
    start_line = getattr(node, "lineno", 1)
    start_col = getattr(node, "col_offset", 0)
    end_line = getattr(node, "end_lineno", None) or start_line
    end_col = getattr(node, "end_col_offset", None)
    if end_col is None:
        end_col = start_col
    return SourceSpan(
        file=relative_path,
        start_line=start_line,
        start_col=start_col,
        end_line=end_line,
        end_col=end_col,
    )


def dotted_name(node: ast.expr) -> str | None:
    """Best-effort rendering of a call target as a dotted name, e.g. ``"requests.post"``.

    Returns ``None`` for callees that aren't a simple name/attribute chain (e.g. the result of
    another call, a subscript, a lambda) — those are not given a stable name, which is the
    honest answer rather than a guess.
    """
    parts: list[str] = []
    current: ast.expr = node
    while True:
        if isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        elif isinstance(current, ast.Name):
            parts.append(current.id)
            break
        else:
            return None
    return ".".join(reversed(parts))
