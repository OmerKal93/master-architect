"""The safe Python frontend: turns ``.py`` files into micro-IR without ever executing them.

Public entry points:

- ``PythonFrontend`` — the ``Frontend`` protocol implementation for one file.
- ``scan_repository`` — discovers and lowers every supported file under a root, enforcing
  resource limits and reporting scan-level diagnostics honestly (never silently truncating).
- ``ScanLimits`` / ``DEFAULT_SCAN_LIMITS`` — the resource bounds every scan runs under.

See ``docs/architecture/what-the-analyzer-sees.md`` for the honest capability statement: what
this frontend can and cannot recognize, and why.
"""

from __future__ import annotations

from agent_reliability.lint.frontend.limits import DEFAULT_SCAN_LIMITS, ScanLimits
from agent_reliability.lint.frontend.python_frontend import PythonFrontend
from agent_reliability.lint.frontend.scan import scan_repository

__all__ = [
    "DEFAULT_SCAN_LIMITS",
    "PythonFrontend",
    "ScanLimits",
    "scan_repository",
]
