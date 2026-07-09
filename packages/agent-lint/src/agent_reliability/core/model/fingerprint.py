"""The ``fp_v1`` fingerprint contract.

A fingerprint identifies "the same finding" across rescans so that baselines and suppressions
survive line drift and reformatting. It deliberately excludes line/column numbers and excludes
severity/message text (so a config-driven severity override, or a rewording of a rule's
description, does not silently reactivate every suppressed finding).

This module defines the *algorithm contract*: it hashes a caller-supplied structural hash of the
matched code, not the source text itself. Computing that structural hash is the frontend's job
(it is language-specific — see ``agent_reliability.lint.frontend`` for the Python AST
implementation) because ``agent_reliability.core`` must stay language-agnostic.

Changing this algorithm requires a new version tag and a migration path for existing baseline
files — see ``PLAN.md`` section 13 ("Fingerprints") and ADR-010 (SARIF).
"""

from __future__ import annotations

import hashlib

FINGERPRINT_ALGORITHM_VERSION = "fp_v1"


def compute_fingerprint(
    *,
    rule_id: str,
    rule_major_version: int,
    normalized_path: str,
    structural_hash: str,
    occurrence_index: int = 0,
) -> str:
    """Compute a stable ``fp_v1`` fingerprint.

    Args:
        rule_id: e.g. ``"AR001"``.
        rule_major_version: the rule's major version — changing this intentionally busts
            fingerprints for that rule (a documented, versioned event, not an accident).
        normalized_path: repo-relative, POSIX-normalized file path (see ``SourceSpan``).
        structural_hash: a hash of the matched AST/IR node's shape, excluding source positions.
            Two occurrences with identical structure and identical position in the file's
            occurrence order produce the same fingerprint; that's intentional — disambiguation
            across truly distinct locations is the job of ``occurrence_index``.
        occurrence_index: disambiguates multiple structurally-identical matches in one file
            (e.g. the same unsafe pattern copy-pasted twice).

    Returns:
        A stable, opaque hex string prefixed with the algorithm version, e.g.
        ``"fp_v1:3a1c9e...".``
    """
    payload = "\x1f".join(
        (
            FINGERPRINT_ALGORITHM_VERSION,
            rule_id,
            str(rule_major_version),
            normalized_path,
            structural_hash,
            str(occurrence_index),
        )
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{FINGERPRINT_ALGORITHM_VERSION}:{digest}"
