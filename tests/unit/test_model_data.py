"""
Unit tests for ModelDataManager.

Tests model creation, version tracking, and update operations.
"""

import pytest
from datetime import datetime

from technical_pricing.model.model_data import ModelDataManager
from technical_pricing.model.types import (
    ModelVersion,
    SignalOutput,
    ScoringResult,
    QueryEvaluationResult,
    PricingResult,
    ModifierApplication,
    VersionType,
    DecisionType,
    PremiumMethod,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def data_manager():
    """Create a fresh ModelDataManager."""
    return ModelDataManager()


@pytest.fixture
def sample_model(data_manager):
    """Create a sample model and return model_id."""
    return data_manager.create_model(
        entity_id="test-entity-001",
        coverage="aerospace",
        config_hash="abc123hash",
        user="test_user"
    )


@pytest.fixture
def sample_version(data_manager, sample_model):
    """Create a sample initial version."""
    return data_manager.create_initial_version(
        model_id=sample_model,
        entity_id="test-entity-001",
        submission_data={"tiv": 10000000, "revenue": 50000000},
        direct_query_responses={"pending_claims": False},
        categorical_selections={"operator_type": "major_airline"},
        config_hash="abc123hash",
        user="test_user"
    )


@pytest.fixture
def sample_scoring_result():
    """Create a sample scoring result for updates."""
    return ScoringResult(
        entity_id="test-entity-001",
        coverage="aerospace",
        signal_outputs=[
            SignalOutput(
                signal_id="sig-001",
                signal_name="safety_record",
                group_name="safety_signals",
                raw_score=85.0,
                confidence=0.95,
                signal_weight=0.5,
                group_weight=0.6,
                weighted_score=255.0,
                data_sources=["faa_registry", "incident_db"],
                extracted_at=datetime.utcnow()
            ),
            SignalOutput(
                signal_id="sig-002",
                signal_name="credit_rating",
                group_name="financial_signals",
                raw_score=70.0,
                confidence=0.90,
                signal_weight=1.0,
                group_weight=0.4,
                weighted_score=280.0,
                data_sources=["credit_agency"],
                extracted_at=datetime.utcnow()
            )
        ],
        group_scores={"safety_signals": 255.0, "financial_signals": 280.0},
        pure_composite_score=535.0,
        aggregate_confidence=0.92,
        signal_conditions_triggered=[],
        tier_overrides_from_signals=[],
        referrals_from_signals=[],
        notes_from_signals=["Good safety record observed"],
        extraction_started_at=datetime.utcnow()
    )


# =============================================================================
# MODEL CREATION TESTS
# =============================================================================

class TestModelCreation:
    """Tests for model creation operations."""

    def test_create_model_returns_id(self, data_manager):
        """Creating model should return a valid model ID."""
        model_id = data_manager.create_model(
            entity_id="test-entity",
            coverage="aerospace",
            config_hash="hash123",
            user="test_user"
        )

        assert isinstance(model_id, str)
        assert len(model_id) > 0

    def test_create_model_stores_metadata(self, data_manager):
        """Creating model should store metadata correctly."""
        model_id = data_manager.create_model(
            entity_id="test-entity",
            coverage="aerospace",
            config_hash="hash123",
            user="test_user"
        )

        model = data_manager.get_model(model_id)

        assert model is not None
        assert model["entity_id"] == "test-entity"
        assert model["coverage"] == "aerospace"
        assert model["config_hash"] == "hash123"
        assert model["created_by"] == "test_user"
        assert model["status"] == "created"

    def test_create_multiple_models_unique_ids(self, data_manager):
        """Each model should have a unique ID."""
        model_ids = [
            data_manager.create_model(
                entity_id=f"entity-{i}",
                coverage="aerospace",
                config_hash="hash123",
                user="test_user"
            )
            for i in range(5)
        ]

        assert len(set(model_ids)) == 5  # All unique


# =============================================================================
# VERSION CREATION TESTS
# =============================================================================

class TestVersionCreation:
    """Tests for version creation operations."""

    def test_create_initial_version(self, data_manager, sample_model):
        """Creating initial version should return ModelVersion."""
        version = data_manager.create_initial_version(
            model_id=sample_model,
            entity_id="test-entity",
            submission_data={"tiv": 10000000},
            direct_query_responses={},
            categorical_selections={},
            config_hash="hash123",
            user="test_user"
        )

        assert isinstance(version, ModelVersion)
        assert version.model_id == sample_model
        assert version.version_number == 1
        assert version.version_type == VersionType.INITIAL
        assert version.entity_id == "test-entity"

    def test_version_number_increments(self, data_manager, sample_model):
        """Version numbers should increment for same model."""
        v1 = data_manager.create_initial_version(
            model_id=sample_model,
            entity_id="test-entity",
            submission_data={},
            direct_query_responses={},
            categorical_selections={},
            config_hash="hash123",
            user="user1"
        )

        v2 = data_manager.create_referral_version(
            model_id=sample_model,
            reviewer="reviewer1"
        )

        assert v1.version_number == 1
        assert v2.version_number == 2

    def test_create_referral_version_copies_data(self, data_manager, sample_version):
        """Referral version should copy data from latest version."""
        # Update original version with scoring
        sample_version.pure_composite_score = 750.0
        sample_version.final_tier = 2

        referral_version = data_manager.create_referral_version(
            model_id=sample_version.model_id,
            reviewer="reviewer1"
        )

        assert referral_version.version_type == VersionType.REFERRAL_REVIEW
        assert referral_version.entity_id == sample_version.entity_id
        assert referral_version.submission_data == sample_version.submission_data

    def test_create_referral_version_applies_adjustments(self, data_manager, sample_version):
        """Referral version should apply adjustments."""
        referral_version = data_manager.create_referral_version(
            model_id=sample_version.model_id,
            reviewer="reviewer1",
            adjustments={
                "final_tier": 2,
                "decision": "approve",
                "notes": ["Approved after review"]
            }
        )

        assert referral_version.final_tier == 2
        assert referral_version.decision == DecisionType.APPROVE
        assert "Approved after review" in referral_version.notes

    def test_create_amendment_version_merges_data(self, data_manager, sample_version):
        """Amendment version should merge new data with existing."""
        amendment = data_manager.create_amendment_version(
            model_id=sample_version.model_id,
            user="user2",
            amendments={
                "submission_data": {"tiv": 15000000},  # Updated TIV
                "direct_query_responses": {"new_query": True}
            }
        )

        assert amendment.version_type == VersionType.AMENDMENT
        assert amendment.submission_data["tiv"] == 15000000
        assert amendment.submission_data["revenue"] == 50000000  # Preserved
        assert amendment.direct_query_responses["new_query"] is True

    def test_create_version_for_invalid_model_raises(self, data_manager):
        """Creating version for non-existent model should raise."""
        with pytest.raises(ValueError, match="Model not found"):
            data_manager.create_initial_version(
                model_id="invalid-model-id",
                entity_id="test",
                submission_data={},
                direct_query_responses={},
                categorical_selections={},
                config_hash="hash",
                user="user"
            )


# =============================================================================
# VERSION UPDATE TESTS
# =============================================================================

class TestVersionUpdates:
    """Tests for version update operations."""

    def test_update_version_scoring(self, data_manager, sample_version, sample_scoring_result):
        """Should update version with scoring results."""
        updated = data_manager.update_version_scoring(
            version_id=sample_version.version_id,
            scoring_result=sample_scoring_result
        )

        assert len(updated.signal_outputs) == 2
        assert updated.pure_composite_score == 535.0
        assert updated.aggregate_confidence == 0.92
        assert updated.group_scores["safety_signals"] == 255.0
        assert "Good safety record observed" in updated.notes

    def test_update_version_queries(self, data_manager, sample_version):
        """Should update version with query results."""
        query_result = QueryEvaluationResult(
            tier_overrides=[4],
            referrals=["Pending claims require review"],
            notes=["Query note"],
            modifiers=[{"name": "risk_modifier", "factor": 1.15}],
            queries_evaluated=[{"id": "pending_claims", "response": True}]
        )

        updated = data_manager.update_version_queries(
            version_id=sample_version.version_id,
            query_result=query_result
        )

        assert 4 in updated.tier_overrides
        assert "Pending claims require review" in updated.referral_reasons
        assert "Query note" in updated.notes

    def test_update_version_pricing(self, data_manager, sample_version):
        """Should update version with pricing results."""
        pricing_result = PricingResult(
            score_based_tier=2,
            tier_overrides_considered=[],
            final_tier=2,
            base_premium=35000.0,
            base_premium_method=PremiumMethod.PURE,
            modifiers_applied=[
                ModifierApplication(
                    name="operator_type:major_airline",
                    factor=0.85,
                    premium_before=35000.0,
                    premium_after=29750.0,
                    source="categorical"
                )
            ],
            premium_after_modifiers=29750.0,
            limit_premiums={1000000: 29750.0, 5000000: 74375.0}
        )

        updated = data_manager.update_version_pricing(
            version_id=sample_version.version_id,
            pricing_result=pricing_result
        )

        assert updated.score_based_tier == 2
        assert updated.final_tier == 2
        assert updated.base_premium == 35000.0
        assert len(updated.modifiers_applied) == 1
        assert updated.limit_premiums[1000000] == 29750.0

    def test_update_version_decision(self, data_manager, sample_version):
        """Should update version with decision."""
        updated = data_manager.update_version_decision(
            version_id=sample_version.version_id,
            decision=DecisionType.APPROVE,
            auto_approve=True,
            referral_reasons=[],
            notes=["Auto-approved"]
        )

        assert updated.decision == DecisionType.APPROVE
        assert updated.auto_approve is True
        assert "Auto-approved" in updated.notes

    def test_update_invalid_version_raises(self, data_manager):
        """Updating non-existent version should raise."""
        with pytest.raises(ValueError, match="Version not found"):
            data_manager.update_version_decision(
                version_id="invalid-version-id",
                decision=DecisionType.APPROVE,
                auto_approve=True
            )


# =============================================================================
# RETRIEVAL TESTS
# =============================================================================

class TestVersionRetrieval:
    """Tests for version retrieval operations."""

    def test_get_version_by_id(self, data_manager, sample_version):
        """Should retrieve version by ID."""
        retrieved = data_manager.get_version(sample_version.version_id)

        assert retrieved is not None
        assert retrieved.version_id == sample_version.version_id

    def test_get_latest_version(self, data_manager, sample_model):
        """Should return most recent version."""
        v1 = data_manager.create_initial_version(
            model_id=sample_model,
            entity_id="test",
            submission_data={},
            direct_query_responses={},
            categorical_selections={},
            config_hash="hash",
            user="user"
        )
        v2 = data_manager.create_referral_version(
            model_id=sample_model,
            reviewer="reviewer"
        )

        latest = data_manager.get_latest_version(sample_model)

        assert latest.version_id == v2.version_id
        assert latest.version_number == 2

    def test_get_version_history(self, data_manager, sample_model):
        """Should return all versions in order."""
        v1 = data_manager.create_initial_version(
            model_id=sample_model,
            entity_id="test",
            submission_data={},
            direct_query_responses={},
            categorical_selections={},
            config_hash="hash",
            user="user"
        )
        v2 = data_manager.create_referral_version(
            model_id=sample_model,
            reviewer="reviewer1"
        )
        v3 = data_manager.create_referral_version(
            model_id=sample_model,
            reviewer="reviewer2"
        )

        history = data_manager.get_version_history(sample_model)

        assert len(history) == 3
        assert history[0].version_number == 1
        assert history[1].version_number == 2
        assert history[2].version_number == 3

    def test_get_nonexistent_version(self, data_manager):
        """Should return None for non-existent version."""
        result = data_manager.get_version("nonexistent")
        assert result is None

    def test_get_latest_version_no_versions(self, data_manager, sample_model):
        """Should return None when no versions exist."""
        # Don't create any versions
        result = data_manager.get_latest_version(sample_model)
        assert result is None


# =============================================================================
# SEARCH TESTS
# =============================================================================

class TestModelSearch:
    """Tests for model search operations."""

    def test_find_models_by_entity(self, data_manager):
        """Should find all models for an entity."""
        # Create models for different entities
        data_manager.create_model("entity-a", "aerospace", "hash1", "user")
        data_manager.create_model("entity-a", "cyber", "hash2", "user")
        data_manager.create_model("entity-b", "aerospace", "hash3", "user")

        models = data_manager.find_models_by_entity("entity-a")

        assert len(models) == 2
        assert all(m["entity_id"] == "entity-a" for m in models)

    def test_find_models_by_coverage(self, data_manager):
        """Should find all models for a coverage."""
        data_manager.create_model("entity-a", "aerospace", "hash1", "user")
        data_manager.create_model("entity-b", "aerospace", "hash2", "user")
        data_manager.create_model("entity-c", "cyber", "hash3", "user")

        models = data_manager.find_models_by_coverage("aerospace")

        assert len(models) == 2
        assert all(m["coverage"] == "aerospace" for m in models)

    def test_find_pending_referrals(self, data_manager, sample_model):
        """Should find versions pending referral review."""
        version = data_manager.create_initial_version(
            model_id=sample_model,
            entity_id="test",
            submission_data={},
            direct_query_responses={},
            categorical_selections={},
            config_hash="hash",
            user="user"
        )

        data_manager.update_version_decision(
            version_id=version.version_id,
            decision=DecisionType.REFER,
            auto_approve=False,
            referral_reasons=["High risk"]
        )

        pending = data_manager.find_pending_referrals()

        assert len(pending) == 1
        assert pending[0].decision == DecisionType.REFER


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================

class TestVersionSerialization:
    """Tests for version serialization/deserialization."""

    def test_version_to_dict(self, data_manager, sample_version, sample_scoring_result):
        """Should serialize version to dictionary."""
        data_manager.update_version_scoring(
            version_id=sample_version.version_id,
            scoring_result=sample_scoring_result
        )

        version_dict = data_manager.version_to_dict(sample_version)

        assert isinstance(version_dict, dict)
        assert version_dict["version_id"] == sample_version.version_id
        assert version_dict["version_type"] == "initial"
        assert version_dict["pure_composite_score"] == 535.0
        assert len(version_dict["signal_outputs"]) == 2

    def test_version_from_dict(self, data_manager, sample_version, sample_scoring_result):
        """Should deserialize version from dictionary."""
        data_manager.update_version_scoring(
            version_id=sample_version.version_id,
            scoring_result=sample_scoring_result
        )

        version_dict = data_manager.version_to_dict(sample_version)
        reconstructed = data_manager.version_from_dict(version_dict)

        assert isinstance(reconstructed, ModelVersion)
        assert reconstructed.version_id == sample_version.version_id
        assert reconstructed.version_type == VersionType.INITIAL
        assert reconstructed.pure_composite_score == 535.0
        assert len(reconstructed.signal_outputs) == 2

    def test_roundtrip_serialization(self, data_manager, sample_version, sample_scoring_result):
        """Serialization roundtrip should preserve data."""
        data_manager.update_version_scoring(
            version_id=sample_version.version_id,
            scoring_result=sample_scoring_result
        )
        data_manager.update_version_decision(
            version_id=sample_version.version_id,
            decision=DecisionType.APPROVE,
            auto_approve=True
        )

        version_dict = data_manager.version_to_dict(sample_version)
        reconstructed = data_manager.version_from_dict(version_dict)

        assert reconstructed.decision == sample_version.decision
        assert reconstructed.auto_approve == sample_version.auto_approve
        assert reconstructed.pure_composite_score == sample_version.pure_composite_score
