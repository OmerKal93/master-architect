"""``scan_repository``: ties discovery and per-file lowering together for a whole scan.

Introduces no new data model types (E03 is explicitly scoped to "no new data models") — the
one thing this module needs that ``IRFragment`` doesn't naturally provide, a place for
scan-wide diagnostics not tied to any single processed file (a discovery-level symlink skip, or
"the whole-scan time budget was exceeded"), is represented as an ``IRFragment`` with
``file=""``. This convention is used nowhere else and is documented here as the one place it
means "not any particular file — this is scan-level."
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from pathlib import Path

from agent_reliability.core.contracts import Frontend
from agent_reliability.core.model.config import Config, default_config
from agent_reliability.core.model.ir import Diagnostic, DiagnosticLevel, IRFragment
from agent_reliability.lint.frontend.discovery import discover_files
from agent_reliability.lint.frontend.limits import (
    DEFAULT_SCAN_LIMITS,
    SCAN_LIMIT_PREFIX,
    ScanLimits,
)
from agent_reliability.lint.frontend.python_frontend import PythonFrontend

SCAN_LEVEL_FILE = ""
"""The ``IRFragment.file`` sentinel used for diagnostics not tied to any single scanned file."""


def scan_repository(
    root: Path,
    *,
    config: Config | None = None,
    limits: ScanLimits = DEFAULT_SCAN_LIMITS,
    frontends: Sequence[Frontend] | None = None,
) -> tuple[IRFragment, ...]:
    """Discover and lower every supported file under ``root``.

    Enforces the whole-scan wall-clock budget: once exceeded, remaining undiscovered/unlowered
    files are skipped and a single scan-level diagnostic (``file=""``) records the truncation —
    a partial scan is always reported honestly, never silently presented as complete.
    """
    effective_config = config if config is not None else default_config()
    effective_frontends: Sequence[Frontend] = (
        frontends if frontends is not None else [PythonFrontend(limits=limits)]
    )

    scan_level_diagnostics: list[Diagnostic] = []
    fragments: list[IRFragment] = []

    start = time.monotonic()
    truncated = False

    discovered_files = discover_files(
        root, config=effective_config, diagnostics=scan_level_diagnostics
    )
    for discovered in discovered_files:
        if time.monotonic() - start > limits.wall_clock_budget_seconds:
            truncated = True
            break

        frontend = next(
            (fe for fe in effective_frontends if fe.supports(discovered.absolute_path)),
            None,
        )
        if frontend is None:
            continue

        fragment = frontend.lower(discovered.absolute_path, root=root)
        fragments.append(fragment)

    if truncated:
        scan_level_diagnostics.append(
            Diagnostic(
                level=DiagnosticLevel.WARNING,
                message=(
                    f"{SCAN_LIMIT_PREFIX} exceeded whole-scan time budget "
                    f"({limits.wall_clock_budget_seconds}s); remaining files were not scanned"
                ),
            )
        )

    # Config-loading diagnostics (e.g. unknown keys) are scan-level too.
    scan_level_diagnostics.extend(effective_config.diagnostics)

    if scan_level_diagnostics:
        fragments.append(
            IRFragment(file=SCAN_LEVEL_FILE, diagnostics=tuple(scan_level_diagnostics))
        )

    return tuple(fragments)
