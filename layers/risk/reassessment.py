"""v8 Phase 5: re-assessment with direct-query signal override.

Used by the broker-reply endpoint to apply a signal value update and
re-invoke the existing workflow. No new pricing or scoring -- this is
a thin orchestration layer over `layers.risk.workflow.run_assessment`.

Pure-ish: the merge helper is fully pure (used by tests); the
`reassess_with_signal_override` function wraps run_assessment which
itself has its own side effects but does not touch the DB. Persistence
of the new model_version + quote is the caller's responsibility (the
existing persistence path in infrastructure/api/routes/submissions.py).
"""
from __future__ import annotations

from typing import Any, Optional

from layers.risk.types import WorkflowResult


class UnknownSignalError(ValueError):
    """Raised when a signal_value_update names a signal not in the coverage."""


def merge_direct_query_responses(
    existing: Optional[dict[str, Any]],
    signal_id: str,
    new_value: Any,
) -> dict[str, Any]:
    """Return a copy of `existing` with signal_id -> new_value applied.

    Pure function. Does not mutate `existing`. None is treated as an
    empty dict. `new_value` is coerced to bool if it looks boolean
    (str "true"/"false", 0/1) so the rest of the workflow can rely on
    bool typing -- direct_query_responses are Dict[str, bool] in the
    workflow signature.
    """
    base = dict(existing or {})
    base[signal_id] = _coerce_bool(new_value)
    return base


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true", "yes", "1", "y", "t"):
            return True
        if v in ("false", "no", "0", "n", "f"):
            return False
    # Anything else: best-effort truthiness
    return bool(value)


def reassess_with_signal_override(
    *,
    entity_id: str,
    coverage: str,
    submission_data: Optional[dict[str, Any]],
    existing_responses: Optional[dict[str, Any]],
    signal_id: str,
    new_value: Any,
    entity_name: Optional[str] = None,
    domain_hint: Optional[str] = None,
    country_hint: Optional[str] = None,
) -> tuple[WorkflowResult, dict[str, Any]]:
    """Apply a signal override and re-invoke the workflow.

    Returns a tuple of:
      - the new WorkflowResult
      - the merged direct_query_responses dict (so the caller can
        persist it back onto the Submission row)

    The caller is responsible for:
      - validating that signal_id is known to the coverage
      - persisting the new ModelVersionRecord and Quote
      - linking the new quote to the originating ReferralMessage
        (via referral_messages.new_quote_id)
    """
    merged = merge_direct_query_responses(existing_responses, signal_id, new_value)

    # Lazy import: run_assessment imports the whole workflow engine which
    # is heavyweight. Keep this module cheap to import.
    from layers.risk.workflow import run_assessment

    result = run_assessment(
        entity_id=entity_id,
        coverage=coverage,
        submission_data=submission_data or {},
        direct_query_responses=merged,
        user="portal-broker-reply",
        entity_name=entity_name,
        domain_hint=domain_hint,
        country_hint=country_hint,
        skip_discovery=True,
    )
    return result, merged
