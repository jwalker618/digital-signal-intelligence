"""
DSI Model Layer - Configuration Manager (Phase 4)

Handles configuration versioning using Content-Addressable Storage:
- Stage 1: Hash YAML content, store payload if new (S3/blob storage)
- Stage 2: Create metadata record in structured storage (PostgreSQL)

This module also provides parsing of YAML configs into typed CoverageConfig objects.
"""

import hashlib
import uuid
import yaml
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from .types import (
    CoverageConfig,
    ConfigVersion,
    ConfigMetadata,
    SignalGroupConfig,
    SignalFeatureConfig,
    DirectQueryConfig,
    CategoricalGroupConfig,
    TierConfig,
    LimitBandConfig,
    PricingConfig,
    utcnow,
)


logger = logging.getLogger("dsi.config_manager")


class ConfigParseError(Exception):
    """Raised when configuration parsing fails."""
    pass


class ConfigNotFoundError(Exception):
    """Raised when a configuration cannot be found."""
    pass


class ConfigManager:
    """
    Manages configuration versioning and storage.

    Implements Content-Addressable Storage pattern:
    - Payload addressed by SHA-256 hash
    - Metadata tracked separately with version IDs

    For this implementation, storage is in-memory with optional file persistence.
    Production would use S3/Azure Blob for payloads and PostgreSQL for metadata.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize ConfigManager.

        Args:
            storage_path: Optional path for file-based storage
        """
        self.storage_path = storage_path

        # In-memory storage (simulating S3 + PostgreSQL)
        self._payload_store: Dict[str, str] = {}           # hash -> yaml content
        self._metadata_store: Dict[str, ConfigVersion] = {} # version_id -> metadata
        self._active_configs: Dict[str, str] = {}          # coverage:config -> hash
        self._parsed_cache: Dict[str, CoverageConfig] = {} # hash -> parsed config

    def hash_config(self, yaml_content: str) -> str:
        """
        Generate SHA-256 hash of YAML payload.

        Args:
            yaml_content: Raw YAML string

        Returns:
            Hex-encoded SHA-256 hash
        """
        # Normalize whitespace for consistent hashing
        normalized = yaml_content.strip()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def store_config(
        self,
        yaml_content: str,
        coverage: str,
        configuration: str,
        user: str,
        set_active: bool = True
    ) -> ConfigVersion:
        """
        Store a configuration using content-addressable storage.

        Stage 1: Check hash, store payload if new
        Stage 2: Create metadata record

        Args:
            yaml_content: Raw YAML configuration string
            coverage: Coverage domain (e.g., "aerospace")
            configuration: Configuration name (e.g., "aerospace_general")
            user: User creating this version
            set_active: Whether to set this as the active config

        Returns:
            ConfigVersion with version_id and metadata
        """
        # Stage 1: Hash and store payload
        config_hash = self.hash_config(yaml_content)

        if config_hash not in self._payload_store:
            # New payload - store it
            self._payload_store[config_hash] = yaml_content
            logger.info(f"Stored new config payload: {config_hash[:12]}...")
        else:
            logger.debug(f"Config payload already exists: {config_hash[:12]}...")

        # Stage 2: Create metadata record
        version_id = str(uuid.uuid4())
        version = ConfigVersion(
            version_id=version_id,
            config_hash=config_hash,
            coverage=coverage,
            configuration=configuration,
            created_by=user,
            created_at=utcnow(),
            is_active=set_active,
        )

        self._metadata_store[version_id] = version

        if set_active:
            config_key = f"{coverage}:{configuration}"
            self._active_configs[config_key] = config_hash
            logger.info(f"Set active config for {config_key}: {config_hash[:12]}...")

        return version

    def store_config_from_file(
        self,
        file_path: Path,
        user: str,
        set_active: bool = True
    ) -> ConfigVersion:
        """
        Store configuration from a YAML file.

        Args:
            file_path: Path to YAML file
            user: User creating this version
            set_active: Whether to set as active

        Returns:
            ConfigVersion with version_id

        Raises:
            FileNotFoundError: If file doesn't exist
            ConfigParseError: If YAML is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        yaml_content = file_path.read_text()

        # Parse to extract coverage and configuration names
        try:
            raw_config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ConfigParseError(f"Invalid YAML: {e}")

        # Get coverage (first key) and configuration (second key)
        coverage = list(raw_config.keys())[0]
        configuration = list(raw_config[coverage].keys())[0]

        return self.store_config(
            yaml_content=yaml_content,
            coverage=coverage,
            configuration=configuration,
            user=user,
            set_active=set_active,
        )

    def load_config(self, config_hash: str) -> CoverageConfig:
        """
        Load and parse configuration by hash.

        Args:
            config_hash: SHA-256 hash of YAML payload

        Returns:
            Parsed CoverageConfig

        Raises:
            ConfigNotFoundError: If hash not in store
            ConfigParseError: If parsing fails
        """
        # Check cache first
        if config_hash in self._parsed_cache:
            return self._parsed_cache[config_hash]

        # Get raw content
        if config_hash not in self._payload_store:
            raise ConfigNotFoundError(f"No config found with hash: {config_hash}")

        yaml_content = self._payload_store[config_hash]

        # Parse and cache
        config = self._parse_yaml(yaml_content, config_hash)
        self._parsed_cache[config_hash] = config

        return config

    def load_config_by_version(self, version_id: str) -> CoverageConfig:
        """
        Load configuration by version ID.

        Args:
            version_id: UUID of the version

        Returns:
            Parsed CoverageConfig

        Raises:
            ConfigNotFoundError: If version not found
        """
        if version_id not in self._metadata_store:
            raise ConfigNotFoundError(f"No version found: {version_id}")

        version = self._metadata_store[version_id]
        return self.load_config(version.config_hash)

    def get_active_config(
        self,
        coverage: str,
        configuration: Optional[str] = None
    ) -> CoverageConfig:
        """
        Get currently active configuration for a coverage.

        Args:
            coverage: Coverage domain (e.g., "aerospace")
            configuration: Optional configuration name (defaults to coverage_general)

        Returns:
            Parsed CoverageConfig

        Raises:
            ConfigNotFoundError: If no active config
        """
        if configuration is None:
            configuration = f"{coverage}_general"

        config_key = f"{coverage}:{configuration}"

        if config_key not in self._active_configs:
            raise ConfigNotFoundError(f"No active config for: {config_key}")

        config_hash = self._active_configs[config_key]
        return self.load_config(config_hash)

    def get_version_history(
        self,
        coverage: str,
        configuration: Optional[str] = None
    ) -> List[ConfigVersion]:
        """
        Get all versions for a coverage/configuration.

        Args:
            coverage: Coverage domain
            configuration: Optional configuration name

        Returns:
            List of ConfigVersion sorted by created_at descending
        """
        versions = []
        for version in self._metadata_store.values():
            if version.coverage == coverage:
                if configuration is None or version.configuration == configuration:
                    versions.append(version)

        return sorted(versions, key=lambda v: v.created_at, reverse=True)

    def _parse_yaml(self, yaml_content: str, config_hash: str) -> CoverageConfig:
        """
        Parse YAML content into CoverageConfig.

        Args:
            yaml_content: Raw YAML string
            config_hash: Hash for reference

        Returns:
            Parsed CoverageConfig

        Raises:
            ConfigParseError: If parsing fails
        """
        try:
            raw_config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ConfigParseError(f"Invalid YAML: {e}")

        try:
            # Get coverage and configuration names
            coverage = list(raw_config.keys())[0]
            config_data = raw_config[coverage]
            configuration = list(config_data.keys())[0]
            config = config_data[configuration]

            # Parse metadata
            metadata = ConfigMetadata.from_yaml(config.get("metadata", {}))

            # Parse direct queries
            direct_queries = [
                DirectQueryConfig.from_yaml(q)
                for q in config.get("direct_queries", [])
            ]

            # Parse categorical groups with their features
            categorical_groups = []
            cat_groups_config = config.get("categorical_groups", [])
            cat_features_config = config.get("categorical_features", {})

            for group_config in cat_groups_config:
                group_id = group_config["id"]
                values_data = cat_features_config.get(group_id, [])
                categorical_groups.append(
                    CategoricalGroupConfig.from_yaml(group_config, values_data)
                )

            # Parse signal groups with their features
            signal_groups = []
            groups_config = config.get("signal_groups", [])
            features_config = config.get("signal_features", {})

            for group_config in groups_config:
                group_id = group_config["id"]
                features_data = features_config.get(group_id, [])
                signal_groups.append(
                    SignalGroupConfig.from_yaml(group_config, features_data)
                )

            # Parse tiers
            tiers_config = config.get("tier_thresholds", {})
            tiers = [
                TierConfig.from_yaml(tier_data)
                for tier_data in tiers_config.get("tiers", [])
            ]

            # Parse limit bands
            limit_bands = [
                LimitBandConfig.from_yaml(band)
                for band in config.get("limit_bandings", [])
            ]

            # Parse pricing
            pricing = PricingConfig.from_yaml(config.get("pricing", {}))

            # Get test profiles
            test_profiles = config.get("test_profiles", {})

            return CoverageConfig(
                coverage=coverage,
                configuration=configuration,
                config_hash=config_hash,
                metadata=metadata,
                direct_queries=direct_queries,
                categorical_groups=categorical_groups,
                signal_groups=signal_groups,
                tiers=tiers,
                limit_bands=limit_bands,
                pricing=pricing,
                test_profiles=test_profiles,
            )

        except KeyError as e:
            raise ConfigParseError(f"Missing required config key: {e}")
        except Exception as e:
            raise ConfigParseError(f"Failed to parse config: {e}")

    def validate_config(self, config: CoverageConfig) -> List[str]:
        """
        Validate a configuration for completeness and consistency.

        Args:
            config: Parsed CoverageConfig

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check signal group weights sum to 1.0
        total_weight = sum(g.weight for g in config.signal_groups)
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"Signal group weights sum to {total_weight:.3f}, expected 1.0")

        # Check feature weights within each group
        for group in config.signal_groups:
            feature_weight = sum(f.weight for f in group.features)
            if group.features and abs(feature_weight - 1.0) > 0.01:
                errors.append(
                    f"Feature weights in '{group.id}' sum to {feature_weight:.3f}, expected 1.0"
                )

        # Check tier coverage (should cover 0-1000)
        if config.tiers:
            min_tier_score = min(t.min_score for t in config.tiers)
            max_tier_score = max(t.max_score for t in config.tiers)
            if min_tier_score > 0:
                errors.append(f"Tier scores don't cover 0, minimum is {min_tier_score}")
            if max_tier_score < 1000:
                errors.append(f"Tier scores don't cover 1000, maximum is {max_tier_score}")

        # Check for duplicate IDs
        signal_ids = set()
        for group in config.signal_groups:
            for feature in group.features:
                if feature.id in signal_ids:
                    errors.append(f"Duplicate signal feature ID: {feature.id}")
                signal_ids.add(feature.id)

        return errors

    def load_from_file(self, file_path: Path) -> CoverageConfig:
        """
        Load and parse configuration directly from a file.

        This is a convenience method that doesn't store the config.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            Parsed CoverageConfig
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        yaml_content = file_path.read_text()
        config_hash = self.hash_config(yaml_content)

        return self._parse_yaml(yaml_content, config_hash)


# Singleton instance for convenience
_default_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the default ConfigManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ConfigManager()
    return _default_manager


def load_coverage_config(
    coverage: str,
    configuration: Optional[str] = None,
    config_path: Optional[Path] = None
) -> CoverageConfig:
    """
    Convenience function to load a coverage configuration.

    Tries in order:
    1. From active configs in manager
    2. From file at config_path
    3. From default location based on coverage name

    Args:
        coverage: Coverage domain (e.g., "aerospace")
        configuration: Configuration name (optional)
        config_path: Explicit path to config file (optional)

    Returns:
        Parsed CoverageConfig
    """
    manager = get_config_manager()

    # Try active config first
    try:
        return manager.get_active_config(coverage, configuration)
    except ConfigNotFoundError:
        pass

    # Try explicit path
    if config_path and config_path.exists():
        return manager.load_from_file(config_path)

    # Try default location
    default_path = Path(__file__).parent.parent / "coverages" / coverage / "config.yaml"
    if default_path.exists():
        return manager.load_from_file(default_path)

    raise ConfigNotFoundError(
        f"Could not find config for {coverage}"
        f" (tried active configs and {default_path})"
    )
