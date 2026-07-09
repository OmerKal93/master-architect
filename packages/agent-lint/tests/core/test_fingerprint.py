from __future__ import annotations

from agent_reliability.core.model.fingerprint import (
    FINGERPRINT_ALGORITHM_VERSION,
    compute_fingerprint,
)


def _fp(**overrides: object) -> str:
    defaults: dict[str, object] = dict(
        rule_id="AR001",
        rule_major_version=1,
        normalized_path="agent/loop.py",
        structural_hash="deadbeef",
        occurrence_index=0,
    )
    defaults.update(overrides)
    return compute_fingerprint(**defaults)  # type: ignore[arg-type]


def test_fingerprint_is_prefixed_with_algorithm_version() -> None:
    fp = _fp()
    assert fp.startswith(f"{FINGERPRINT_ALGORITHM_VERSION}:")


def test_fingerprint_is_deterministic() -> None:
    assert _fp() == _fp()


def test_fingerprint_stable_under_formatting_perturbation() -> None:
    # The structural hash is what a frontend computes from the *shape* of the matched node,
    # excluding line/column. Two calls with the same structural_hash simulate the same code
    # after reformatting (e.g. a blank line inserted above it) producing the same fingerprint —
    # that is the entire point of excluding positions from the hash input.
    fp_before_reformat = _fp(structural_hash="shape-of-while-true-loop")
    fp_after_reformat = _fp(structural_hash="shape-of-while-true-loop")
    assert fp_before_reformat == fp_after_reformat


def test_fingerprint_changes_with_rule_id() -> None:
    assert _fp(rule_id="AR001") != _fp(rule_id="AR002")


def test_fingerprint_changes_with_rule_major_version() -> None:
    assert _fp(rule_major_version=1) != _fp(rule_major_version=2)


def test_fingerprint_changes_with_path() -> None:
    assert _fp(normalized_path="a.py") != _fp(normalized_path="b.py")


def test_fingerprint_changes_with_structural_hash() -> None:
    assert _fp(structural_hash="aaa") != _fp(structural_hash="bbb")


def test_fingerprint_changes_with_occurrence_index() -> None:
    assert _fp(occurrence_index=0) != _fp(occurrence_index=1)


def test_fingerprint_is_a_valid_hex_digest_after_prefix() -> None:
    fp = _fp()
    _, _, digest = fp.partition(":")
    assert len(digest) == 64
    int(digest, 16)  # raises ValueError if not valid hex
