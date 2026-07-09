from __future__ import annotations

from agent_reliability.lint.terminal_safety import sanitize_for_terminal


def test_plain_text_is_unchanged() -> None:
    assert sanitize_for_terminal("hello world") == "hello world"


def test_newlines_and_tabs_survive() -> None:
    text = "line one\n\tindented\nline two"
    assert sanitize_for_terminal(text) == text


def test_strips_ansi_color_codes() -> None:
    colored = "\x1b[31mred text\x1b[0m"
    assert sanitize_for_terminal(colored) == "red text"


def test_strips_cursor_movement_sequences() -> None:
    text = "before\x1b[2Kafter"
    assert sanitize_for_terminal(text) == "beforeafter"


def test_strips_osc_sequences() -> None:
    # OSC sequences can, on some terminals, rewrite the window title or worse.
    text = "before\x1b]0;evil title\x07after"
    assert sanitize_for_terminal(text) == "beforeafter"


def test_strips_bell_and_control_chars() -> None:
    text = "before\x07\x00\x01after"
    assert sanitize_for_terminal(text) == "beforeafter"


def test_strips_del_character() -> None:
    assert sanitize_for_terminal("a\x7fb") == "ab"


def test_strips_lone_escape_not_part_of_a_recognized_sequence() -> None:
    # 'z' (0x7A) is outside the recognized two-character ESC-sequence final-byte ranges, so
    # this exercises the bare-ESC fallback rather than the structured-sequence alternative.
    assert sanitize_for_terminal("a\x1bzb") == "azb"


def test_strips_trailing_lone_escape() -> None:
    assert sanitize_for_terminal("a\x1b") == "a"


def test_hostile_filename_style_payload() -> None:
    # A filename or evidence string crafted to hide/rewrite terminal output.
    payload = "safe_name\x1b[2K\x1b[1Ghidden_malicious_content.py"
    sanitized = sanitize_for_terminal(payload)
    assert "\x1b" not in sanitized
