"""
World Engine: Maturity Evaluator (WE-1b)

Determines the current maturity stage of the World Engine based on population
size and time depth. Gates capability activation -- discovery, CAF computation,
portfolio simulation each require a minimum maturity stage.

See development/project/version/5/world_engine_phases/WE-1_Foundation.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from world_engine.types import MaturityStage, MaturityState


class MaturityEvaluator:
    """Determines the World Engine's current maturity stage.

    Usage:
        evaluator = MaturityEvaluator()
        state = evaluator.evaluate(db_session)
        if state.capabilities["discovery"]:
            ...  # run discovery pipeline
    """

    # Population and time depth thresholds per stage
    STAGE_THRESHOLDS: dict[MaturityStage, dict[str, int]] = {
        MaturityStage.SEED: {"min_entities": 0, "min_months": 0},
        MaturityStage.LEARN: {"min_entities": 500, "min_months": 6},
        MaturityStage.EMERGE: {"min_entities": 5000, "min_months": 18},
        MaturityStage.SIMULATE: {"min_entities": 50000, "min_months": 36},
    }

    # Capability gates per stage
    CAPABILITIES: dict[MaturityStage, dict[str, bool]] = {
        MaturityStage.SEED: {
            "consistency": True,
            "discovery": False,
            "caf": False,
            "portfolio_concentration": False,
            "simulation": False,
            "concentration_aware_caf": False,
        },
        MaturityStage.LEARN: {
            "consistency": True,
            "discovery": True,
            "caf": False,
            "portfolio_concentration": False,
            "simulation": False,
            "concentration_aware_caf": False,
        },
        MaturityStage.EMERGE: {
            "consistency": True,
            "discovery": True,
            "caf": True,
            "portfolio_concentration": True,
            "simulation": False,
            "concentration_aware_caf": False,
        },
        MaturityStage.SIMULATE: {
            "consistency": True,
            "discovery": True,
            "caf": True,
            "portfolio_concentration": True,
            "simulation": True,
            "concentration_aware_caf": True,
        },
    }

    def evaluate(self, db: Session) -> MaturityState:
        """Query assessment database and determine current maturity stage.

        Args:
            db: Synchronous SQLAlchemy session.

        Returns:
            MaturityState with current stage, population stats, and capability flags.
        """
        entity_count = self._count_assessed_entities(db)
        temporal_count = self._count_entities_with_temporal_data(db)
        earliest = self._earliest_assessment(db)
        time_depth = self._time_depth_months(earliest)

        # Relationship counts default to zero if the we_relationships table
        # doesn't exist yet (e.g. during migration bootstrap).
        active, provisional, candidate = self._count_relationships(db)

        stage = self._determine_stage(entity_count, time_depth)
        caps = self.CAPABILITIES[stage]

        return MaturityState(
            stage=stage,
            assessed_entity_count=entity_count,
            entities_with_temporal_data=temporal_count,
            earliest_assessment=earliest,
            time_depth_months=time_depth,
            active_relationships=active,
            provisional_relationships=provisional,
            candidate_relationships=candidate,
            capabilities=caps,
            evaluated_at=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _determine_stage(self, entity_count: int, time_depth_months: float) -> MaturityStage:
        """Return the highest stage whose thresholds are met."""
        # Walk stages from most advanced down, return the first one we qualify for.
        for stage in (MaturityStage.SIMULATE, MaturityStage.EMERGE, MaturityStage.LEARN):
            thresholds = self.STAGE_THRESHOLDS[stage]
            if (
                entity_count >= thresholds["min_entities"]
                and time_depth_months >= thresholds["min_months"]
            ):
                return stage
        return MaturityStage.SEED

    def _count_assessed_entities(self, db: Session) -> int:
        """Count distinct entities that have submissions.

        Entity identity = entity_name (the stable identifier on Submission).
        Returns 0 gracefully if the submissions table doesn't yet exist.
        """
        from infrastructure.db.models import Submission

        try:
            stmt = select(func.count(func.distinct(Submission.entity_name))).select_from(Submission)
            result = db.execute(stmt).scalar()
            return int(result or 0)
        except Exception:
            db.rollback()
            return 0

    def _count_entities_with_temporal_data(self, db: Session) -> int:
        """Count entities with >= 2 distinct model versions across their submissions.

        Required for discovery pipeline -- Granger causality needs time-series.
        Returns 0 gracefully if the relevant tables don't yet exist.
        """
        from infrastructure.db.models import ModelVersionRecord, Submission

        try:
            subq = (
                select(Submission.entity_name, func.count(ModelVersionRecord.id).label("n"))
                .select_from(Submission)
                .join(ModelVersionRecord, ModelVersionRecord.submission_id == Submission.id)
                .group_by(Submission.entity_name)
                .having(func.count(ModelVersionRecord.id) >= 2)
                .subquery()
            )
            stmt = select(func.count()).select_from(subq)
            result = db.execute(stmt).scalar()
            return int(result or 0)
        except Exception:
            db.rollback()
            return 0

    def _earliest_assessment(self, db: Session) -> Optional[datetime]:
        """Return timestamp of earliest model version, or None if no data.

        Returns None gracefully if the model_versions table doesn't exist.
        """
        from infrastructure.db.models import ModelVersionRecord

        try:
            stmt = select(func.min(ModelVersionRecord.created_at))
            return db.execute(stmt).scalar()
        except Exception:
            db.rollback()
            return None

    def _time_depth_months(self, earliest: Optional[datetime]) -> float:
        """Compute months between earliest assessment and now."""
        if earliest is None:
            return 0.0
        now = datetime.now(timezone.utc)
        # Normalise tz: earliest may be naive if inserted without tz.
        if earliest.tzinfo is None:
            earliest = earliest.replace(tzinfo=timezone.utc)
        delta = now - earliest
        return delta.days / 30.0

    def _count_relationships(self, db: Session) -> tuple[int, int, int]:
        """Return (active, provisional, candidate) relationship counts.

        Returns (0, 0, 0) if the we_relationships table does not yet exist
        (e.g. before migration 011 is applied).
        """
        try:
            from sqlalchemy import text

            active = db.execute(
                text("SELECT COUNT(*) FROM we_relationships WHERE lifecycle_state = 'active'")
            ).scalar()
            provisional = db.execute(
                text("SELECT COUNT(*) FROM we_relationships WHERE lifecycle_state = 'provisional'")
            ).scalar()
            candidate = db.execute(
                text("SELECT COUNT(*) FROM we_relationships WHERE lifecycle_state = 'candidate'")
            ).scalar()
            return int(active or 0), int(provisional or 0), int(candidate or 0)
        except Exception:
            # Table doesn't exist yet or query failed -- treat as empty registry.
            db.rollback()
            return 0, 0, 0
