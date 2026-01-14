"""
Unit tests for ConfigManager.

Tests configuration hashing, storage, loading, and validation.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from layers.risk.config_manager import ConfigManager
from layers.risk.types import (
    CoverageConfig,
    ConfigVersion,
    SignalGroupConfig,
    SignalConfig,
    TierConfig,
    DirectQueryConfig,
    LimitBand,
    DecisionType,
    ConditionAction,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def config_manager():
    """Create a ConfigManager with a temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield ConfigManager(config_dir=tmpdir)


@pytest.fixture
def sample_yaml_content():
    """Sample YAML configuration for testing."""
    return """
aerospace:
  aerospace_general:
    metadata:
      name: "Test Aerospace Model"
      version: "1.0.0"
      min_premium: 25000

    required_inputs:
      - entity_id
      - tiv

    direct_queries:
      - id: "pending_claims"
        question: "Are there any pending claims?"
        impacts:
          - type: referral
            value: "Pending claims require review"
            trigger_on: true

    categorical_groups:
      - operator_type

    categorical_features:
      operator_type:
        major_airline: 0.85
        regional_airline: 1.00

    signal_groups:
      - name: safety_signals
        weight: 0.6
        conditions: []
      - name: financial_signals
        weight: 0.4
        conditions: []

    signal_features:
      safety_signals:
        - name: safety_record
          weight: 0.5
          inference_function: infer_safety_record
          categorizer_type: threshold_bucket
          categorizer_params:
            thresholds: [20, 40, 60, 80]
            scores: [20, 40, 60, 80, 100]
          conditions: []
        - name: incident_history
          weight: 0.5
          inference_function: infer_incident_history
          categorizer_type: threshold_bucket
          categorizer_params:
            thresholds: [20, 40, 60, 80]
            scores: [20, 40, 60, 80, 100]
          conditions: []
      financial_signals:
        - name: credit_rating
          weight: 1.0
          inference_function: infer_credit_rating
          categorizer_type: category_mapper
          categorizer_params:
            mapping:
              AAA: 100
              AA: 85
              A: 70
              BBB: 55
              BB: 40
          conditions: []

    tier_thresholds:
      - tier: 1
        min_score: 800
        max_score: 1000
        base_premium: 25000
        decision: approve
      - tier: 2
        min_score: 600
        max_score: 799
        base_premium: 35000
        decision: approve
      - tier: 3
        min_score: 400
        max_score: 599
        base_premium: 50000
        decision: refer
      - tier: 4
        min_score: 200
        max_score: 399
        base_premium: 75000
        decision: refer
      - tier: 5
        min_score: 0
        max_score: 199
        base_premium: 100000
        decision: decline

    limit_bands:
      - limit: 1000000
        ilf: 1.0
      - limit: 5000000
        ilf: 2.5
      - limit: 10000000
        ilf: 4.0

    deductible_credits:
      10000: 1.0
      25000: 0.95
      50000: 0.90
"""


# =============================================================================
# HASH GENERATION TESTS
# =============================================================================

class TestConfigHashing:
    """Tests for configuration hash generation."""

    def test_hash_generates_sha256(self, config_manager, sample_yaml_content):
        """Hash should be a valid SHA-256 hex string."""
        config_hash = config_manager.hash_config(sample_yaml_content)

        assert isinstance(config_hash, str)
        assert len(config_hash) == 64  # SHA-256 produces 64 hex chars
        assert all(c in '0123456789abcdef' for c in config_hash)

    def test_same_content_same_hash(self, config_manager, sample_yaml_content):
        """Identical content should produce identical hash."""
        hash1 = config_manager.hash_config(sample_yaml_content)
        hash2 = config_manager.hash_config(sample_yaml_content)

        assert hash1 == hash2

    def test_different_content_different_hash(self, config_manager, sample_yaml_content):
        """Different content should produce different hash."""
        hash1 = config_manager.hash_config(sample_yaml_content)
        hash2 = config_manager.hash_config(sample_yaml_content + " ")  # Single space change

        assert hash1 != hash2

    def test_hash_is_deterministic(self, config_manager):
        """Hash function should be deterministic across calls."""
        content = "test: value"
        hashes = [config_manager.hash_config(content) for _ in range(10)]

        assert len(set(hashes)) == 1  # All hashes should be identical


