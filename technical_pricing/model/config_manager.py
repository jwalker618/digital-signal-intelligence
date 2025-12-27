"""
DSI Config Manager

Handles configuration storage, hashing, and retrieval using
content-addressable storage (hybrid) pattern.

Step 1: Configuration instantiation
- Stage 1: Hash YAML, store payload if new
- Stage 2: Store metadata record

Step 3: Minimum viable input verification
"""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .types import (
    CoverageConfig,
    ConfigVersion,
    SignalGroupConfig,
    SignalConfig,
    SignalCondition,
    DirectQueryConfig,
    DirectQueryImpact,
    TierConfig,
    LimitBand,
    ConditionAction,
    DecisionType,
)


class ConfigManager:
    """
    Manages configuration versioning and storage.
    
    Implements content-addressable storage pattern:
    - Payload stored by SHA-256 hash (deduplication)
    - Metadata stored separately (version tracking)
    
    For now, uses local file storage. Production would use:
    - S3/Azure Blob/GCS for payloads
    - PostgreSQL for metadata
    """
    
    def __init__(
        self,
        config_dir: Path | str = "coverages",
        storage_dir: Path | str | None = None
    ):
        """
        Initialize config manager.
        
        Args:
            config_dir: Directory containing coverage YAML files
            storage_dir: Directory for content-addressable storage (optional)
        """
        self.config_dir = Path(config_dir)
        self.storage_dir = Path(storage_dir) if storage_dir else None
        
        # In-memory cache of loaded configs
        self._config_cache: dict[str, CoverageConfig] = {}
        
        # In-memory version tracking (production: PostgreSQL)
        self._versions: dict[str, ConfigVersion] = {}  # version_id -> ConfigVersion
        self._active_configs: dict[str, str] = {}  # coverage -> version_id
        
        # In-memory payload storage (production: S3)
        self._payloads: dict[str, str] = {}  # hash -> yaml_content
    
    # =========================================================================
    # HASHING (Step 1, Stage 1)
    # =========================================================================
    
    def hash_config(self, yaml_content: str) -> str:
        """
        Generate SHA-256 hash of YAML payload.
        
        Even a single space change produces different hash,
        ensuring unique integrity for each configuration snapshot.
        """
        return hashlib.sha256(yaml_content.encode('utf-8')).hexdigest()
    
    # =========================================================================
    # STORAGE (Step 1)
    # =========================================================================
    
    def store_config(
        self,
        yaml_content: str,
        coverage: str,
        configuration: str,
        user: str
    ) -> ConfigVersion:
        """
        Store configuration using content-addressable pattern.
        
        Stage 1: Check hash, store payload if new
        Stage 2: Create metadata record
        
        Returns:
            ConfigVersion with version_id
        """
        # Stage 1: Hash and store payload
        config_hash = self.hash_config(yaml_content)
        
        if config_hash not in self._payloads:
            # New payload - store it
            self._payloads[config_hash] = yaml_content
            
            # Production: Upload to S3
            if self.storage_dir:
                payload_path = self.storage_dir / f"{config_hash}.yaml"
                payload_path.parent.mkdir(parents=True, exist_ok=True)
                payload_path.write_text(yaml_content)
        
        # Stage 2: Create metadata record
        version_id = str(uuid.uuid4())
        version = ConfigVersion(
            version_id=version_id,
            config_hash=config_hash,
            coverage=coverage,
            configuration=configuration,
            created_by=user,
            created_at=datetime.utcnow(),
            is_active=False
        )
        
        self._versions[version_id] = version
        
        return version
    
    def activate_config(self, version_id: str) -> None:
        """Set a config version as the active one for its coverage"""
        if version_id not in self._versions:
            raise ValueError(f"Version not found: {version_id}")
        
        version = self._versions[version_id]
        
        # Deactivate previous active config for this coverage
        if version.coverage in self._active_configs:
            old_version_id = self._active_configs[version.coverage]
            if old_version_id in self._versions:
                self._versions[old_version_id].is_active = False
        
        # Activate new version
        version.is_active = True
        self._active_configs[version.coverage] = version_id
        
        # Clear cache for this coverage
        cache_key = f"{version.coverage}:{version.configuration}"
        self._config_cache.pop(cache_key, None)
    
    # =========================================================================
    # LOADING
    # =========================================================================
    
    def load_config(self, config_hash: str) -> CoverageConfig:
        """Load and parse config by hash"""
        if config_hash not in self._payloads:
            raise ValueError(f"Config hash not found: {config_hash}")
        
        yaml_content = self._payloads[config_hash]
        return self._parse_yaml(yaml_content, config_hash)
    
    def load_config_by_version(self, version_id: str) -> CoverageConfig:
        """Load config by version ID (looks up hash first)"""
        if version_id not in self._versions:
            raise ValueError(f"Version not found: {version_id}")
        
        version = self._versions[version_id]
        return self.load_config(version.config_hash)
    
    def get_active_config(self, coverage: str) -> CoverageConfig:
        """Get currently active config for a coverage"""
        if coverage not in self._active_configs:
            raise ValueError(f"No active config for coverage: {coverage}")
        
        version_id = self._active_configs[coverage]
        return self.load_config_by_version(version_id)
    
    def load_from_file(self, coverage: str, configuration: str | None = None) -> CoverageConfig:
        """
        Load config directly from YAML file.
        
        This is the primary method during development.
        In production, configs would be loaded via store_config + activate_config.
        
        Args:
            coverage: Coverage name (e.g., 'aerospace', 'cyber')
            configuration: Specific configuration name (optional)
        
        Returns:
            Parsed and validated CoverageConfig
        """
        # Check cache first
        cache_key = f"{coverage}:{configuration or 'default'}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        # Find config file
        config_path = self.config_dir / coverage / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        
        # Load and parse
        yaml_content = config_path.read_text()
        config_hash = self.hash_config(yaml_content)
        config = self._parse_yaml(yaml_content, config_hash, coverage, configuration)
        
        # Cache and return
        self._config_cache[cache_key] = config
        return config
    
    # =========================================================================
    # PARSING
    # =========================================================================
    
    def _parse_yaml(
        self,
        yaml_content: str,
        config_hash: str,
        coverage: str | None = None,
        configuration: str | None = None
    ) -> CoverageConfig:
        """
        Parse YAML content into typed CoverageConfig.
        
        Handles the nested structure of coverage YAML files.
        """
        raw = yaml.safe_load(yaml_content)
        
        # Navigate to correct level
        # YAML structure: coverage: { configuration: { ... } }
        if coverage and coverage in raw:
            raw = raw[coverage]
        
        if configuration and configuration in raw:
            raw = raw[configuration]
        elif not configuration:
            # Take first configuration if not specified
            if isinstance(raw, dict):
                first_key = next(iter(raw.keys()), None)
                if first_key and isinstance(raw[first_key], dict):
                    configuration = first_key
                    raw = raw[first_key]
        
        # Extract metadata
        metadata = raw.get('metadata', {})
        
        # Parse signal groups
        signal_groups = self._parse_signal_groups(
            raw.get('signal_groups', []),
            raw.get('signal_features', {})
        )
        
        # Parse direct queries
        direct_queries = self._parse_direct_queries(raw.get('direct_queries', []))
        
        # Parse tier thresholds
        tier_thresholds = self._parse_tier_thresholds(raw.get('tier_thresholds', []))
        
        # Parse limit bands
        limit_bands = self._parse_limit_bands(raw.get('limit_bands', []))
        
        # Parse deductible credits
        deductible_credits = {
            float(k): float(v)
            for k, v in raw.get('deductible_credits', {}).items()
        }
        
        # Build config
        config = CoverageConfig(
            coverage=coverage or raw.get('coverage', 'unknown'),
            configuration=configuration or raw.get('configuration', 'default'),
            version=metadata.get('version', '0.0.0'),
            config_hash=config_hash,
            required_inputs=raw.get('required_inputs', []),
            signal_groups=signal_groups,
            direct_queries=direct_queries,
            categorical_groups=raw.get('categorical_groups', []),
            categorical_features=raw.get('categorical_features', {}),
            tier_thresholds=tier_thresholds,
            limit_bands=limit_bands,
            deductible_credits=deductible_credits,
            metadata=metadata
        )
        
        return config
    
    def _parse_signal_groups(
        self,
        groups_raw: list[dict],
        features_raw: dict[str, list[dict]]
    ) -> list[SignalGroupConfig]:
        """Parse signal_groups and signal_features into SignalGroupConfig objects"""
        groups = []
        
        for group_data in groups_raw:
            group_name = group_data.get('name', '')
            
            # Get signals for this group from signal_features
            signals_data = features_raw.get(group_name, [])
            signals = [
                SignalConfig(
                    name=s.get('name', ''),
                    weight=float(s.get('weight', 0)),
                    inference_function=s.get('inference_function', ''),
                    categorizer_type=s.get('categorizer_type', ''),
                    categorizer_params=s.get('categorizer_params', {}),
                    conditions=self._parse_conditions(s.get('conditions', []))
                )
                for s in signals_data
            ]
            
            group = SignalGroupConfig(
                name=group_name,
                weight=float(group_data.get('weight', 0)),
                signals=signals,
                conditions=self._parse_conditions(group_data.get('conditions', []))
            )
            groups.append(group)
        
        return groups
    
    def _parse_conditions(self, conditions_raw: list[dict]) -> list[SignalCondition]:
        """Parse condition definitions"""
        conditions = []
        
        for c in conditions_raw:
            try:
                condition = SignalCondition(
                    condition_type=c.get('condition_type', ''),
                    condition_value=c.get('condition_value'),
                    action=ConditionAction(c.get('action', 'note')),
                    action_value=c.get('action_value')
                )
                conditions.append(condition)
            except ValueError as e:
                # Skip invalid conditions but log
                print(f"Warning: Invalid condition skipped: {e}")
        
        return conditions
    
    def _parse_direct_queries(self, queries_raw: list[dict]) -> list[DirectQueryConfig]:
        """Parse direct query definitions"""
        queries = []
        
        for q in queries_raw:
            impacts = []
            for i in q.get('impacts', []):
                impact = DirectQueryImpact(
                    impact_type=ConditionAction(i.get('type', 'note')),
                    value=i.get('value'),
                    trigger_on=i.get('trigger_on', True)
                )
                impacts.append(impact)
            
            query = DirectQueryConfig(
                id=q.get('id', ''),
                question=q.get('question', ''),
                impacts=impacts
            )
            queries.append(query)
        
        return queries
    
    def _parse_tier_thresholds(self, tiers_raw: list[dict]) -> list[TierConfig]:
        """Parse tier threshold definitions"""
        tiers = []
        
        for t in tiers_raw:
            tier = TierConfig(
                tier=int(t.get('tier', 0)),
                min_score=int(t.get('min_score', 0)),
                max_score=int(t.get('max_score', 0)),
                decision=DecisionType(t.get('decision', 'approve')),
                base_premium=t.get('base_premium'),
                rate=t.get('rate'),
                rate_basis=t.get('rate_basis')
            )
            tiers.append(tier)
        
        return tiers
    
    def _parse_limit_bands(self, bands_raw: list[dict]) -> list[LimitBand]:
        """Parse ILF table"""
        return [
            LimitBand(
                limit=float(b.get('limit', 0)),
                ilf=float(b.get('ilf', 1.0))
            )
            for b in bands_raw
        ]
    
    # =========================================================================
    # VALIDATION (Step 3)
    # =========================================================================
    
    def validate_config(self, config: CoverageConfig) -> list[str]:
        """
        Validate configuration integrity.
        
        Returns list of validation errors (empty if valid).
        """
        return config.validate()
    
    def verify_required_inputs(
        self,
        config: CoverageConfig,
        submission_data: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        Verify minimum viable inputs are present (Step 3).
        
        Args:
            config: Coverage configuration
            submission_data: Submitted data to validate
        
        Returns:
            Tuple of (is_valid, missing_fields)
        """
        missing = []
        
        for required in config.required_inputs:
            if required not in submission_data:
                missing.append(required)
            elif submission_data[required] is None:
                missing.append(required)
            elif isinstance(submission_data[required], str) and not submission_data[required].strip():
                missing.append(required)
        
        return (len(missing) == 0, missing)
    
    # =========================================================================
    # INFERENCE FUNCTION VALIDATION
    # =========================================================================
    
    def validate_inference_functions(
        self,
        config: CoverageConfig,
        registry: dict[str, Any] | None = None
    ) -> list[str]:
        """
        Verify all inference_function references have implementations.
        
        Args:
            config: Coverage configuration
            registry: Optional inference function registry to check against
        
        Returns:
            List of missing inference functions
        """
        missing = []
        
        for group in config.signal_groups:
            for signal in group.signals:
                func_name = signal.inference_function
                if not func_name:
                    missing.append(f"{group.name}.{signal.name}: no inference_function specified")
                elif registry and func_name not in registry:
                    missing.append(f"{group.name}.{signal.name}: {func_name} not in registry")
        
        return missing
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_version_history(self, coverage: str) -> list[ConfigVersion]:
        """Get all versions for a coverage, sorted by creation time"""
        versions = [
            v for v in self._versions.values()
            if v.coverage == coverage
        ]
        return sorted(versions, key=lambda v: v.created_at, reverse=True)
    
    def get_config_diff(self, hash1: str, hash2: str) -> dict:
        """
        Compare two config versions.
        
        Returns dict with added, removed, and changed elements.
        (Placeholder for future implementation)
        """
        # TODO: Implement detailed config diffing
        return {
            "hash1": hash1,
            "hash2": hash2,
            "same": hash1 == hash2
        }
    
    def list_coverages(self) -> list[str]:
        """List all available coverages from config directory"""
        if not self.config_dir.exists():
            return []
        
        return [
            d.name for d in self.config_dir.iterdir()
            if d.is_dir() and (d / "config.yaml").exists()
        ]
