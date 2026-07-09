from __future__ import annotations

import ast

from agent_reliability.lint.frontend.ast_utils import (
    dotted_name,
    exceeds_node_limit,
    safe_parse,
    span_of,
    structural_hash,
)
from agent_reliability.lint.frontend.limits import SCAN_LIMIT_PREFIX


class TestSafeParse:
    def test_parses_valid_source(self) -> None:
        tree, diagnostic = safe_parse("x = 1\n", relative_path="a.py")
        assert tree is not None
        assert diagnostic is None

    def test_syntax_error_is_caught(self) -> None:
        tree, diagnostic = safe_parse("def f(:\n", relative_path="a.py")
        assert tree is None
        assert diagnostic is not None
        assert diagnostic.file == "a.py"

    def test_null_byte_is_caught(self) -> None:
        tree, diagnostic = safe_parse("x = 1\x00\n", relative_path="a.py")
        assert tree is None
        assert diagnostic is not None

    def test_deeply_nested_parentheses_is_categorized_as_scan_limit(self) -> None:
        source = "x = " + "(" * 600 + "1" + ")" * 600 + "\n"
        tree, diagnostic = safe_parse(source, relative_path="a.py")
        assert tree is None
        assert diagnostic is not None
        assert diagnostic.message.startswith(SCAN_LIMIT_PREFIX)

    def test_ordinary_syntax_error_is_not_categorized_as_scan_limit(self) -> None:
        tree, diagnostic = safe_parse("def f(:\n", relative_path="a.py")
        assert tree is None
        assert diagnostic is not None
        assert not diagnostic.message.startswith(SCAN_LIMIT_PREFIX)

    def test_never_executes_source(self) -> None:
        # If this were ever executed rather than only parsed, the sentinel file would be
        # written to disk. Its absence is the proof.
        import tempfile
        from pathlib import Path

        sentinel = Path(tempfile.gettempdir()) / "art_e03_should_never_exist.txt"
        sentinel.unlink(missing_ok=True)
        source = f"open({str(sentinel)!r}, 'w').write('pwned')\n"
        safe_parse(source, relative_path="a.py")
        assert not sentinel.exists()


class TestNodeLimit:
    def test_small_tree_under_limit(self) -> None:
        tree = ast.parse("x = 1\n")
        assert exceeds_node_limit(tree, limit=1000) is False

    def test_exceeds_limit_with_low_threshold(self) -> None:
        tree = ast.parse("x = 1\ny = 2\nz = 3\n")
        assert exceeds_node_limit(tree, limit=2) is True

    def test_exits_early_without_counting_whole_tree(self) -> None:
        # A large tree with a very low limit should still return quickly. This is a smoke
        # test, not a timing assertion, but it exercises the early-exit path.
        big_source = "\n".join(f"x{i} = {i}" for i in range(5000))
        tree = ast.parse(big_source)
        assert exceeds_node_limit(tree, limit=10) is True


class TestStructuralHash:
    def test_identical_shape_same_hash(self) -> None:
        tree1 = ast.parse("while True:\n    f()\n")
        tree2 = ast.parse("\n\n\nwhile True:\n    f()\n")  # same shape, different position
        loop1 = tree1.body[0]
        loop2 = tree2.body[0]
        assert structural_hash(loop1) == structural_hash(loop2)

    def test_different_shape_different_hash(self) -> None:
        tree1 = ast.parse("while True:\n    f()\n")
        tree2 = ast.parse("while True:\n    g()\n")
        assert structural_hash(tree1.body[0]) != structural_hash(tree2.body[0])

    def test_returns_hex_digest(self) -> None:
        tree = ast.parse("x = 1\n")
        h = structural_hash(tree)
        assert len(h) == 64
        int(h, 16)


class TestDottedName:
    def test_simple_attribute(self) -> None:
        node = ast.parse("requests.post").body[0].value  # type: ignore[attr-defined]
        assert dotted_name(node) == "requests.post"

    def test_nested_attribute(self) -> None:
        node = ast.parse("a.b.c.d").body[0].value  # type: ignore[attr-defined]
        assert dotted_name(node) == "a.b.c.d"

    def test_bare_name(self) -> None:
        node = ast.parse("foo").body[0].value  # type: ignore[attr-defined]
        assert dotted_name(node) == "foo"

    def test_dynamic_callee_returns_none(self) -> None:
        # e.g. `get_client().post` -- the base is a Call, not a Name, so there's no stable
        # dotted name to give it.
        node = ast.parse("get_client().post").body[0].value  # type: ignore[attr-defined]
        assert dotted_name(node) is None


class TestSpanOf:
    def test_builds_span_from_node_positions(self) -> None:
        tree = ast.parse("x = 1\n")
        node = tree.body[0]
        span = span_of(node, relative_path="a.py")
        assert span.file == "a.py"
        assert span.start_line == 1
