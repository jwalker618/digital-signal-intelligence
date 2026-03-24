"""
Unit tests for ConfigManager.

Tests configuration hashing, storage, loading, and validation.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from layers.risk.config_manager import ConfigManager, ConfigNotFoundError
from layers.risk.types import (
    CoverageConfig,
    ConfigVersion,
    SignalGroupConfig,
    TierConfig,
    DirectQueryConfig,
    LimitBandConfig,
    DecisionType,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def config_manager():
    """Create a ConfigManager with a temporary storage path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield ConfigManager(storage_path=Path(tmpdir))


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

    direct_queries:
      - id: "pending_claims"
        question: "Are there any pending claims?"
        impacts:
          - type: referral
            value: "Pending claims require review"
            trigger_on: true

    signal_groups:
      - id: safety_signals
        name: Safety Signals
        weight: 0.6
      - id: financial_signals
        name: Financial Signals
        weight: 0.4

    signal_features:
      safety_signals:
        - id: safety_record
          name: Safety Record
          weight: 0.5
          inference_function: infer_safety_record
          categorizer_type: threshold_bucket
          categorizer_params:
            thresholds: [20, 40, 60, 80]
            scores: [20, 40, 60, 80, 100]
        - id: incident_history
          name: Incident History
          weight: 0.5
          inference_function: infer_incident_history
          categorizer_type: threshold_bucket
          categorizer_params:
            thresholds: [20, 40, 60, 80]
            scores: [20, 40, 60, 80, 100]
      financial_signals:
        - id: credit_rating
          name: Credit Rating
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

    tier_thresholds:
      tiers:
        - id: 1
          label: "TIER_1"
          min_score: 800
          max_score: 1000
          auto_approve: true
          premium: 25000
        - id: 2
          label: "TIER_2"
          min_score: 600
          max_score: 799
          auto_approve: true
          premium: 35000
        - id: 3
          label: "TIER_3"
          min_score: 400
          max_score: 599
          premium: 50000
        - id: 4
          label: "TIER_4"
          min_score: 200
          max_score: 399
          premium: 75000
        - id: 5
          label: "TIER_5"
          min_score: 0
          max_score: 199
          auto_decline: true
          premium: 100000
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
        hash2 = config_manager.hash_config(sample_yaml_content + "extra")

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
            user="test_user",
            set_active=True,
        )

        assert isinstance(version, ConfigVersion)
        assert version.coverage == "aerospace"
        assert version.configuration == "aerospace_general"
        assert version.created_by == "test_user"
        assert version.is_active is True

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

    def test_store_without_set_active(self, config_manager, sample_yaml_content):
        """Storing config with set_active=False should not set as active."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="test",
            user="test_user",
            set_active=False,
        )

        assert version.is_active is False

    def test_store_config_overwrites_active(self, config_manager, sample_yaml_content):
        """Storing new active config should replace previous active for same key."""
        version1 = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="user1",
            set_active=True,
        )

        version2 = config_manager.store_config(
            yaml_content=sample_yaml_content + "\n# v2",
            coverage="aerospace",
            configuration="aerospace_general",
            user="user2",
            set_active=True,
        )

        # Loading active should give latest
        config = config_manager.get_active_config("aerospace", "aerospace_general")
        assert config.config_hash == version2.config_hash


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
            configuration="aerospace_general",
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
            configuration="aerospace_general",
            user="test_user"
        )

        config = config_manager.load_config_by_version(version.version_id)

        assert isinstance(config, CoverageConfig)

    def test_load_active_config(self, config_manager, sample_yaml_content):
        """Should load active config for coverage."""
        config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user",
            set_active=True,
        )

        config = config_manager.get_active_config("aerospace", "aerospace_general")

        assert isinstance(config, CoverageConfig)

    def test_load_nonexistent_hash_raises(self, config_manager):
        """Loading non-existent hash should raise ConfigNotFoundError."""
        with pytest.raises(ConfigNotFoundError):
            config_manager.load_config("nonexistent-hash")

    def test_load_no_active_config_raises(self, config_manager):
        """Loading when no active config should raise ConfigNotFoundError."""
        with pytest.raises(ConfigNotFoundError):
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

        assert config.metadata.name == "Test Aerospace Model"
        assert config.metadata.version == "1.0.0"

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

        safety_group = next((g for g in config.signal_groups if g.id == "safety_signals"), None)
        assert safety_group is not None
        assert safety_group.weight == 0.6
        assert len(safety_group.features) == 2

    def test_parses_tiers(self, config_manager, sample_yaml_content):
        """Should parse tier definitions correctly."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )
        config = config_manager.load_config(version.config_hash)

        assert len(config.tiers) == 5

        tier1 = next((t for t in config.tiers if t.tier == 1), None)
        assert tier1 is not None
        assert tier1.min_score == 800
        assert tier1.max_score == 1000
        assert tier1.decision == DecisionType.APPROVE

    def test_parses_direct_queries(self, config_manager, sample_yaml_content):
        """Should parse direct queries correctly."""
        version = config_manager.store_config(
            yaml_content=sample_yaml_content,
            coverage="aerospace",
            configuration="aerospace_general",
            user="test_user"
        )
        config = config_manager.load_config(version.config_hash)

        assert len(config.direct_queries) == 1
        assert config.direct_queries[0].id == "pending_claims"


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
