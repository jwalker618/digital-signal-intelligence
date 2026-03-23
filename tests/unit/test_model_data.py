"""
Unit tests for ModelDataManager.

Tests model creation, version tracking, and update operations.
"""

import pytest
from unittest.mock import MagicMock

from layers.risk.model_data import ModelDataManager, ModelNotFoundError, VersionNotFoundError
from layers.risk.types import (
    ModelVersion,
    SignalOutput,
    DecisionType,
    utcnow,
)


# =============================================================================
# HELPERS
# =============================================================================

def _mock_config(coverage_id="aerospace", config_id="aerospace_general"):
    """Create a mock CoverageConfig for testing."""
    config = MagicMock()
    config.coverage_id = coverage_id
    config.config_id = config_id
    config.config_hash = "test-hash"
    return config


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
        config=_mock_config(),
        submission_data={"tiv": 10000000, "revenue": 50000000},
        user="test_user",
    )


@pytest.fixture
def sample_version(data_manager, sample_model):
    """Create a sample initial version."""
    return data_manager.create_version(
        model_id=sample_model,
        version_type="initial",
        user="test_user",
        submission_data={"tiv": 10000000, "revenue": 50000000},
        direct_query_responses={"pending_claims": False},
        categorical_selections={"operator_type": "major_airline"},
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
            config=_mock_config(),
            user="test_user",
        )

        assert isinstance(model_id, str)
        assert len(model_id) > 0

    def test_create_model_stores_metadata(self, data_manager):
        """Creating model should store metadata correctly."""
        model_id = data_manager.create_model(
            entity_id="test-entity",
            config=_mock_config(),
            user="test_user",
        )

        model = data_manager.get_model(model_id)

        assert model is not None
        assert model["entity_id"] == "test-entity"
        assert model["coverage"] == "aerospace"
        assert model["configuration"] == "aerospace_general"
        assert model["created_by"] == "test_user"

    def test_create_multiple_models_unique_ids(self, data_manager):
        """Each model should have a unique ID."""
        model_ids = [
            data_manager.create_model(
                entity_id=f"entity-{i}",
                config=_mock_config(),
                user="test_user",
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
        version = data_manager.create_version(
            model_id=sample_model,
            version_type="initial",
            user="test_user",
            submission_data={"tiv": 10000000},
        )

        assert isinstance(version, ModelVersion)
        assert version.model_id == sample_model
        assert version.version_number == 1
        assert version.version_type == "initial"
        assert version.entity_id == "test-entity-001"

    def test_version_number_increments(self, data_manager, sample_model):
        """Version numbers should increment for same model."""
        v1 = data_manager.create_version(
            model_id=sample_model,
            version_type="initial",
            user="user1",
        )

        v2 = data_manager.create_version(
            model_id=sample_model,
            version_type="referral_review",
            user="reviewer1",
        )

        assert v1.version_number == 1
        assert v2.version_number == 2

    def test_create_referral_version(self, data_manager, sample_version):
        """Referral version should be created with correct type."""
        referral_version = data_manager.create_version(
            model_id=sample_version.model_id,
            version_type="referral_review",
            user="reviewer1",
            submission_data=sample_version.submission_data,
        )

        assert referral_version.version_type == "referral_review"
        assert referral_version.entity_id == sample_version.entity_id

    def test_create_amendment_version(self, data_manager, sample_version):
        """Amendment version should be created with correct type."""
        amendment = data_manager.create_version(
            model_id=sample_version.model_id,
            version_type="amendment",
            user="user2",
            submission_data={"tiv": 15000000},
        )

        assert amendment.version_type == "amendment"
        assert amendment.submission_data["tiv"] == 15000000

    def test_create_version_for_invalid_model_raises(self, data_manager):
        """Creating version for non-existent model should raise."""
        with pytest.raises(ModelNotFoundError):
            data_manager.create_version(
                model_id="invalid-model-id",
                version_type="initial",
                user="user",
            )


# =============================================================================
# VERSION UPDATE TESTS
# =============================================================================

class TestVersionUpdates:
    """Tests for version update operations."""

    def test_update_version_scoring(self, data_manager, sample_version):
        """Should update version with scoring results."""
        updated = data_manager.update_version(
            version_id=sample_version.version_id,
            pure_composite_score=535.0,
            confidence=0.92,
            signal_outputs=[
                SignalOutput(
                    signal_id="sig-001",
                    signal_name="Safety Record",
                    group_id="safety_signals",
                    raw_score=85.0,
                    confidence=0.95,
                    weight=0.5,
                    weighted_score=42.5,
                ),
            ],
            group_scores={"safety_signals": {"risk_score": 85.0}},
        )

        assert updated.pure_composite_score == 535.0
        assert updated.confidence == 0.92
        assert len(updated.signal_outputs) == 1

    def test_update_version_pricing(self, data_manager, sample_version):
        """Should update version with pricing results."""
        updated = data_manager.update_version(
            version_id=sample_version.version_id,
            score_based_tier=2,
            final_tier=2,
            base_premium=35000.0,
            limit_premiums={1000000: 29750.0, 5000000: 74375.0},
        )

        assert updated.score_based_tier == 2
        assert updated.final_tier == 2
        assert updated.base_premium == 35000.0
        assert updated.limit_premiums[1000000] == 29750.0

    def test_update_version_decision(self, data_manager, sample_version):
        """Should update version with decision."""
        updated = data_manager.update_version(
            version_id=sample_version.version_id,
            decision=DecisionType.APPROVE,
            auto_approve=True,
            notes=["Auto-approved"],
        )

        assert updated.decision == DecisionType.APPROVE
        assert updated.auto_approve is True
        assert "Auto-approved" in updated.notes

    def test_update_invalid_version_raises(self, data_manager):
        """Updating non-existent version should raise."""
        with pytest.raises(VersionNotFoundError):
            data_manager.update_version(
                version_id="invalid-version-id",
                decision=DecisionType.APPROVE,
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
        v1 = data_manager.create_version(
            model_id=sample_model,
            version_type="initial",
            user="user",
        )
        v2 = data_manager.create_version(
            model_id=sample_model,
            version_type="referral_review",
            user="reviewer",
        )

        latest = data_manager.get_latest_version(sample_model)

        assert latest.version_id == v2.version_id
        assert latest.version_number == 2

    def test_get_version_history(self, data_manager, sample_model):
        """Should return all versions in order."""
        v1 = data_manager.create_version(
            model_id=sample_model,
            version_type="initial",
            user="user",
        )
        v2 = data_manager.create_version(
            model_id=sample_model,
            version_type="referral_review",
            user="reviewer1",
        )
        v3 = data_manager.create_version(
            model_id=sample_model,
            version_type="referral_review",
            user="reviewer2",
        )

        history = data_manager.get_version_history(sample_model)

        assert len(history) == 3
        assert history[0].version_number == 1
        assert history[1].version_number == 2
        assert history[2].version_number == 3

    def test_get_nonexistent_version(self, data_manager):
        """Should raise for non-existent version."""
        with pytest.raises(VersionNotFoundError):
            data_manager.get_version("nonexistent")

    def test_get_latest_version_no_versions(self, data_manager, sample_model):
        """Should raise when no versions exist."""
        with pytest.raises(VersionNotFoundError):
            data_manager.get_latest_version(sample_model)


# =============================================================================
# SEARCH TESTS
# =============================================================================

class TestModelSearch:
    """Tests for model search operations."""

    def test_find_models_for_entity(self, data_manager):
        """Should find all models for an entity."""
        data_manager.create_model("entity-a", _mock_config(), user="user")
        data_manager.create_model("entity-a", _mock_config(config_id="cyber_general"), user="user")
        data_manager.create_model("entity-b", _mock_config(), user="user")

        models = data_manager.find_models_for_entity("entity-a")

        assert len(models) == 2
