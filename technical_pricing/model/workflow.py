"""
DSI Workflow Engine

Orchestrates the complete 13-step model workflow.

Steps 1-2: Configuration and model data initialization
Step 3: Input verification
Steps 4-6: Signal scoring
Step 7: Query evaluation
Steps 8-12: Pricing
Step 13: Decision output
"""

from datetime import datetime
from typing import Callable

from .types import (
    CoverageConfig,
    ModelVersion,
    WorkflowResult,
    SubmissionRequest,
    ScoringResult,
    QueryEvaluationResult,
    PricingResult,
    DecisionType,
    VersionType,
)
from .config_manager import ConfigManager
from .model_data import ModelDataManager
from .scorer import ModelScorer
from .query_evaluator import QueryEvaluator
from .pricer import ModelPricer


class WorkflowEngine:
    """
    Orchestrates complete model workflow.
    
    This is the main entry point for running the DSI model.
    All components are injected for testability and flexibility.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        data_manager: ModelDataManager,
        scorer: ModelScorer,
        query_evaluator: QueryEvaluator,
        pricer: ModelPricer
    ):
        """
        Initialize workflow engine with dependencies.
        
        Args:
            config_manager: Manages configuration loading/storage
            data_manager: Manages model data and versions
            scorer: Executes signal scoring (Steps 4-6)
            query_evaluator: Evaluates direct queries (Step 7)
            pricer: Calculates premiums (Steps 8-12)
        """
        self.config_manager = config_manager
        self.data_manager = data_manager
        self.scorer = scorer
        self.query_evaluator = query_evaluator
        self.pricer = pricer
    
    # =========================================================================
    # MAIN WORKFLOW
    # =========================================================================
    
    def run_workflow(
        self,
        request: SubmissionRequest
    ) -> WorkflowResult:
        """
        Execute complete 13-step workflow.
        
        Args:
            request: Submission request with all inputs
        
        Returns:
            WorkflowResult with decision and premium options
        """
        # Step 1: Load configuration
        try:
            config = self.config_manager.load_from_file(request.coverage)
        except FileNotFoundError as e:
            return self._error_result(
                request=request,
                error=f"Configuration not found: {e}"
            )
        
        # Validate configuration
        config_errors = self.config_manager.validate_config(config)
        if config_errors:
            return self._error_result(
                request=request,
                error=f"Invalid configuration: {config_errors}"
            )
        
        # Step 2: Create model data file
        model_id = self.data_manager.create_model(
            entity_id=request.entity_id,
            coverage=request.coverage,
            config_hash=config.config_hash,
            user=request.user
        )
        
        # Create initial version
        version = self.data_manager.create_initial_version(
            model_id=model_id,
            entity_id=request.entity_id,
            submission_data=request.submission_data,
            direct_query_responses=request.direct_query_responses,
            categorical_selections=request.categorical_selections,
            config_hash=config.config_hash,
            user=request.user
        )
        
        # Step 3: Verify minimum viable inputs
        is_valid, missing_inputs = self.config_manager.verify_required_inputs(
            config=config,
            submission_data=request.submission_data
        )
        
        if not is_valid:
            return WorkflowResult(
                model_version=version,
                decision=DecisionType.REFER,
                auto_approve=False,
                referral_reasons=["Missing required inputs"],
                missing_inputs=missing_inputs
            )
        
        # Steps 4-6: Score entity
        scoring_result = self.scorer.score_entity(
            entity_id=request.entity_id,
            config=config,
            submission_data=request.submission_data
        )
        
        # Update version with scoring
        version = self.data_manager.update_version_scoring(
            version_id=version.version_id,
            scoring_result=scoring_result
        )
        
        # Step 7: Evaluate direct queries
        query_result = self.query_evaluator.evaluate_queries(
            responses=request.direct_query_responses,
            config=config
        )
        
        # Update version with query results
        version = self.data_manager.update_version_queries(
            version_id=version.version_id,
            query_result=query_result
        )
        
        # Steps 8-12: Calculate pricing
        pricing_result = self.pricer.price_submission(
            pure_composite_score=scoring_result.pure_composite_score,
            signal_tier_overrides=scoring_result.tier_overrides_from_signals,
            query_tier_overrides=query_result.tier_overrides,
            query_modifiers=query_result.modifiers,
            categorical_selections=request.categorical_selections,
            submission_data=request.submission_data,
            config=config
        )
        
        # Update version with pricing
        version = self.data_manager.update_version_pricing(
            version_id=version.version_id,
            pricing_result=pricing_result
        )
        
        # Step 13: Determine decision
        all_referral_reasons = (
            scoring_result.referrals_from_signals +
            query_result.referrals
        )
        all_notes = (
            scoring_result.notes_from_signals +
            query_result.notes
        )
        
        decision, auto_approve = self.determine_decision(
            final_tier=pricing_result.final_tier,
            referral_reasons=all_referral_reasons,
            config=config
        )
        
        # Update version with decision
        version = self.data_manager.update_version_decision(
            version_id=version.version_id,
            decision=decision,
            auto_approve=auto_approve,
            referral_reasons=all_referral_reasons,
            notes=all_notes
        )
        
        # Build result
        premium_options = pricing_result.limit_premiums
        recommended_limit = self._get_recommended_limit(premium_options, config)
        recommended_premium = premium_options.get(recommended_limit, 0)
        
        return WorkflowResult(
            model_version=version,
            decision=decision,
            auto_approve=auto_approve,
            referral_reasons=all_referral_reasons,
            notes=all_notes,
            premium_options=premium_options,
            recommended_limit=recommended_limit,
            recommended_premium=recommended_premium
        )
    
    # =========================================================================
    # STEP 3: INPUT VERIFICATION
    # =========================================================================
    
    def verify_inputs(
        self,
        submission_data: dict,
        config: CoverageConfig
    ) -> tuple[bool, list[str]]:
        """
        Verify minimum viable inputs are present.
        
        Delegates to config_manager.
        """
        return self.config_manager.verify_required_inputs(config, submission_data)
    
    # =========================================================================
    # STEP 13: DECISION DETERMINATION
    # =========================================================================
    
    def determine_decision(
        self,
        final_tier: int,
        referral_reasons: list[str],
        config: CoverageConfig
    ) -> tuple[DecisionType, bool]:
        """
        Determine final decision (Step 13).
        
        Decision logic:
        - If tier has decision='decline' â DECLINE
        - If any referral reasons â REFER, auto_approve=False
        - If tier has decision='refer' â REFER, auto_approve=False
        - Otherwise â APPROVE, auto_approve=True
        
        Returns:
            Tuple of (decision, auto_approve)
        """
        # Get tier configuration
        tier_config = None
        for t in config.tier_thresholds:
            if t.tier == final_tier:
                tier_config = t
                break
        
        # Check tier-level decision
        if tier_config:
            if tier_config.decision == DecisionType.DECLINE:
                return (DecisionType.DECLINE, False)
            
            if tier_config.decision == DecisionType.REFER:
                return (DecisionType.REFER, False)
        
        # Check for referral triggers
        if referral_reasons:
            return (DecisionType.REFER, False)
        
        # Default to approve
        return (DecisionType.APPROVE, True)
    
    # =========================================================================
    # REFERRAL PROCESSING
    # =========================================================================
    
    def process_referral(
        self,
        model_id: str,
        reviewer: str,
        decision: str,
        adjustments: dict | None = None
    ) -> WorkflowResult:
        """
        Handle referral review (creates new model version).
        
        Args:
            model_id: ID of the model being reviewed
            reviewer: User reviewing the referral
            decision: Reviewer's decision ('approve', 'decline', 'refer')
            adjustments: Optional adjustments (tier, notes, modifiers)
        
        Returns:
            WorkflowResult with updated decision
        """
        # Get latest version
        latest = self.data_manager.get_latest_version(model_id)
        if latest is None:
            raise ValueError(f"Model not found: {model_id}")
        
        # Create referral review version
        adjustments = adjustments or {}
        adjustments['decision'] = decision
        
        version = self.data_manager.create_referral_version(
            model_id=model_id,
            reviewer=reviewer,
            adjustments=adjustments
        )
        
        # Update decision
        final_decision = DecisionType(decision)
        auto_approve = (final_decision == DecisionType.APPROVE)
        
        version = self.data_manager.update_version_decision(
            version_id=version.version_id,
            decision=final_decision,
            auto_approve=auto_approve,
            notes=[f"Reviewed by {reviewer}"]
        )
        
        return WorkflowResult(
            model_version=version,
            decision=final_decision,
            auto_approve=auto_approve,
            referral_reasons=version.referral_reasons,
            notes=version.notes,
            premium_options=version.limit_premiums,
            recommended_limit=list(version.limit_premiums.keys())[0] if version.limit_premiums else 0,
            recommended_premium=list(version.limit_premiums.values())[0] if version.limit_premiums else 0
        )
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _error_result(
        self,
        request: SubmissionRequest,
        error: str
    ) -> WorkflowResult:
        """Create an error result"""
        # Create a minimal version for error tracking
        version = ModelVersion(
            version_id="error",
            model_id="error",
            version_number=0,
            version_type=VersionType.INITIAL,
            entity_id=request.entity_id,
            decision=DecisionType.DECLINE
        )
        
        return WorkflowResult(
            model_version=version,
            decision=DecisionType.DECLINE,
            auto_approve=False,
            validation_errors=[error]
        )
    
    def _get_recommended_limit(
        self,
        premium_options: dict[float, float],
        config: CoverageConfig
    ) -> float:
        """Get recommended limit from options"""
        if not premium_options:
            return 0.0
        
        # Default to middle limit option
        limits = sorted(premium_options.keys())
        if len(limits) >= 3:
            return limits[len(limits) // 2]
        return limits[0]
    
    def get_workflow_summary(self, result: WorkflowResult) -> dict:
        """
        Get summary of workflow execution for API response.
        """
        version = result.model_version
        
        return {
            'model_id': version.model_id,
            'version_id': version.version_id,
            'version_number': version.version_number,
            'entity_id': version.entity_id,
            'decision': result.decision.value,
            'auto_approve': result.auto_approve,
            'scoring': {
                'composite_score': version.pure_composite_score,
                'confidence': version.aggregate_confidence,
                'score_based_tier': version.score_based_tier,
                'final_tier': version.final_tier
            },
            'pricing': {
                'base_premium': version.base_premium,
                'final_premium': version.final_premium,
                'modifiers_count': len(version.modifiers_applied)
            },
            'premium_options': result.premium_options,
            'recommended': {
                'limit': result.recommended_limit,
                'premium': result.recommended_premium
            },
            'referral_reasons': result.referral_reasons,
            'notes': result.notes,
            'is_valid': result.is_valid,
            'validation_errors': result.validation_errors,
            'missing_inputs': result.missing_inputs
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_workflow_engine(
    config_dir: str = "coverages",
    inference_registry: dict[str, Callable] | None = None
) -> WorkflowEngine:
    """
    Factory function to create a fully configured workflow engine.
    
    Args:
        config_dir: Directory containing coverage YAML files
        inference_registry: Dict mapping inference function names to callables
    
    Returns:
        Configured WorkflowEngine
    """
    config_manager = ConfigManager(config_dir=config_dir)
    data_manager = ModelDataManager()
    scorer = ModelScorer(inference_registry=inference_registry or {})
    query_evaluator = QueryEvaluator()
    pricer = ModelPricer()
    
    return WorkflowEngine(
        config_manager=config_manager,
        data_manager=data_manager,
        scorer=scorer,
        query_evaluator=query_evaluator,
        pricer=pricer
    )


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def run_model(
    entity_id: str,
    coverage: str,
    submission_data: dict,
    direct_query_responses: dict[str, bool] | None = None,
    categorical_selections: dict[str, str] | None = None,
    user: str = "system",
    config_dir: str = "coverages",
    inference_registry: dict[str, Callable] | None = None
) -> WorkflowResult:
    """
    Convenience function to run the complete model workflow.
    
    Creates engine, builds request, and runs workflow.
    
    Args:
        entity_id: Entity being evaluated
        coverage: Coverage type (e.g., 'aerospace', 'cyber')
        submission_data: Submission data including rate basis values
        direct_query_responses: Responses to direct queries
        categorical_selections: Selected categories
        user: User running the model
        config_dir: Directory containing YAML configs
        inference_registry: Inference function registry
    
    Returns:
        WorkflowResult with decision and premiums
    """
    engine = create_workflow_engine(
        config_dir=config_dir,
        inference_registry=inference_registry
    )
    
    request = SubmissionRequest(
        entity_id=entity_id,
        coverage=coverage,
        submission_data=submission_data,
        direct_query_responses=direct_query_responses or {},
        categorical_selections=categorical_selections or {},
        user=user
    )
    
    return engine.run_workflow(request)
