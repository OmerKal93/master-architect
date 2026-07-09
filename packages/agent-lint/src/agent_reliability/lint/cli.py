"""The ``agent-lint`` CLI.

The exit-code contract is permanent from this PR onward (``EXECUTION.md`` E04): ``scan`` grows
flags over time, never new exit-code semantics.

    0 -- clean scan, no findings
    1 -- scan completed, at least one finding
    2 -- usage error (bad path, bad arguments)
    3 -- internal error (a bug in agent-lint itself; never a raw traceback to the user)
    4 -- partial scan (a resource limit was hit; results may be incomplete)

If both findings and a partial-scan condition occur, exit code 1 takes precedence: a real
finding is actionable regardless of whether the scan was also truncated, and the partial-scan
diagnostics are still printed either way — nothing about the truncation is hidden.
"""

from __future__ import annotations

from pathlib import Path

import typer

from agent_reliability.core.model.config import load_config_for_root
from agent_reliability.lint.engine import run_scan
from agent_reliability.lint.frontend.limits import SCAN_LIMIT_PREFIX
from agent_reliability.lint.reporting.text import render_text
from agent_reliability.lint.terminal_safety import sanitize_for_terminal

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_USAGE_ERROR = 2
EXIT_INTERNAL_ERROR = 3
EXIT_PARTIAL_SCAN = 4

app = typer.Typer(
    name="agent-lint",
    help="Local-first static analyzer for AI agent reliability and security anti-patterns.",
    add_completion=False,
    no_args_is_help=True,
)


@app.callback()
def _callback() -> None:
    """Local-first static analyzer for AI agent reliability and security anti-patterns.

    Present so ``scan`` stays a required, named subcommand (``agent-lint scan PATH``) rather
    than Typer's single-command shortcut collapsing it to ``agent-lint PATH`` -- the documented
    command surface (EXECUTION.md E04) is ``agent-lint scan``, and that is a permanent contract.
    """


@app.command()
def scan(
    path: Path = typer.Argument(  # noqa: B008 -- idiomatic Typer: Argument() belongs in the default
        Path("."), help="Directory to scan. Defaults to the current directory."
    ),
) -> None:
    """Scan PATH for agent reliability and security findings. Runs entirely offline."""
    resolved = path.resolve()

    if not resolved.exists():
        typer.echo(sanitize_for_terminal(f"error: path does not exist: {path}"), err=True)
        raise typer.Exit(EXIT_USAGE_ERROR)
    if not resolved.is_dir():
        typer.echo(sanitize_for_terminal(f"error: path is not a directory: {path}"), err=True)
        raise typer.Exit(EXIT_USAGE_ERROR)

    try:
        config = load_config_for_root(resolved)
        findings, diagnostics = run_scan(resolved, config=config)
    except Exception as exc:  # noqa: BLE001 -- CLI boundary: never leak a raw traceback (exit 3)
        typer.echo(sanitize_for_terminal(f"internal error: {exc}"), err=True)
        raise typer.Exit(EXIT_INTERNAL_ERROR) from exc

    output = render_text(findings, diagnostics)
    typer.echo(sanitize_for_terminal(output))

    if findings:
        raise typer.Exit(EXIT_FINDINGS)
    if any(d.message.startswith(SCAN_LIMIT_PREFIX) for d in diagnostics):
        raise typer.Exit(EXIT_PARTIAL_SCAN)
    raise typer.Exit(EXIT_CLEAN)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
