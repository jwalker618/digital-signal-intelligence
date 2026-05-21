"""V7 Phase 5 — compliance-grade audit log (distinct from operational AuditLog).

Lives at ``infrastructure/db/models.py:ComplianceAuditLog``. This module
provides the canonical write API and the documented set of event types.

Adding a new event type? Append the constant below and document its
payload shape inline. Tests assert event_type is one of the known
constants when checked.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from infrastructure.db.models import ComplianceAuditLog


# Canonical event types. Other modules should import from here.
EVENT_EVIDENCE_GRADE_REFERRAL_FIRED = "evidence_grade_referral_fired"
EVENT_EVIDENCE_GRADE_POLICY_EVALUATED = "evidence_grade_policy_evaluated"
EVENT_EXPECTED_GRADE_VIOLATION = "expected_grade_violation"
EVENT_VALIDATOR_VERDICT = "validator_verdict"
EVENT_VALIDATOR_FAILURE = "validator_failure"
EVENT_CALIBRATION_SAMPLE_LOGGED = "calibration_sample_logged"
EVENT_CALIBRATION_DECISION_RECORDED = "calibration_decision_recorded"
EVENT_COMMITMENT_COMMITTED = "commitment_committed"
EVENT_MECHANISM_STORED = "mechanism_stored"
EVENT_MECHANISM_EXTRACTION_FAILED = "mechanism_extraction_failed"
EVENT_ROOT_CAUSE_CLUSTER = "root_cause_cluster"
EVENT_VARIANT_GENERATED = "variant_generated"
EVENT_VARIANT_EXTRACTED = "variant_extracted"
EVENT_VARIANT_NO_OP = "variant_no_op"
EVENT_ENTITY_EVENT_RECEIVED = "entity_event_received"
EVENT_DELTA_RECOMPUTE_STARTED = "delta_recompute_started"
EVENT_DELTA_RECOMPUTE_COMPLETED = "delta_recompute_completed"

KNOWN_EVENT_TYPES: frozenset[str] = frozenset({
    EVENT_EVIDENCE_GRADE_REFERRAL_FIRED,
    EVENT_EVIDENCE_GRADE_POLICY_EVALUATED,
    EVENT_EXPECTED_GRADE_VIOLATION,
    EVENT_VALIDATOR_VERDICT,
    EVENT_VALIDATOR_FAILURE,
    EVENT_CALIBRATION_SAMPLE_LOGGED,
    EVENT_CALIBRATION_DECISION_RECORDED,
    EVENT_COMMITMENT_COMMITTED,
    EVENT_MECHANISM_STORED,
    EVENT_MECHANISM_EXTRACTION_FAILED,
    EVENT_ROOT_CAUSE_CLUSTER,
    EVENT_VARIANT_GENERATED,
    EVENT_VARIANT_EXTRACTED,
    EVENT_VARIANT_NO_OP,
    EVENT_ENTITY_EVENT_RECEIVED,
    EVENT_DELTA_RECOMPUTE_STARTED,
    EVENT_DELTA_RECOMPUTE_COMPLETED,
})


def log_event(
    db: Session,
    *,
    event_type: str,
    payload: dict[str, Any],
    model_version_id: Optional[uuid.UUID] = None,
    submission_id: Optional[uuid.UUID] = None,
    signal_id: Optional[str] = None,
    actor: str = "system",
) -> None:
    """Insert a ComplianceAuditLog row. Caller commits.

    Accepts unknown `event_type` so future phases can introduce new types
    without touching this module; callers are encouraged to use the
    EVENT_* constants for known types and `KNOWN_EVENT_TYPES` for
    validation in tests.
    """
    db.add(ComplianceAuditLog(
        event_type=event_type,
        model_version_id=model_version_id,
        submission_id=submission_id,
        signal_id=signal_id,
        actor=actor,
        payload=payload,
    ))
