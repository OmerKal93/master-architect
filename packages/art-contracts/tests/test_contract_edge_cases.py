"""Regression tests for independent-review findings against art_contracts.contract."""

from __future__ import annotations

import pytest

from art_contracts.contract import LedgerRecorder, MissingKeyFieldError, check_at_most_once


def test_missing_key_field_raises_clear_error_not_a_silent_none_collision():
    """Two genuinely DIFFERENT real invocations of a tool with no `request_id` field must not be
    silently reported as a false-positive at_most_once violation via a None==None key collision.
    """
    ledger = LedgerRecorder()
    ledger.record("send_email", {"to": "alice@example.com", "subject": "hi"})
    ledger.record("send_email", {"to": "bob@example.com", "subject": "bye"})

    with pytest.raises(MissingKeyFieldError) as excinfo:
        check_at_most_once(ledger)  # default key_fields=("request_id",), absent from both calls

    assert "send_email" in str(excinfo.value)
    assert "request_id" in str(excinfo.value)


def test_present_key_field_with_genuinely_distinct_values_passes():
    """Control: two real invocations with DIFFERENT, present key values must not violate."""
    ledger = LedgerRecorder()
    ledger.record("process_refund", {"request_id": "req-1", "amount": 10.0})
    ledger.record("process_refund", {"request_id": "req-2", "amount": 20.0})
    check_at_most_once(ledger)  # must not raise
