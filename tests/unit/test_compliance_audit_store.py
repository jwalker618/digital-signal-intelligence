"""V7 Phase 5 — compliance_audit_store tests (mock session)."""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from infrastructure.db.compliance_audit_store import (
    EVENT_COMMITMENT_COMMITTED,
    EVENT_EVIDENCE_GRADE_REFERRAL_FIRED,
    EVENT_VALIDATOR_VERDICT,
    KNOWN_EVENT_TYPES,
    log_event,
)
from infrastructure.db.models import ComplianceAuditLog


class TestLogEvent:
    def test_default_actor_is_system(self):
        db = MagicMock()
        log_event(db, event_type=EVENT_EVIDENCE_GRADE_REFERRAL_FIRED, payload={"why": "test"})
        row = db.add.call_args[0][0]
        assert isinstance(row, ComplianceAuditLog)
        assert row.actor == "system"
        assert row.event_type == EVENT_EVIDENCE_GRADE_REFERRAL_FIRED

    def test_carries_optional_ids(self):
        db = MagicMock()
        mv_id = uuid.uuid4()
        sub_id = uuid.uuid4()
        log_event(
            db,
            event_type=EVENT_COMMITMENT_COMMITTED,
            payload={"digest": "abc"},
            model_version_id=mv_id,
            submission_id=sub_id,
            signal_id="sig_a",
        )
        row = db.add.call_args[0][0]
        assert row.model_version_id == mv_id
        assert row.submission_id == sub_id
        assert row.signal_id == "sig_a"
        assert row.payload == {"digest": "abc"}

    def test_accepts_custom_actor(self):
        db = MagicMock()
        log_event(
            db,
            event_type=EVENT_VALIDATOR_VERDICT,
            payload={},
            actor="validator-llm:claude-opus-4-7",
        )
        row = db.add.call_args[0][0]
        assert row.actor == "validator-llm:claude-opus-4-7"

    def test_unknown_event_type_accepted_for_forward_compat(self):
        """Future phases introduce new event types without touching this store."""
        db = MagicMock()
        log_event(db, event_type="future_event_phase99", payload={})
        row = db.add.call_args[0][0]
        assert row.event_type == "future_event_phase99"


class TestKnownEventTypes:
    def test_known_constants_documented(self):
        # Sanity: all event constants live in KNOWN_EVENT_TYPES.
        assert EVENT_EVIDENCE_GRADE_REFERRAL_FIRED in KNOWN_EVENT_TYPES
        assert EVENT_VALIDATOR_VERDICT in KNOWN_EVENT_TYPES
        assert EVENT_COMMITMENT_COMMITTED in KNOWN_EVENT_TYPES
