"""Terminal-escape stripping for CLI output (PLAN.md threat T12).

Evidence, filenames, and other strings that end up in terminal output may originate from a
scanned repository the user does not control. Without sanitization, a filename or piece of
source code containing ANSI/VT100 control sequences could manipulate the terminal (hide or
rewrite text, move the cursor, spoof a prompt) on some terminal emulators. Every string this CLI
prints is passed through ``sanitize_for_terminal`` first — including the fixed strings this
module itself writes, since defense-in-depth here is cheap and the alternative is remembering to
sanitize at every call site individually.
"""

from __future__ import annotations

import re

# ANSI CSI sequences (ESC [ ... final-byte), OSC sequences (ESC ] ... BEL), and other
# two-character ESC sequences, tried FIRST so a full escape sequence is stripped as one unit
# rather than the alternation matching just the leading ESC byte via the bare control-char
# class below (regex alternation is "first match wins per position", not "longest match wins").
# Then: C0 control characters except \t and \n (legitimate in multi-line output), plus DEL. ESC
# (\x1b) is deliberately excluded from that class -- it is handled by the first alternative
# above; the final `|\x1b` alternative is a fallback that still strips a lone ESC byte that
# wasn't part of any recognized sequence, so nothing with a raw ESC ever reaches the terminal.
_CONTROL_CHAR_PATTERN = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*\x07|[@-Z\\-_])"
    r"|[\x00-\x08\x0b\x0c\x0e-\x1a\x1c-\x1f\x7f]"
    r"|\x1b"
)


def sanitize_for_terminal(text: str) -> str:
    """Strip control characters and escape sequences that could manipulate a terminal."""
    return _CONTROL_CHAR_PATTERN.sub("", text)
