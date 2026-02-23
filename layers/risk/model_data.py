"""
DSI Model Layer - Model Data Manager (Phase 4)

Manages model data file operations:
- Create new models for entities
- Track signal outputs and versions
- Maintain full audit trail of interactions

Each model has multiple versions representing:
- Initial assessment
- Referral reviews
- Amendments
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from .types import (
    ModelVersion,
    SignalOutput,
    CategoricalOutput,
    TriggeredCondition,
    AppliedModifier,
    CoverageConfig,
    DecisionType,
    utcnow,
)


logger = logging.getLogger("dsi.model_data")


class ModelNotFoundError(Exception):
    """Raised when a model cannot be found."""
    pass


class VersionNotFoundError(Exception):
    """Raised when a model version cannot be found."""
    pass


class ModelDataManager:
    """
    Manages model data file operations.

    Tracks all signal outputs, versions, and interactions for auditability.
    In production, this would persist to a database. This implementation
    uses in-memory storage with optional serialization.
    """

    def __init__(self):
        """Initialize ModelDataManager."""
        # In-memory storage
        self._models: Dict[str, Dict[str, Any]] = {}           # model_id -> model data
        self._versions: Dict[str, ModelVersion] = {}           # version_id -> version
        self._model_versions: Dict[str, List[str]] = {}        # model_id -> [version_ids]

    def create_model(
        self,
        entity_id: str,
        config: CoverageConfig,
        submission_data: Optional[Dict[str, Any]] = None,
        user: str = "system"
    ) -> str:
        """
        Create new model for an entity.

        This initializes the model data file that will track all versions.

        Args:
            entity_id: The entity being assessed
            config: The coverage configuration
            submission_data: Initial submission data
            user: User creating the model

        Returns:
            model_id: UUID for the new model
        """
        model_id = str(uuid.uuid4())

        self._models[model_id] = {
            "model_id": model_id,
            "entity_id": entity_id,
            "coverage": config.coverage_id,
            "configuration": config.config_id,
            "config_hash": getattr(config, 'config_hash', ''),
            "submission_data": submission_data or {},
            "created_at": utcnow(),
            "created_by": user,
            "version_count": 0,
        }

        self._model_versions[model_id] = []

        logger.info(f"Created model {model_id[:8]}... for entity {entity_id}")

        return model_id

    def create_version(
        self,
        model_id: str,
        version_type: str,
        user: str = "system",
        **data
    ) -> ModelVersion:
        """
        Create new version of existing model.

        Each version represents a complete snapshot of the model at a point in time.

        Args:
            model_id: The model to version
            version_type: Type of version ('initial', 'referral_review', 'amendment')
            user: User creating the version
            **data: All version data fields

        Returns:
            Created ModelVersion

        Raises:
            ModelNotFoundError: If model doesn't exist
        """
        if model_id not in self._models:
            raise ModelNotFoundError(f"Model not found: {model_id}")

        model_data = self._models[model_id]

        # Increment version number
        version_number = model_data["version_count"] + 1
        model_data["version_count"] = version_number

        # Create version
        version_id = str(uuid.uuid4())
        version = ModelVersion(
            version_id=version_id,
            model_id=model_id,
            version_number=version_number,
            version_type=version_type,
            config_hash=model_data["config_hash"],
            coverage=model_data["coverage"],
            configuration=model_data["configuration"],
            entity_id=model_data["entity_id"],
            created_at=utcnow(),
            created_by=user,
            **data
        )

        # Store version
        self._versions[version_id] = version
        self._model_versions[model_id].append(version_id)

        logger.info(
            f"Created version {version_number} ({version_type}) "
            f"for model {model_id[:8]}..."
        )

        return version

    def get_model(self, model_id: str) -> Dict[str, Any]:
        """
        Get model data by ID.

        Args:
            model_id: The model ID

        Returns:
            Model data dictionary

        Raises:
            ModelNotFoundError: If model doesn't exist
        """
        if model_id not in self._models:
            raise ModelNotFoundError(f"Model not found: {model_id}")

        return dict(self._models[model_id])

    def get_version(self, version_id: str) -> ModelVersion:
        """
        Get version by ID.

        Args:
            version_id: The version ID

        Returns:
            ModelVersion

        Raises:
            VersionNotFoundError: If version doesn't exist
        """
        if version_id not in self._versions:
            raise VersionNotFoundError(f"Version not found: {version_id}")

        return self._versions[version_id]

    def get_latest_version(self, model_id: str) -> ModelVersion:
        """
        Get most recent version for a model.

        Args:
            model_id: The model ID

        Returns:
            Most recent ModelVersion

        Raises:
            ModelNotFoundError: If model doesn't exist
            VersionNotFoundError: If no versions exist
        """
        if model_id not in self._models:
            raise ModelNotFoundError(f"Model not found: {model_id}")

        version_ids = self._model_versions.get(model_id, [])
        if not version_ids:
            raise VersionNotFoundError(f"No versions for model: {model_id}")

        # Get version with highest version_number
        latest_id = version_ids[-1]
        return self._versions[latest_id]

    def get_version_history(self, model_id: str) -> List[ModelVersion]:
        """
        Get all versions for a model.

        Args:
            model_id: The model ID

        Returns:
            List of ModelVersion sorted by version_number

        Raises:
            ModelNotFoundError: If model doesn't exist
        """
        if model_id not in self._models:
            raise ModelNotFoundError(f"Model not found: {model_id}")

        version_ids = self._model_versions.get(model_id, [])
        versions = [self._versions[vid] for vid in version_ids]

        return sorted(versions, key=lambda v: v.version_number)

    def find_models_for_entity(self, entity_id: str) -> List[str]:
        """
        Find all models for an entity.

        Args:
            entity_id: The entity ID

        Returns:
            List of model IDs
        """
        return [
            model_id for model_id, data in self._models.items()
            if data["entity_id"] == entity_id
        ]

    def update_version(
        self,
        version_id: str,
        **updates
    ) -> ModelVersion:
        """
        Update fields on an existing version.

        Note: In production, this might create a new version instead
        of modifying. For audit trail, versions should generally be immutable.

        Args:
            version_id: The version to update
            **updates: Fields to update

        Returns:
            Updated ModelVersion

        Raises:
            VersionNotFoundError: If version doesn't exist
        """
        if version_id not in self._versions:
            raise VersionNotFoundError(f"Version not found: {version_id}")

        version = self._versions[version_id]

        # Update allowed fields
        for key, value in updates.items():
            if hasattr(version, key):
                setattr(version, key, value)

        return version

    def add_signal_output(
        self,
        version_id: str,
        signal_output: SignalOutput
    ) -> None:
        """
        Add a signal output to a version.

        Args:
            version_id: The version ID
            signal_output: The signal output to add

        Raises:
            VersionNotFoundError: If version doesn't exist
        """
        if version_id not in self._versions:
            raise VersionNotFoundError(f"Version not found: {version_id}")

        self._versions[version_id].signal_outputs.append(signal_output)

    def add_triggered_condition(
        self,
        version_id: str,
        condition: TriggeredCondition,
        source: str = "signal"
    ) -> None:
        """
        Add a triggered condition to a version.

        Args:
            version_id: The version ID
            condition: The triggered condition
            source: 'signal' or 'query'

        Raises:
            VersionNotFoundError: If version doesn't exist
        """
        if version_id not in self._versions:
            raise VersionNotFoundError(f"Version not found: {version_id}")

        version = self._versions[version_id]

        if source == "signal":
            version.signal_conditions.append(condition)
        else:
            version.query_conditions.append(condition)

    def add_applied_modifier(
        self,
        version_id: str,
        modifier: AppliedModifier
    ) -> None:
        """
        Add an applied modifier to a version.

        Args:
            version_id: The version ID
            modifier: The applied modifier

        Raises:
            VersionNotFoundError: If version doesn't exist
        """
        if version_id not in self._versions:
            raise VersionNotFoundError(f"Version not found: {version_id}")

        self._versions[version_id].modifiers_applied.append(modifier)

    def get_audit_trail(self, model_id: str) -> Dict[str, Any]:
        """
        Get complete audit trail for a model.

        Returns all versions with their full data for compliance/audit.

        Args:
            model_id: The model ID

        Returns:
            Dictionary with model info and all versions
        """
        if model_id not in self._models:
            raise ModelNotFoundError(f"Model not found: {model_id}")

        model_data = dict(self._models[model_id])
        versions = self.get_version_history(model_id)

        return {
            "model": model_data,
            "versions": [self._version_to_dict(v) for v in versions],
        }

    def _version_to_dict(self, version: ModelVersion) -> Dict[str, Any]:
        """Convert ModelVersion to dictionary for serialization."""
        return {
            "version_id": version.version_id,
            "model_id": version.model_id,
            "version_number": version.version_number,
            "version_type": version.version_type,
            "entity_id": version.entity_id,
            "coverage": version.coverage,
            "configuration": version.configuration,
            "config_hash": version.config_hash,
            "pure_composite_score": version.pure_composite_score,
            "final_tier": version.final_tier,
            "tier_label": version.tier_label,
            "base_premium": version.base_premium,
            "final_premium": version.final_premium,
            "decision": version.decision.value if isinstance(version.decision, DecisionType) else version.decision,
            "auto_approve": version.auto_approve,
            "referral_reasons": version.referral_reasons,
            "notes": version.notes,
            "confidence": version.confidence,
            "signal_coverage": version.signal_coverage,
            "created_at": version.created_at.isoformat() if version.created_at else None,
            "created_by": version.created_by,
            "signal_outputs": [
                {
                    "signal_id": s.signal_id,
                    "group_id": s.group_id,
                    "raw_score": s.raw_score,
                    "confidence": s.confidence,
                }
                for s in version.signal_outputs
            ],
            "group_scores": version.group_scores,
            "tier_overrides": version.tier_overrides,
            "modifiers_applied": [
                {
                    "source": m.source,
                    "source_id": m.source_id,
                    "name": m.name,
                    "factor": m.factor,
                }
                for m in version.modifiers_applied
            ],
        }


# Singleton instance for convenience
_default_manager: Optional[ModelDataManager] = None


def get_model_data_manager() -> ModelDataManager:
    """Get the default ModelDataManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ModelDataManager()
    return _default_manager
