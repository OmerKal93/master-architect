"""AT6 -- ART-0-plan.md section 5, Target 1 (AO-1 mutation testing dogfood), narrowed scope.

Real `node` subprocess calls -- not mocked. The "real" case requires HarnessKit's own, unmodified,
already-merged claimDecisionDispatch (scripts/manager-advisor/ao1-dispatch.js) by path; this test
never edits or writes to the HarnessKit repo. The "mutant" case is a standalone reimplementation
with the exact one dedup check removed (see tests/ao1_fixtures/run_mutant_claim.js's own header
for the precise diff).

Pass condition (ART-0-plan.md section 5): `at_most_once`, via the AO-1 trace-ingestion adapter,
must PASS on the real code and FAIL on the mutant.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from art_contracts.ao1_adapter import ingest_ao1_claim_log
from art_contracts.contract import ContractViolation, check_at_most_once

HARNESSKIT_REPO = "C:/Dev/hk-worktrees/phase-a-v1-integration"
FIXTURES_DIR = Path(__file__).parent / "ao1_fixtures"

# Independent-review fix: HARNESSKIT_REPO points at a separate project's git worktree, which is
# routinely created/removed as part of that project's own workflow -- skip with a clear reason
# instead of a raw Node MODULE_NOT_FOUND stack trace if it's ever absent.
_harnesskit_missing_reason = (
    f"HarnessKit worktree not found at {HARNESSKIT_REPO} -- this test requires its real, "
    "unmodified scripts/manager-advisor/ao1-dispatch.js by path (read-only, never modified)."
)
requires_harnesskit_repo = pytest.mark.skipif(
    not Path(HARNESSKIT_REPO).exists(), reason=_harnesskit_missing_reason
)


def _run_node_fixture(args: list[str]) -> dict:
    # Independent-review fix: `text=True` without an explicit encoding decodes stdout using the
    # OS's locale-preferred codepage (e.g. cp1255 on this machine), not UTF-8 -- Node always
    # writes UTF-8. A reviewer reproduced a silent decode failure (stdout becomes None, masked
    # inside subprocess's reader thread) whenever a non-ASCII byte appears in the JSON payload
    # (e.g. a temp path under a non-ASCII user profile). Fixed by decoding as UTF-8 explicitly.
    result = subprocess.run(
        ["node", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, f"node fixture failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    return json.loads(result.stdout)


@pytest.fixture
def scratch_dirs():
    base = tempfile.mkdtemp(prefix="art0-ao1-dogfood-")
    yield {
        "real_scratch": str(Path(base) / "real-scratch"),
        "mutant_scratch": str(Path(base) / "mutant-scratch"),
        "real_log": str(Path(base) / "real-claims.ndjson"),
        "mutant_log": str(Path(base) / "mutant-claims.ndjson"),
    }
    shutil.rmtree(base, ignore_errors=True)


@requires_harnesskit_repo
def test_real_unmodified_ao1_dedup_passes_at_most_once(scratch_dirs):
    """The real, unmodified, already-merged AO-1 dedup guard must produce exactly one successful
    claim for two attempts at the same decision_id -- so at_most_once must PASS (no violation).
    """
    _run_node_fixture([
        str(FIXTURES_DIR / "run_real_claim.js"),
        HARNESSKIT_REPO,
        scratch_dirs["real_log"],
        scratch_dirs["real_scratch"],
    ])

    ledger = ingest_ao1_claim_log(scratch_dirs["real_log"])
    assert len(ledger.invocations) == 1, (
        f"expected exactly 1 successful claim from the real dedup guard, got {len(ledger.invocations)}"
    )
    check_at_most_once(ledger, key_fields=("decision_id",))  # must not raise


def test_mutant_ao1_dedup_is_caught_by_at_most_once(scratch_dirs):
    """The approved mutant (dedup check removed) must produce TWO successful claims for the same
    decision_id -- so at_most_once must FAIL, proving the contract checker has real detection
    power and doesn't just always pass.
    """
    _run_node_fixture([
        str(FIXTURES_DIR / "run_mutant_claim.js"),
        scratch_dirs["mutant_log"],
        scratch_dirs["mutant_scratch"],
    ])

    ledger = ingest_ao1_claim_log(scratch_dirs["mutant_log"])
    assert len(ledger.invocations) == 2, (
        f"expected exactly 2 successful claims from the mutant (bug reproduced), got {len(ledger.invocations)}"
    )
    with pytest.raises(ContractViolation) as excinfo:
        check_at_most_once(ledger, key_fields=("decision_id",))
    assert excinfo.value.contract_name == "at_most_once"
    assert "art0-mutant-dedup-check" in str(excinfo.value)
