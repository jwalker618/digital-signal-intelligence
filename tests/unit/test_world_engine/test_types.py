"""WE-1 type system tests."""

from datetime import datetime, timezone

import pytest

from world_engine.types import (
    CausalAdjustmentFactor,
    CausalDirection,
    ConsistencyScore,
    DiscoveredRelationship,
    DriftAlert,
    DriftSeverity,
    LifecycleState,
    MaturityStage,
    MaturityState,
    PortfolioConcentration,
    PrecursorEvaluation,
    StateTransition,
    TierMigrationDistribution,
)


class TestEnums:
    def test_maturity_stage_values(self):
        assert MaturityStage("seed") == MaturityStage.SEED
        assert MaturityStage("learn") == MaturityStage.LEARN
        assert MaturityStage("emerge") == MaturityStage.EMERGE
        assert MaturityStage("simulate") == MaturityStage.SIMULATE

    def test_lifecycle_state_values(self):
        for v in ("candidate", "provisional", "active", "deprecated"):
            assert LifecycleState(v).value == v

    def test_causal_direction_values(self):
        for v in ("a_causes_b", "b_causes_a", "bidirectional", "contemporaneous"):
            assert CausalDirection(v).value == v

    def test_drift_severity_values(self):
        for v in ("info", "warning", "critical"):
            assert DriftSeverity(v).value == v


class TestCausalAdjustmentFactor:
    def test_neutral_factory(self):
        caf = CausalAdjustmentFactor.neutral(
            entity_id="e1", assessment_id="a1", current_tier=2
        )
        assert caf.caf_value == 1.0
        assert caf.confidence == 0.0
        assert caf.relationships_evaluated == 0
        assert caf.constrained is False
        assert caf.constraint_regime == "neutral"
        assert caf.trajectory.current_tier == 2
        assert caf.trajectory.probabilities == {2: 1.0}

    def test_round_trip_serialisation(self):
        """Ensure the CAF type survives JSON round-trip (needed for DB storage)."""
        caf = CausalAdjustmentFactor(
            entity_id="e1",
            assessment_id="a1",
            caf_value=1.18,
            confidence=0.74,
            active_precursors=[
                PrecursorEvaluation(
                    relationship_id="r1",
                    precursor_signal="sig_a",
                    entity_value=0.82,
                    threshold=0.70,
                    distance_from_threshold=0.12,
                    implied_probability=0.65,
                    lag_months=9.0,
                )
            ],
            trajectory=TierMigrationDistribution(
                current_tier=2,
                probabilities={1: 0.02, 2: 0.65, 3: 0.25, 4: 0.08},
                expected_tier=2.39,
                policy_period_months=12,
            ),
            relationships_evaluated=3,
            constrained=False,
            raw_caf=1.18,
            constraint_regime="initial",
            computed_at=datetime.now(timezone.utc),
        )
        serialised = caf.model_dump(mode="json")
        restored = CausalAdjustmentFactor(**serialised)
        assert restored.caf_value == 1.18
        assert len(restored.active_precursors) == 1
        assert restored.trajectory.expected_tier == pytest.approx(2.39)


class TestDiscoveredRelationship:
    def test_influence_weight_bounds(self):
        with pytest.raises(Exception):
            DiscoveredRelationship(
                id="r1",
                source_signal="a",
                target_signal="b",
                direction=CausalDirection.A_CAUSES_B,
                correlation_rho=0.5,
                effect_size=0.3,
                population_size=100,
                lifecycle_state=LifecycleState.CANDIDATE,
                state_entered_at=datetime.now(timezone.utc),
                influence_weight=1.5,  # out of bounds
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )


class TestDriftAlert:
    def test_drift_alert_defaults(self):
        alert = DriftAlert(
            id="d1",
            alert_type="regime_change",
            severity=DriftSeverity.WARNING,
            description="Test drift",
            detected_at=datetime.now(timezone.utc),
        )
        assert alert.acknowledged is False
        assert alert.acknowledged_at is None
        assert alert.source_signal is None


class TestConsistencyScore:
    def test_overall_consistency_bounds(self):
        with pytest.raises(Exception):
            ConsistencyScore(
                entity_id="e1",
                assessment_id="a1",
                overall_consistency=1.5,  # out of bounds
                computed_at=datetime.now(timezone.utc),
            )

    def test_valid_score(self):
        score = ConsistencyScore(
            entity_id="e1",
            assessment_id="a1",
            overall_consistency=0.85,
            signal_pair_scores={"sig_a|sig_b": 0.9},
            cross_layer_divergence={"risk_vs_loss": 0.15},
            computed_at=datetime.now(timezone.utc),
        )
        assert score.overall_consistency == 0.85
        assert "sig_a|sig_b" in score.signal_pair_scores


class TestPortfolioConcentration:
    def test_valid_concentration(self):
        conc = PortfolioConcentration(
            entity_id="commercial_1",
            dimension="node",
            detail="47 entities share AWS us-east-1",
            severity=0.75,
            affected_entities=[f"e{i}" for i in range(47)],
            computed_at=datetime.now(timezone.utc),
        )
        assert conc.dimension == "node"
        assert len(conc.affected_entities) == 47


class TestStateTransition:
    def test_transition_fields(self):
        t = StateTransition(
            from_state=LifecycleState.CANDIDATE,
            to_state=LifecycleState.PROVISIONAL,
            transitioned_at=datetime.now(timezone.utc),
            reason="Holdout validation passed",
            evidence={"holdout_rho": 0.35, "holdout_p": 0.001},
        )
        assert t.from_state == LifecycleState.CANDIDATE
        assert t.to_state == LifecycleState.PROVISIONAL
        assert t.evidence["holdout_rho"] == 0.35
