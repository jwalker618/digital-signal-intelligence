"""V6/E6 — detector ↔ referral-bridge wiring.

Exposes `wire_default_drift_observers(detector, db_factory)` which
attaches a DriftReferralBridge whose dispatcher writes a row into the
`referrals` table with `referral_type = 'DRIFT'` and the source
`drift_alert_id` FK populated.

Usage (application bootstrap)::

    from world_engine.drift.detector import DriftDetector
    from world_engine.drift.wiring import wire_default_drift_observers
    detector = DriftDetector()
    wire_default_drift_observers(detector, db_factory=get_db_session)

Keeping the wiring in a separate module means the detector never
imports the referral service directly (avoiding a circular dep) and
tests can wire alternative dispatchers trivially.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from sqlalchemy import text

from world_engine.drift.referral_bridge import (
    DriftReferral,
    DriftReferralBridge,
)

log = logging.getLogger("dsi.drift.wiring")


DBFactory = Callable[[], Any]


def _referral_row_dispatcher(db_factory: DBFactory) -> Callable[[DriftReferral], None]:
    """Return a dispatcher that INSERTs a referral row per DriftReferral.

    The existing `referrals` table gained two columns via alembic 022:
    `referral_type` + `drift_alert_id`. We write the minimum set of
    columns; other fields (quote_id, referral_code, priority) default.
    """
    def dispatch(referral: DriftReferral) -> None:
        db = db_factory()
        try:
            db.execute(
                text(
                    "INSERT INTO referrals "
                    "  (id, referral_code, referral_type, drift_alert_id, "
                    "   reasons, priority, status) "
                    "VALUES "
                    "  (gen_random_uuid(), "
                    "   concat('DR-', substr(md5(random()::text), 1, 10)), "
                    "   'DRIFT', :drift_alert_id, "
                    "   :reasons, :priority, 'PENDING')"
                ),
                {
                    "drift_alert_id": referral.drift_alert_id,
                    "reasons": [
                        {
                            "kind": referral.drift_type,
                            "severity": referral.severity,
                            "message": referral.message,
                            "detected_at": referral.detected_at,
                            "coverage": referral.coverage,
                            "config_id": referral.config_id,
                            "entity_id": referral.entity_id,
                        }
                    ],
                    "priority": _priority_for_severity(referral.severity),
                },
            )
            try:
                db.commit()
            except Exception:
                pass
        finally:
            try:
                db.close()
            except Exception:
                pass
    return dispatch


def _priority_for_severity(severity: str) -> int:
    return {"high": 1, "medium": 3, "low": 6}.get(severity, 5)


def wire_default_drift_observers(
    detector,
    *,
    db_factory: Optional[DBFactory] = None,
    extra_dispatchers: Optional[list] = None,
) -> DriftReferralBridge:
    """Attach the default referral-row dispatcher to ``detector``.

    Returns the DriftReferralBridge so callers can register additional
    dispatchers (e.g. Slack / PagerDuty) after wiring.
    """
    dispatchers = []
    if db_factory is not None:
        dispatchers.append(_referral_row_dispatcher(db_factory))
    for d in extra_dispatchers or []:
        dispatchers.append(d)

    bridge = DriftReferralBridge(dispatchers=dispatchers)
    detector.on_alert(bridge.dispatch_alert)
    return bridge
