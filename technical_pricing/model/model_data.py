"""
DSI Model Data Manager

Handles model data file creation and version tracking.

Step 2: Model data file creation
- Stage 1: Capture every item with ID, persist signal outputs
- Stage 2: Track interactions as new versions (audit trail)
"""

import uuid
from datetime import datetime
from typing import Any

from .types import (
    ModelVersion,
    SignalOutput,
    ModifierApplication,
    ScoringResult,
    QueryEvaluationResult,
    PricingResult,
    VersionType,
    DecisionType,
)


class ModelDataManager:
    """
    Manages model data file operations.
    
    Every model execution creates a versioned snapshot.
    Subsequent interactions (referrals, amendments) create new versions.
    This provides complete audit trail.
    
    For now, uses in-memory storage.
    Production would use PostgreSQL + S3.
    """
    
    def __init__(self):
        """Initialize model data manager"""
        # In-memory storage (production: PostgreSQL)
        self._models: dict[str, dict] = {}  # model_id -> model metadata
        self._versions: dict[str, ModelVersion] = {}  # version_id -> ModelVersion
        self._model_versions: dict[str, list[str]] = {}  # model_id -> [version_ids]
    
    # =========================================================================
    # MODEL CREATION
    # =========================================================================
    
    def create_model(
        self,
        entity_id: str,
        coverage: str,
        config_hash: str,
        user: str
    ) -> str:
        """
        Create new model, return model_id.
        
        A model represents a single submission/entity being evaluated.
        Each model can have multiple versions as it progresses through workflow.
        """
        model_id = str(uuid.uuid4())
        
        self._models[model_id] = {
            "model_id": model_id,
            "entity_id": entity_id,
            "coverage": coverage,
            "config_hash": config_hash,
            "created_by": user,
            "created_at": datetime.utcnow(),
            "status": "created"
        }
        
        self._model_versions[model_id] = []
        
        return model_id
    
    # =========================================================================
    # VERSION CREATION (Step 2)
    # =========================================================================
    
    def create_initial_version(
        self,
        model_id: str,
        entity_id: str,
        submission_data: dict,
        direct_query_responses: dict[str, bool],
        categorical_selections: dict[str, str],
        config_hash: str,
        user: str
    ) -> ModelVersion:
        """
        Create initial version for a model (Step 2, Stage 1).
        
        This is called when a submission is first processed.
        Signal outputs will be populated by the scorer.
        """
        return self._create_version(
            model_id=model_id,
            version_type=VersionType.INITIAL,
            entity_id=entity_id,
            submission_data=submission_data,
            direct_query_responses=direct_query_responses,
            categorical_selections=categorical_selections,
            config_hash=config_hash,
            user=user
        )
    
    def create_referral_version(
        self,
        model_id: str,
        reviewer: str,
        adjustments: dict | None = None
    ) -> ModelVersion:
        """
        Create new version from referral review (Step 2, Stage 2).
        
        Copies data from latest version and allows adjustments.
        """
        latest = self.get_latest_version(model_id)
        if latest is None:
            raise ValueError(f"No existing version for model: {model_id}")
        
        # Copy data from latest version
        return self._create_version(
            model_id=model_id,
            version_type=VersionType.REFERRAL_REVIEW,
            entity_id=latest.entity_id,
            submission_data=latest.submission_data,
            direct_query_responses=latest.direct_query_responses,
            categorical_selections=latest.categorical_selections,
            config_hash=latest.config_hash,
            user=reviewer,
            copy_from=latest,
            adjustments=adjustments
        )
    
    def create_amendment_version(
        self,
        model_id: str,
        user: str,
        amendments: dict
    ) -> ModelVersion:
        """
        Create new version from amendment.
        
        Used when submission data changes after initial processing.
        """
        latest = self.get_latest_version(model_id)
        if latest is None:
            raise ValueError(f"No existing version for model: {model_id}")
        
        # Merge amendments into submission data
        updated_submission = {**latest.submission_data, **amendments.get('submission_data', {})}
        updated_queries = {**latest.direct_query_responses, **amendments.get('direct_query_responses', {})}
        updated_categories = {**latest.categorical_selections, **amendments.get('categorical_selections', {})}
        
        return self._create_version(
            model_id=model_id,
            version_type=VersionType.AMENDMENT,
            entity_id=latest.entity_id,
            submission_data=updated_submission,
            direct_query_responses=updated_queries,
            categorical_selections=updated_categories,
            config_hash=latest.config_hash,
            user=user
        )
    
    def _create_version(
        self,
        model_id: str,
        version_type: VersionType,
        entity_id: str,
        submission_data: dict,
        direct_query_responses: dict[str, bool],
        categorical_selections: dict[str, str],
        config_hash: str,
        user: str,
        copy_from: ModelVersion | None = None,
        adjustments: dict | None = None
    ) -> ModelVersion:
        """Internal method to create a new version"""
        if model_id not in self._models:
            raise ValueError(f"Model not found: {model_id}")
        
        # Determine version number
        existing_versions = self._model_versions.get(model_id, [])
        version_number = len(existing_versions) + 1
        
        # Create version ID
        version_id = str(uuid.uuid4())
        
        # Create version object
        version = ModelVersion(
            version_id=version_id,
            model_id=model_id,
            version_number=version_number,
            version_type=version_type,
            entity_id=entity_id,
            submission_data=submission_data,
            direct_query_responses=direct_query_responses,
            categorical_selections=categorical_selections,
            config_hash=config_hash,
            created_at=datetime.utcnow(),
            created_by=user
        )
        
        # If copying from previous version, copy computed values
        if copy_from:
            version.signal_outputs = copy_from.signal_outputs.copy()
            version.group_scores = copy_from.group_scores.copy()
            version.pure_composite_score = copy_from.pure_composite_score
            version.aggregate_confidence = copy_from.aggregate_confidence
            version.signal_conditions = copy_from.signal_conditions.copy()
            version.query_conditions = copy_from.query_conditions.copy()
            version.tier_overrides = copy_from.tier_overrides.copy()
            version.score_based_tier = copy_from.score_based_tier
            version.final_tier = copy_from.final_tier
            version.base_premium = copy_from.base_premium
            version.modifiers_applied = copy_from.modifiers_applied.copy()
            version.limit_premiums = copy_from.limit_premiums.copy()
            version.final_premium = copy_from.final_premium
            version.referral_reasons = copy_from.referral_reasons.copy()
            version.notes = copy_from.notes.copy()
        
        # Apply any adjustments (for referral reviews)
        if adjustments:
            if 'final_tier' in adjustments:
                version.final_tier = adjustments['final_tier']
            if 'decision' in adjustments:
                version.decision = DecisionType(adjustments['decision'])
            if 'notes' in adjustments:
                version.notes.extend(adjustments['notes'])
            if 'modifiers' in adjustments:
                for mod in adjustments['modifiers']:
                    version.modifiers_applied.append(ModifierApplication(**mod))
        
        # Store version
        self._versions[version_id] = version
        self._model_versions[model_id].append(version_id)
        
        return version
    
    # =========================================================================
    # VERSION UPDATES
    # =========================================================================
    
    def update_version_scoring(
        self,
        version_id: str,
        scoring_result: ScoringResult
    ) -> ModelVersion:
        """
        Update version with scoring results (Steps 4-6).
        
        Called after signal extraction and scoring.
        """
        if version_id not in self._versions:
            raise ValueError(f"Version not found: {version_id}")
        
        version = self._versions[version_id]
        
        # Step 4: Signal outputs
        version.signal_outputs = scoring_result.signal_outputs
        version.group_scores = scoring_result.group_scores
        
        # Step 5: Pure composite
        version.pure_composite_score = scoring_result.pure_composite_score
        version.aggregate_confidence = scoring_result.aggregate_confidence
        
        # Step 6: Signal conditions
        version.signal_conditions = scoring_result.signal_conditions_triggered
        version.tier_overrides.extend(scoring_result.tier_overrides_from_signals)
        version.referral_reasons.extend(scoring_result.referrals_from_signals)
        version.notes.extend(scoring_result.notes_from_signals)
        
        return version
    
    def update_version_queries(
        self,
        version_id: str,
        query_result: QueryEvaluationResult
    ) -> ModelVersion:
        """
        Update version with query evaluation results (Step 7).
        """
        if version_id not in self._versions:
            raise ValueError(f"Version not found: {version_id}")
        
        version = self._versions[version_id]
        
        version.query_conditions = query_result.queries_evaluated
        version.tier_overrides.extend(query_result.tier_overrides)
        version.referral_reasons.extend(query_result.referrals)
        version.notes.extend(query_result.notes)
        
        return version
    
    def update_version_pricing(
        self,
        version_id: str,
        pricing_result: PricingResult
    ) -> ModelVersion:
        """
        Update version with pricing results (Steps 8-12).
        """
        if version_id not in self._versions:
            raise ValueError(f"Version not found: {version_id}")
        
        version = self._versions[version_id]
        
        # Steps 8-9: Tier
        version.score_based_tier = pricing_result.score_based_tier
        version.final_tier = pricing_result.final_tier
        
        # Step 10: Base premium
        version.base_premium = pricing_result.base_premium
        
        # Step 11: Modifiers
        version.modifiers_applied = pricing_result.modifiers_applied
        
        # Step 12: Limit bands
        version.limit_premiums = pricing_result.limit_premiums
        
        # Final premium (at default/selected limit)
        if pricing_result.limit_premiums:
            # Use first limit as default
            version.final_premium = list(pricing_result.limit_premiums.values())[0]
        else:
            version.final_premium = pricing_result.premium_after_modifiers
        
        return version
    
    def update_version_decision(
        self,
        version_id: str,
        decision: DecisionType,
        auto_approve: bool,
        referral_reasons: list[str] | None = None,
        notes: list[str] | None = None
    ) -> ModelVersion:
        """
        Update version with final decision (Step 13).
        """
        if version_id not in self._versions:
            raise ValueError(f"Version not found: {version_id}")
        
        version = self._versions[version_id]
        
        version.decision = decision
        version.auto_approve = auto_approve
        
        if referral_reasons:
            version.referral_reasons.extend(referral_reasons)
        if notes:
            version.notes.extend(notes)
        
        # Update model status
        model = self._models.get(version.model_id)
        if model:
            model['status'] = decision.value
        
        return version
    
    # =========================================================================
    # RETRIEVAL
    # =========================================================================
    
    def get_version(self, version_id: str) -> ModelVersion | None:
        """Get a specific version by ID"""
        return self._versions.get(version_id)
    
    def get_latest_version(self, model_id: str) -> ModelVersion | None:
        """Get most recent version for a model"""
        if model_id not in self._model_versions:
            return None
        
        version_ids = self._model_versions[model_id]
        if not version_ids:
            return None
        
        return self._versions.get(version_ids[-1])
    
    def get_version_history(self, model_id: str) -> list[ModelVersion]:
        """Get all versions for audit trail"""
        if model_id not in self._model_versions:
            return []
        
        return [
            self._versions[vid]
            for vid in self._model_versions[model_id]
            if vid in self._versions
        ]
    
    def get_model(self, model_id: str) -> dict | None:
        """Get model metadata"""
        return self._models.get(model_id)
    
    # =========================================================================
    # SEARCH & FILTERING
    # =========================================================================
    
    def find_models_by_entity(self, entity_id: str) -> list[dict]:
        """Find all models for an entity"""
        return [
            m for m in self._models.values()
            if m.get('entity_id') == entity_id
        ]
    
    def find_models_by_coverage(self, coverage: str) -> list[dict]:
        """Find all models for a coverage"""
        return [
            m for m in self._models.values()
            if m.get('coverage') == coverage
        ]
    
    def find_models_by_status(self, status: str) -> list[dict]:
        """Find all models with a specific status"""
        return [
            m for m in self._models.values()
            if m.get('status') == status
        ]
    
    def find_pending_referrals(self) -> list[ModelVersion]:
        """Find all versions pending referral review"""
        return [
            v for v in self._versions.values()
            if v.decision == DecisionType.REFER and not v.auto_approve
        ]
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def version_to_dict(self, version: ModelVersion) -> dict:
        """
        Convert ModelVersion to dictionary for storage/API response.
        """
        return {
            "version_id": version.version_id,
            "model_id": version.model_id,
            "version_number": version.version_number,
            "version_type": version.version_type.value,
            "entity_id": version.entity_id,
            "submission_data": version.submission_data,
            "direct_query_responses": version.direct_query_responses,
            "categorical_selections": version.categorical_selections,
            "signal_outputs": [
                {
                    "signal_id": s.signal_id,
                    "signal_name": s.signal_name,
                    "group_name": s.group_name,
                    "raw_score": s.raw_score,
                    "confidence": s.confidence,
                    "weighted_score": s.weighted_score,
                    "data_sources": s.data_sources,
                    "extracted_at": s.extracted_at.isoformat(),
                    "conditions_triggered": s.conditions_triggered
                }
                for s in version.signal_outputs
            ],
            "group_scores": version.group_scores,
            "pure_composite_score": version.pure_composite_score,
            "aggregate_confidence": version.aggregate_confidence,
            "signal_conditions": version.signal_conditions,
            "query_conditions": version.query_conditions,
            "tier_overrides": version.tier_overrides,
            "score_based_tier": version.score_based_tier,
            "final_tier": version.final_tier,
            "base_premium": version.base_premium,
            "modifiers_applied": [
                {
                    "name": m.name,
                    "factor": m.factor,
                    "premium_before": m.premium_before,
                    "premium_after": m.premium_after,
                    "source": m.source
                }
                for m in version.modifiers_applied
            ],
            "limit_premiums": version.limit_premiums,
            "final_premium": version.final_premium,
            "decision": version.decision.value,
            "auto_approve": version.auto_approve,
            "referral_reasons": version.referral_reasons,
            "notes": version.notes,
            "config_hash": version.config_hash,
            "created_at": version.created_at.isoformat(),
            "created_by": version.created_by
        }
    
    def version_from_dict(self, data: dict) -> ModelVersion:
        """
        Reconstruct ModelVersion from dictionary.
        """
        # Convert signal outputs
        signal_outputs = [
            SignalOutput(
                signal_id=s["signal_id"],
                signal_name=s["signal_name"],
                group_name=s["group_name"],
                raw_score=s["raw_score"],
                confidence=s["confidence"],
                signal_weight=s.get("signal_weight", 0),
                group_weight=s.get("group_weight", 0),
                weighted_score=s["weighted_score"],
                data_sources=s.get("data_sources", []),
                extracted_at=datetime.fromisoformat(s["extracted_at"]),
                conditions_triggered=s.get("conditions_triggered", [])
            )
            for s in data.get("signal_outputs", [])
        ]
        
        # Convert modifiers
        modifiers = [
            ModifierApplication(
                name=m["name"],
                factor=m["factor"],
                premium_before=m["premium_before"],
                premium_after=m["premium_after"],
                source=m.get("source", "unknown")
            )
            for m in data.get("modifiers_applied", [])
        ]
        
        return ModelVersion(
            version_id=data["version_id"],
            model_id=data["model_id"],
            version_number=data["version_number"],
            version_type=VersionType(data["version_type"]),
            entity_id=data["entity_id"],
            submission_data=data.get("submission_data", {}),
            direct_query_responses=data.get("direct_query_responses", {}),
            categorical_selections=data.get("categorical_selections", {}),
            signal_outputs=signal_outputs,
            group_scores=data.get("group_scores", {}),
            pure_composite_score=data.get("pure_composite_score", 0),
            aggregate_confidence=data.get("aggregate_confidence", 0),
            signal_conditions=data.get("signal_conditions", []),
            query_conditions=data.get("query_conditions", []),
            tier_overrides=data.get("tier_overrides", []),
            score_based_tier=data.get("score_based_tier", 0),
            final_tier=data.get("final_tier", 0),
            base_premium=data.get("base_premium", 0),
            modifiers_applied=modifiers,
            limit_premiums=data.get("limit_premiums", {}),
            final_premium=data.get("final_premium", 0),
            decision=DecisionType(data.get("decision", "refer")),
            auto_approve=data.get("auto_approve", False),
            referral_reasons=data.get("referral_reasons", []),
            notes=data.get("notes", []),
            config_hash=data.get("config_hash", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=data.get("created_by", "")
        )
