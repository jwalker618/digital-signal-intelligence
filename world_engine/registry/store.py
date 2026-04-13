"""
World Engine: Intelligence Registry (WE-1d)

Single point of access for all World Engine intelligence. Wraps the database
with a query-optimised read API and a write API used only by internal
subsystems. The write API is not exposed via HTTP -- only internal Python
access.

See development/project/version/5/world_engine_phases/WE-1_Foundation.md
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.maturity import MaturityEvaluator
from world_engine.types import (
    CausalAdjustmentFactor,
    ConsistencyScore,
    DiscoveredRelationship,
    DriftAlert,
    DriftSeverity,
    LifecycleState,
    MaturityState,
    PortfolioConcentration,
    ScanRunReport,
    StateTransition,
)


class IntelligenceRegistry:
    """Single point of access for all World Engine intelligence.

    Reads are available to all DSI components. Writes are internal only --
    invoked by Engine subsystems (Consistency Scorer, Discovery Pipeline,
    Causal Pricing Engine, Portfolio Builder).
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================================================================
    # READ API -- available to all DSI components
    # ==================================================================

    def get_maturity_state(self) -> MaturityState:
        """Current maturity stage with capability flags."""
        return MaturityEvaluator().evaluate(self.db)

    def get_active_relationships(
        self, signal_ids: Optional[list[str]] = None
    ) -> list[DiscoveredRelationship]:
        """All ACTIVE relationships, optionally filtered by signal participation."""
        query = """
            SELECT * FROM we_relationships
            WHERE lifecycle_state = 'active'
        """
        params: dict = {}
        if signal_ids:
            query += " AND (source_signal = ANY(:signals) OR target_signal = ANY(:signals))"
            params["signals"] = list(signal_ids)
        rows = self.db.execute(text(query), params).mappings().all()
        return [self._row_to_relationship(r) for r in rows]

    def get_relationships_for_entity(
        self, signal_scores: dict[str, float]
    ) -> list[DiscoveredRelationship]:
        """Active relationships matching any of the entity's signals."""
        if not signal_scores:
            return []
        return self.get_active_relationships(signal_ids=list(signal_scores.keys()))

    def get_relationship(self, relationship_id: str) -> Optional[DiscoveredRelationship]:
        """Single relationship with full state history."""
        row = self.db.execute(
            text("SELECT * FROM we_relationships WHERE id = :id"),
            {"id": relationship_id},
        ).mappings().first()
        if row is None:
            return None
        rel = self._row_to_relationship(row)
        rel.state_history = self._load_state_history(relationship_id)
        return rel

    def list_relationships(
        self,
        state: Optional[LifecycleState] = None,
        source_signal: Optional[str] = None,
        target_signal: Optional[str] = None,
        coverage: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[DiscoveredRelationship], int]:
        """Paginated list of relationships with filters. Returns (items, total)."""
        conditions: list[str] = []
        params: dict = {"limit": limit, "offset": offset}

        if state is not None:
            conditions.append("lifecycle_state = :state")
            params["state"] = state.value
        if source_signal is not None:
            conditions.append("source_signal = :source")
            params["source"] = source_signal
        if target_signal is not None:
            conditions.append("target_signal = :target")
            params["target"] = target_signal
        if coverage is not None:
            conditions.append("coverage_scope @> :coverage::jsonb")
            params["coverage"] = f'["{coverage}"]'

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        total = self.db.execute(
            text(f"SELECT COUNT(*) FROM we_relationships{where}"), params
        ).scalar() or 0

        rows = self.db.execute(
            text(
                f"SELECT * FROM we_relationships{where} "
                "ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        ).mappings().all()

        return [self._row_to_relationship(r) for r in rows], int(total)

    def get_consistency_score(self, assessment_id: str) -> Optional[ConsistencyScore]:
        row = self.db.execute(
            text(
                "SELECT * FROM we_consistency_scores "
                "WHERE assessment_id = :aid ORDER BY computed_at DESC LIMIT 1"
            ),
            {"aid": assessment_id},
        ).mappings().first()
        if row is None:
            return None
        return ConsistencyScore(
            entity_id=row["entity_id"],
            assessment_id=row["assessment_id"],
            overall_consistency=row["overall_consistency"],
            signal_pair_scores=row["signal_pair_scores"] or {},
            cross_group_scores=row["cross_group_scores"] or {},
            cross_layer_divergence=row["cross_layer_divergence"] or {},
            divergent_pairs=row["divergent_pairs"] or [],
            computed_at=row["computed_at"],
        )

    def get_caf(self, assessment_id: str) -> Optional[CausalAdjustmentFactor]:
        row = self.db.execute(
            text(
                "SELECT * FROM we_causal_adjustments "
                "WHERE assessment_id = :aid ORDER BY computed_at DESC LIMIT 1"
            ),
            {"aid": assessment_id},
        ).mappings().first()
        if row is None:
            return None
        return self._row_to_caf(row)

    def get_portfolio_concentrations(
        self, commercial_entity_id: str
    ) -> list[PortfolioConcentration]:
        rows = self.db.execute(
            text(
                "SELECT * FROM we_portfolio_concentrations "
                "WHERE entity_id = :eid ORDER BY severity DESC"
            ),
            {"eid": commercial_entity_id},
        ).mappings().all()
        return [
            PortfolioConcentration(
                entity_id=r["entity_id"],
                dimension=r["dimension"],
                detail=r["detail"],
                severity=r["severity"],
                affected_entities=r["affected_entities"] or [],
                computed_at=r["computed_at"],
            )
            for r in rows
        ]

    def get_drift_alerts(
        self,
        severity: Optional[DriftSeverity] = None,
        since: Optional[datetime] = None,
        unacknowledged_only: bool = False,
        limit: int = 100,
    ) -> list[DriftAlert]:
        conditions: list[str] = []
        params: dict = {"limit": limit}
        if severity is not None:
            conditions.append("severity = :sev")
            params["sev"] = severity.value
        if since is not None:
            conditions.append("detected_at >= :since")
            params["since"] = since
        if unacknowledged_only:
            conditions.append("acknowledged = false")

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = self.db.execute(
            text(
                f"SELECT * FROM we_drift_alerts{where} "
                "ORDER BY detected_at DESC LIMIT :limit"
            ),
            params,
        ).mappings().all()
        return [self._row_to_drift(r) for r in rows]

    def get_engine_stats(self) -> dict:
        """Summary statistics for the /stats endpoint.

        World-engine tables live only in alembic migration 011. When the
        schema was bootstrapped via Base.metadata.create_all (no alembic
        run), those tables won't exist and every query below would raise.
        Each probe is therefore wrapped defensively -- missing tables
        surface as zero counts so the endpoint still returns a usable
        payload instead of a 500. Matches the pattern in
        world_engine/maturity.py._count_relationships.
        """
        def _scalar(sql: str, params: dict | None = None) -> int:
            try:
                result = self.db.execute(text(sql), params or {}).scalar()
                return int(result or 0)
            except Exception:
                self.db.rollback()
                return 0

        def _rows(sql: str) -> list:
            try:
                return self.db.execute(text(sql)).all()
            except Exception:
                self.db.rollback()
                return []

        counts_by_state = dict(
            _rows(
                "SELECT lifecycle_state, COUNT(*) FROM we_relationships "
                "GROUP BY lifecycle_state"
            )
        )
        scan_total = _scalar("SELECT COUNT(*) FROM we_scan_runs")
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        scan_week = _scalar(
            "SELECT COUNT(*) FROM we_scan_runs WHERE started_at >= :since",
            {"since": week_ago},
        )
        drift_unack = _scalar(
            "SELECT COUNT(*) FROM we_drift_alerts WHERE acknowledged = false"
        )
        cons_total = _scalar("SELECT COUNT(*) FROM we_consistency_scores")
        caf_total = _scalar("SELECT COUNT(*) FROM we_causal_adjustments")
        return {
            "relationships_by_state": {
                state: int(count) for state, count in counts_by_state.items()
            },
            "scan_runs_total": scan_total,
            "scan_runs_last_7_days": scan_week,
            "drift_alerts_unacknowledged": drift_unack,
            "consistency_scores_total": cons_total,
            "caf_computations_total": caf_total,
        }

    # ==================================================================
    # WRITE API -- internal use only
    # ==================================================================

    def register_candidate(self, relationship: DiscoveredRelationship) -> str:
        """Insert a new CANDIDATE relationship. Returns the generated id."""
        rel_id = relationship.id or str(uuid.uuid4())
        self.db.execute(
            text(
                """
                INSERT INTO we_relationships (
                    id, source_signal, target_signal, direction, lag_months,
                    correlation_rho, granger_f_statistic, granger_p_value,
                    effect_size, confounders_tested, holdout_rho, holdout_p_value,
                    predictive_hit_rate, population_size, coverage_scope,
                    lifecycle_state, state_entered_at, influence_weight,
                    created_at, updated_at
                ) VALUES (
                    :id, :source, :target, :direction, :lag,
                    :rho, :gf, :gp,
                    :eff, CAST(:conf AS jsonb), :h_rho, :h_p,
                    :hit, :pop, CAST(:cov AS jsonb),
                    :state, :entered, :weight,
                    :created, :updated
                )
                """
            ),
            {
                "id": rel_id,
                "source": relationship.source_signal,
                "target": relationship.target_signal,
                "direction": relationship.direction.value,
                "lag": relationship.lag_months,
                "rho": relationship.correlation_rho,
                "gf": relationship.granger_f_statistic,
                "gp": relationship.granger_p_value,
                "eff": relationship.effect_size,
                "conf": _json(relationship.confounders_tested),
                "h_rho": relationship.holdout_rho,
                "h_p": relationship.holdout_p_value,
                "hit": relationship.predictive_hit_rate,
                "pop": relationship.population_size,
                "cov": _json(relationship.coverage_scope),
                "state": relationship.lifecycle_state.value,
                "entered": relationship.state_entered_at,
                "weight": relationship.influence_weight,
                "created": relationship.created_at,
                "updated": relationship.updated_at,
            },
        )
        return rel_id

    def transition_state(
        self,
        relationship_id: str,
        to_state: LifecycleState,
        reason: str,
        evidence: dict,
    ) -> StateTransition:
        """Record a lifecycle state transition. Updates relationship and writes audit row."""
        now = datetime.now(timezone.utc)

        current = self.db.execute(
            text("SELECT lifecycle_state FROM we_relationships WHERE id = :id"),
            {"id": relationship_id},
        ).scalar()
        if current is None:
            raise ValueError(f"Relationship {relationship_id} not found")

        from_state = LifecycleState(current)

        # Write transition audit row
        self.db.execute(
            text(
                """
                INSERT INTO we_state_transitions (
                    relationship_id, from_state, to_state, transitioned_at, reason, evidence
                ) VALUES (
                    :id, :from_s, :to_s, :at, :reason, CAST(:ev AS jsonb)
                )
                """
            ),
            {
                "id": relationship_id,
                "from_s": from_state.value,
                "to_s": to_state.value,
                "at": now,
                "reason": reason,
                "ev": _json(evidence),
            },
        )

        # Update relationship state
        self.db.execute(
            text(
                "UPDATE we_relationships "
                "SET lifecycle_state = :state, state_entered_at = :at, updated_at = :at "
                "WHERE id = :id"
            ),
            {"id": relationship_id, "state": to_state.value, "at": now},
        )

        return StateTransition(
            from_state=from_state,
            to_state=to_state,
            transitioned_at=now,
            reason=reason,
            evidence=evidence,
        )

    def store_consistency_score(self, score: ConsistencyScore) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO we_consistency_scores (
                    entity_id, assessment_id, overall_consistency,
                    signal_pair_scores, cross_group_scores,
                    cross_layer_divergence, divergent_pairs, computed_at
                ) VALUES (
                    :eid, :aid, :overall,
                    CAST(:sp AS jsonb), CAST(:cg AS jsonb),
                    CAST(:cld AS jsonb), CAST(:dp AS jsonb), :at
                )
                """
            ),
            {
                "eid": score.entity_id,
                "aid": score.assessment_id,
                "overall": score.overall_consistency,
                "sp": _json(score.signal_pair_scores),
                "cg": _json(score.cross_group_scores),
                "cld": _json(score.cross_layer_divergence),
                "dp": _json(score.divergent_pairs),
                "at": score.computed_at,
            },
        )

    def store_caf(self, caf: CausalAdjustmentFactor) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO we_causal_adjustments (
                    entity_id, assessment_id, caf_value, confidence,
                    active_precursors, trajectory, relationships_evaluated,
                    constrained, raw_caf, constraint_regime, computed_at
                ) VALUES (
                    :eid, :aid, :caf, :conf,
                    CAST(:prec AS jsonb), CAST(:traj AS jsonb), :n,
                    :cnst, :raw, :regime, :at
                )
                """
            ),
            {
                "eid": caf.entity_id,
                "aid": caf.assessment_id,
                "caf": caf.caf_value,
                "conf": caf.confidence,
                "prec": _json([p.model_dump() for p in caf.active_precursors]),
                "traj": _json(caf.trajectory.model_dump()),
                "n": caf.relationships_evaluated,
                "cnst": caf.constrained,
                "raw": caf.raw_caf,
                "regime": caf.constraint_regime,
                "at": caf.computed_at,
            },
        )

    def store_concentration(self, concentration: PortfolioConcentration) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO we_portfolio_concentrations (
                    entity_id, dimension, detail, severity,
                    affected_entities, computed_at
                ) VALUES (
                    :eid, :dim, :detail, :sev, CAST(:aff AS jsonb), :at
                )
                """
            ),
            {
                "eid": concentration.entity_id,
                "dim": concentration.dimension,
                "detail": concentration.detail,
                "sev": concentration.severity,
                "aff": _json(concentration.affected_entities),
                "at": concentration.computed_at,
            },
        )

    def store_drift_alert(self, alert: DriftAlert) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO we_drift_alerts (
                    id, alert_type, severity, source_signal, target_signal,
                    relationship_id, description, evidence, detected_at,
                    acknowledged, acknowledged_at
                ) VALUES (
                    :id, :type, :sev, :src, :tgt,
                    :rel, :desc, CAST(:ev AS jsonb), :at,
                    :ack, :ackat
                )
                """
            ),
            {
                "id": alert.id or str(uuid.uuid4()),
                "type": alert.alert_type,
                "sev": alert.severity.value,
                "src": alert.source_signal,
                "tgt": alert.target_signal,
                "rel": alert.relationship_id,
                "desc": alert.description,
                "ev": _json(alert.evidence),
                "at": alert.detected_at,
                "ack": alert.acknowledged,
                "ackat": alert.acknowledged_at,
            },
        )

    def store_scan_run(self, report: ScanRunReport) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO we_scan_runs (
                    run_id, started_at, completed_at, maturity_stage,
                    entities_scanned, pairs_tested, candidates_found,
                    candidates_after_inference, candidates_after_confound,
                    candidates_after_holdout, new_registrations,
                    drift_alerts_raised, stats, errors
                ) VALUES (
                    :rid, :st, :ct, :ms,
                    :ent, :pt, :cf,
                    :cai, :cac, :cah, :nr,
                    :da, CAST(:stats AS jsonb), CAST(:errs AS jsonb)
                )
                """
            ),
            {
                "rid": report.run_id,
                "st": report.started_at,
                "ct": report.completed_at,
                "ms": report.maturity_stage.value,
                "ent": report.entities_scanned,
                "pt": report.pairs_tested,
                "cf": report.candidates_found,
                "cai": report.candidates_after_inference,
                "cac": report.candidates_after_confound,
                "cah": report.candidates_after_holdout,
                "nr": report.new_registrations,
                "da": report.drift_alerts_raised,
                "stats": _json(
                    {"transitions": [t.model_dump(mode="json") for t in report.state_transitions]}
                ),
                "errs": _json(report.errors),
            },
        )

    def acknowledge_drift_alert(self, alert_id: str) -> Optional[datetime]:
        """Mark a drift alert as acknowledged. Returns the ack timestamp or None if not found."""
        now = datetime.now(timezone.utc)
        result = self.db.execute(
            text(
                "UPDATE we_drift_alerts "
                "SET acknowledged = true, acknowledged_at = :at "
                "WHERE id = :id AND acknowledged = false"
            ),
            {"id": alert_id, "at": now},
        )
        return now if result.rowcount else None

    # ==================================================================
    # Internal helpers
    # ==================================================================

    def _load_state_history(self, relationship_id: str) -> list[StateTransition]:
        rows = self.db.execute(
            text(
                "SELECT from_state, to_state, transitioned_at, reason, evidence "
                "FROM we_state_transitions WHERE relationship_id = :id "
                "ORDER BY transitioned_at ASC"
            ),
            {"id": relationship_id},
        ).mappings().all()
        return [
            StateTransition(
                from_state=LifecycleState(r["from_state"]),
                to_state=LifecycleState(r["to_state"]),
                transitioned_at=r["transitioned_at"],
                reason=r["reason"],
                evidence=r["evidence"] or {},
            )
            for r in rows
        ]

    def _row_to_relationship(self, row) -> DiscoveredRelationship:
        from world_engine.types import CausalDirection

        return DiscoveredRelationship(
            id=str(row["id"]),
            source_signal=row["source_signal"],
            target_signal=row["target_signal"],
            direction=CausalDirection(row["direction"]),
            lag_months=row["lag_months"],
            correlation_rho=row["correlation_rho"],
            granger_f_statistic=row["granger_f_statistic"],
            granger_p_value=row["granger_p_value"],
            effect_size=row["effect_size"],
            confounders_tested=row["confounders_tested"] or [],
            holdout_rho=row["holdout_rho"],
            holdout_p_value=row["holdout_p_value"],
            predictive_hit_rate=row["predictive_hit_rate"],
            population_size=row["population_size"],
            coverage_scope=row["coverage_scope"] or [],
            lifecycle_state=LifecycleState(row["lifecycle_state"]),
            state_entered_at=row["state_entered_at"],
            state_history=[],
            influence_weight=row["influence_weight"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_caf(self, row) -> CausalAdjustmentFactor:
        from world_engine.types import PrecursorEvaluation, TierMigrationDistribution

        traj_data = row["trajectory"] or {}
        trajectory = TierMigrationDistribution(
            current_tier=traj_data.get("current_tier", 0),
            probabilities={int(k): v for k, v in (traj_data.get("probabilities") or {}).items()},
            expected_tier=traj_data.get("expected_tier", 0.0),
            policy_period_months=traj_data.get("policy_period_months", 12),
        )
        precursors = [
            PrecursorEvaluation(**p) for p in (row["active_precursors"] or [])
        ]
        return CausalAdjustmentFactor(
            entity_id=row["entity_id"],
            assessment_id=row["assessment_id"],
            caf_value=row["caf_value"],
            confidence=row["confidence"],
            active_precursors=precursors,
            trajectory=trajectory,
            relationships_evaluated=row["relationships_evaluated"],
            constrained=row["constrained"],
            raw_caf=row["raw_caf"],
            constraint_regime=row["constraint_regime"],
            computed_at=row["computed_at"],
        )

    def _row_to_drift(self, row) -> DriftAlert:
        return DriftAlert(
            id=str(row["id"]),
            alert_type=row["alert_type"],
            severity=DriftSeverity(row["severity"]),
            source_signal=row["source_signal"],
            target_signal=row["target_signal"],
            relationship_id=str(row["relationship_id"]) if row["relationship_id"] else None,
            description=row["description"],
            evidence=row["evidence"] or {},
            detected_at=row["detected_at"],
            acknowledged=row["acknowledged"],
            acknowledged_at=row["acknowledged_at"],
        )


def _json(value) -> str:
    """Serialise a value to JSON text for CAST(:param AS jsonb) parameter binding."""
    import json

    def default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if hasattr(o, "model_dump"):
            return o.model_dump(mode="json")
        if hasattr(o, "value"):  # Enum
            return o.value
        raise TypeError(f"Cannot serialise {type(o)}")

    return json.dumps(value, default=default)