# =============================================================================
# STORAGE TESTS
# =============================================================================

class TestConfigStorage:
    """Tests for configuration storage operations."""

    def test_store_config_returns_version(self, config_manager, sample_yaml_content):
        """Storing config should return a ConfigVersion object."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )

        assert isinstance(version, ConfigVersion)
        assert version.coverage == "aerospace"
        assert version.configuration == "aerospace_general"
        assert version.created_by == "test_user"
        assert version.is_active is False

    def test_store_same_content_uses_same_hash(self, config_manager, sample_yaml_content):
        """Storing same content twice should use same hash."""
        version1 = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="v1",
            user="user1"
        )
        version2 = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="v2",
            user="user2"
        )

        assert version1.config_hash == version2.config_hash
        assert version1.version_id != version2.version_id

    def test_activate_config_sets_active(self, config_manager, sample_yaml_content):
        """Activating config should set is_active to True."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="test",
            user="test_user"
        )

        assert version.is_active is False

        config_manager.activate_config(version.version_id)

        assert version.is_active is True

    def test_activate_config_deactivates_previous(self, config_manager, sample_yaml_content):
        """Activating new config should deactivate previous active config."""
        version1 = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="v1",
            user="user1"
        )
        config_manager.activate_config(version1.version_id)
        assert version1.is_active is True

        version2 = config_manager.store_config(
            yaml_content=sample_yaml_content + "\n",
            coverage="aerospace",
            configuration="v2",
            user="user2"
        )
        config_manager.activate_config(version2.version_id)

        assert version1.is_active is False
        assert version2.is_active is True

    def test_activate_invalid_version_raises(self, config_manager):
        """Activating non-existent version should raise ValueError."""
        with pytest.raises(ValueError, match="Version not found"):
            config_manager.activate_config("invalid-version-id")


# =============================================================================
# LOADING TESTS
# =============================================================================

