"""ART-0 pytest integration (Batch 3). One fixture, nothing more -- per ART-0-plan.md's own
"no DSL yet" / Fable's "zero abstractions without a corresponding line in the demo script"
discipline. `check_at_most_once` raising a real `ContractViolation(AssertionError)` is already
pytest-native (AT5); this fixture only removes per-test ledger-wiring boilerplate.
"""

from __future__ import annotations

import pytest

from art_contracts.contract import LedgerRecorder


@pytest.fixture
def art_ledger() -> LedgerRecorder:
    """A fresh, real side-effect ledger for one test -- pass it into a sample agent's tool
    implementation, then check it with `art_contracts.contract.check_at_most_once`.
    """
    return LedgerRecorder()