class TestConfigLoading:
    """Tests for configuration loading operations."""

    def test_load_by_hash(self, config_manager, sample_yaml_content):
        """Should load config by hash."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="test",
            user="test_user"
        )

        config = config_manager.load_config(version.config_hash)

        assert isinstance(config, CoverageConfig)
        assert config.config_hash == version.config_hash

    def test_load_by_version_id(self, config_manager, sample_yaml_content):
        """Should load config by version ID."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="test",
            user="test_user"
        )

        config = config_manager.load_config_by_version(version.version_id)

        assert isinstance(config, CoverageConfig)

    def test_load_active_config(self, config_manager, sample_yaml_content):
        """Should load active config for coverage."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="test",
            user="test_user"
        )
        config_manager.activate_config(version.version_id)

        config = config_manager.get_active_config("aerospace")

        assert isinstance(config, CoverageConfig)

    def test_load_nonexistent_hash_raises(self, config_manager):
        """Loading non-existent hash should raise ValueError."""
        with pytest.raises(ValueError, match="Config hash not found"):
            config_manager.load_config("nonexistent-hash")

    def test_load_no_active_config_raises(self, config_manager):
        """Loading when no active config should raise ValueError."""
        with pytest.raises(ValueError, match="No active config"):
            config_manager.get_active_config("aerospace")


# =============================================================================
# PARSING TESTS
# =============================================================================

class TestConfigParsing:
    """Tests for YAML configuration parsing."""

    def test_parses_metadata(self, config_manager, sample_yaml_content):
        """Should parse metadata correctly."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )
        config = config_manager.load_config(version.config_hash)

        assert config.metadata["name"] == "Test Aerospace Model"
        assert config.metadata["version"] == "1.0.0"
        assert config.metadata["min_premium"] == 25000

    def test_parses_required_inputs(self, config_manager, sample_yaml_content):
        """Should parse required inputs correctly."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )
        config = config_manager.load_config(version.config_hash)

        assert "entity_id" in config.required_inputs
        assert "tiv" in config.required_inputs

    def test_parses_signal_groups(self, config_manager, sample_yaml_content):
        """Should parse signal groups correctly."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )
        config = config_manager.load_config(version.config_hash)

        assert len(config.signal_groups) == 2

        safety_group = next((g for g in config.signal_groups if g.name == "safety_signals"), None)
        assert safety_group is not None
        assert safety_group.weight == 0.6
        assert len(safety_group.signals) == 2

    def test_parses_tier_thresholds(self, config_manager, sample_yaml_content):
        """Should parse tier thresholds correctly."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )
        config = config_manager.load_config(version.config_hash)

        assert len(config.tier_thresholds) == 5

        tier1 = next((t for t in config.tier_thresholds if t.tier == 1), None)
        assert tier1 is not None
        assert tier1.min_score == 800
        assert tier1.max_score == 1000
        assert tier1.base_premium == 25000
        assert tier1.decision == DecisionType.APPROVE

    def test_parses_limit_bands(self, config_manager, sample_yaml_content):
        """Should parse limit bands correctly."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )
        config = config_manager.load_config(version.config_hash)

        assert len(config.limit_bands) == 3

        band1m = next((b for b in config.limit_bands if b.limit == 1000000), None)
        assert band1m is not None
        assert band1m.ilf == 1.0


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_valid_config(self, config_manager, sample_yaml_content):
        """Valid config should pass validation."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )
        config = config_manager.load_config(version.config_hash)

        errors = config_manager.validate_config(config)

        assert len(errors) == 0

    def test_verify_required_inputs_all_present(self, config_manager, sample_yaml_content):
        """Should pass when all required inputs present."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )
        config = config_manager.load_config(version.config_hash)

        submission_data = {"entity_id": "test-entity", "tiv": 10000000}
        is_valid, missing = config_manager.verify_required_inputs(config, submission_data)

        assert is_valid is True
        assert len(missing) == 0

    def test_verify_required_inputs_missing(self, config_manager, sample_yaml_content):
        """Should fail when required inputs missing."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )
        config = config_manager.load_config(version.config_hash)

        submission_data = {"entity_id": "test-entity"}  # Missing tiv
        is_valid, missing = config_manager.verify_required_inputs(config, submission_data)

        assert is_valid is False
        assert "tiv" in missing

    def test_verify_required_inputs_null_value(self, config_manager, sample_yaml_content):
        """Should fail when required input is null."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )
        config = config_manager.load_config(version.config_hash)

        submission_data = {"entity_id": "test-entity", "tiv": None}
        is_valid, missing = config_manager.verify_required_inputs(config, submission_data)

        assert is_valid is False
        assert "tiv" in missing


# =============================================================================
# VERSION HISTORY TESTS
# =============================================================================

class TestVersionHistory:
    """Tests for version history tracking."""

    def test_get_version_history(self, config_manager, sample_yaml_content):
        """Should return version history sorted by creation time."""
        v1 = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="v1",
            user="user1"
        )
        v2 = config_manager.store_config(
            yaml_content=sample_yaml_content + "\n",
            coverage="aerospace",
            configuration="v2",
            user="user2"
        )
        v3 = config_manager.store_config(
            yaml_content=sample_yaml_content + "\n\n",
            coverage="aerospace",
            configuration="v3",
            user="user3"
        )

        history = config_manager.get_version_history("aerospace")

        assert len(history) == 3
        # Should be sorted descending by creation time
        assert history[0].version_id == v3.version_id
        assert history[2].version_id == v1.version_id

    def test_get_version_history_empty_coverage(self, config_manager):
        """Should return empty list for coverage with no versions."""
        history = config_manager.get_version_history("nonexistent")

        assert history == []
