"""
DSI Model Layer - Workflow Engine (Phase 4 + 6 + 7)

Orchestrates the complete 14-step workflow:

0. Website Discovery (Phase 6)
0a. Appetite Check — pre-qualification gate (underwriting authority)
1. Model Configuration Instantiation
2. Model Data File Creation
3. Minimum Viable Input Verification
4. Signal Extraction
5. Pure Composite Score Calculation
6. Signal Conditions Evaluation
7. Direct Query Response Evaluation
8. Maximum Tier Override Application
9. Final Tier Capture
10. Base Premium Generation
10.5. Traditional Modifiers (Phase 7 - OPTIONAL)
11. Modifier Application
12. Limit Band Scaling
13. Output Decision

This is the main entry point for running DSI assessments.
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple

from infrastructure.models.compiler import get_config, ConfigQuarantinedError
from infrastructure.models.config_schema import CoverageConfig, TierAction

from .types import (
    WorkflowResult,
    ModelVersion,
    DecisionType,
    DiscoveryOutput,
    DiscoveryConfidence,
    AppliedModifier,
    utcnow,
)
from .model_data import ModelDataManager, get_model_data_manager
from .scorer import ModelScorer, get_scorer
from .query_evaluator import QueryEvaluator, get_query_evaluator
from .appetite import evaluate_appetite
from .pricer import ModelPricer, get_pricer
from .rol_validator import ROLValidator
from .rol_recommender import ROLRecommender
from .modifiers import (
    TraditionalModifier,
    TraditionalModifierResult,
    LossHistoryModifier,
    ExposureModifier,
    ExternalRatingModifier,
)

from signal_architecture.signals.types import InferenceContext

# Phase 16: Loss Correlation Layer (optional, graceful import)
try:
    from layers.loss import (
        LossCorrelationScorer,
        LossCorrelationConfig,
        LossPropensityResult,
    )
    LOSS_CORRELATION_AVAILABLE = True
except ImportError:
    LOSS_CORRELATION_AVAILABLE = False
    LossCorrelationScorer = None
    LossCorrelationConfig = None
    LossPropensityResult = None
from signal_architecture.discovery.website_discovery import (
    WebsiteDiscoveryEngine,
    DiscoveryResult,
    ConfidenceLevel,
)


logger = logging.getLogger("dsi.workflow")


class WorkflowError(Exception):
    """Raised when workflow execution fails."""
    pass


class MissingInputError(Exception):
    """Raised when required inputs are missing."""
    def __init__(self, missing_fields: List[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Missing required inputs: {', '.join(missing_fields)}")


class WorkflowEngine:
    """
    Orchestrates the complete 14-step DSI model workflow.

    This engine coordinates all components:
    - WebsiteDiscoveryEngine: Entity website discovery (Step 0)
    - Compiled Pydantic configs: Configuration via compiler
    - ModelDataManager: Model data tracking
    - ModelScorer: Signal extraction and scoring
    - QueryEvaluator: Direct query evaluation
    - ModelPricer: Premium calculation
    - TraditionalModifiers: Optional actuarial modifiers (Step 10.5)
    """

    def __init__(
        self,
        data_manager: Optional[ModelDataManager] = None,
        scorer: Optional[ModelScorer] = None,
        query_evaluator: Optional[QueryEvaluator] = None,
        pricer: Optional[ModelPricer] = None,
        discovery_engine: Optional[WebsiteDiscoveryEngine] = None,
        traditional_modifiers: Optional[List[TraditionalModifier]] = None,
        enable_default_modifiers: bool = True,
        loss_correlation_scorer: Optional["LossCorrelationScorer"] = None,
        enable_loss_correlation: bool = True,
    ):
        """
        Initialize WorkflowEngine with dependencies.

        Args:
            data_manager: Model data manager (uses default if None)
            scorer: Model scorer (uses default if None)
            query_evaluator: Query evaluator (uses default if None)
            pricer: Model pricer (uses default if None)
            discovery_engine: Website discovery engine (uses default if None)
            traditional_modifiers: Optional list of traditional modifiers
            enable_default_modifiers: If True and no modifiers provided, use defaults
        """
        self.data_manager = data_manager or get_model_data_manager()
        self.scorer = scorer or get_scorer()
        self.query_evaluator = query_evaluator or get_query_evaluator()
        self.pricer = pricer or get_pricer()
        self.discovery_engine = discovery_engine or WebsiteDiscoveryEngine()

        # Traditional modifiers (Phase 7) - all optional
        if traditional_modifiers is not None:
            self.traditional_modifiers = traditional_modifiers
        elif enable_default_modifiers:
            # Default modifiers with sensible defaults
            self.traditional_modifiers = [
                LossHistoryModifier(enabled=True),
                ExposureModifier(enabled=True),
                ExternalRatingModifier(enabled=False),  # Disabled by default
            ]
        else:
            self.traditional_modifiers = []

        # Loss Correlation Scorer (Phase 16) - optional
        self.loss_correlation_scorer = loss_correlation_scorer
        self.enable_loss_correlation = enable_loss_correlation and LOSS_CORRELATION_AVAILABLE

    def _calculate_loss_propensity(
        self,
        signal_outputs: List[Any],
        config: CoverageConfig,
        previous_result: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Calculate loss propensity from signal outputs (Phase 16).

        This runs in parallel with risk scoring, using the same signals
        but applying loss-specific weighting and correlation logic.

        Args:
            signal_outputs: Signal extraction results from main pipeline
            config: Coverage configuration
            previous_result: Previous propensity result for trend analysis

        Returns:
            LossPropensityResult or None if loss correlation disabled
        """
        if not self.enable_loss_correlation:
            return None

        if not LOSS_CORRELATION_AVAILABLE:
            logger.debug("Loss correlation layer not available")
            return None

        # Check if loss correlation is enabled in config
        loss_config_data = getattr(config, 'loss_correlation', None)
        if loss_config_data is None:
            logger.debug("Loss correlation not configured for coverage")
            return None

        if isinstance(loss_config_data, dict) and not loss_config_data.get('enabled', False):
            logger.debug("Loss correlation disabled in config")
            return None

        try:
            # Create scorer if not provided
            if self.loss_correlation_scorer is None:
                if isinstance(loss_config_data, dict):
                    loss_config = LossCorrelationConfig.from_dict(loss_config_data)
                else:
                    loss_config = loss_config_data
                self.loss_correlation_scorer = LossCorrelationScorer(loss_config)

            # Calculate propensity
            loss_result = self.loss_correlation_scorer.calculate_propensity(
                signal_outputs,
                previous_result
            )

            logger.info(
                f"Loss propensity calculated: score={loss_result.loss_propensity_score:.1f}, "
                f"band={loss_result.loss_propensity_band.value}, "
                f"confidence={loss_result.loss_confidence:.2f}"
            )

            return loss_result

        except Exception as e:
            logger.warning(f"Loss propensity calculation failed: {e}")
            return None

    def run_workflow(
        self,
        entity_id: str,
        coverage: str,
        submission_data: Optional[Dict[str, Any]] = None,
        direct_query_responses: Optional[Dict[str, bool]] = None,
        categorical_selections: Optional[Dict[str, str]] = None,
        user: str = "system",
        config: Optional[CoverageConfig] = None,
        skip_input_validation: bool = False,
        # Discovery parameters (Step 0)
        entity_name: Optional[str] = None,
        domain_hint: Optional[str] = None,
        country_hint: Optional[str] = None,
        skip_discovery: bool = False
    ) -> WorkflowResult:
        """
        Execute the complete 14-step workflow.

        Args:
            entity_id: The entity being assessed
            coverage: Coverage domain (e.g., "aerospace")
            submission_data: Submission data (limits, TIV, etc.)
            direct_query_responses: Optional direct query answers
            categorical_selections: Optional category overrides
            user: User running the workflow
            config: Optional pre-loaded config (loaded if None)
            skip_input_validation: Skip Step 3 validation
            entity_name: Company name for discovery (defaults to entity_id)
            domain_hint: Optional domain hint (e.g., "example.com")
            country_hint: Optional country hint (e.g., "UK", "US")
            skip_discovery: Skip Step 0 discovery if domain is known

        Returns:
            WorkflowResult with complete assessment

        Raises:
            MissingInputError: If required inputs missing (Step 3)
            WorkflowError: If workflow execution fails
        """
        submission_data = submission_data or {}
        direct_query_responses = direct_query_responses or {}
        categorical_selections = categorical_selections or {}

        # Use entity_id as entity_name if not provided
        entity_name = entity_name or entity_id

        logger.info(f"Starting workflow for entity {entity_id}, coverage {coverage}")

        # Step 0: Website Discovery
        discovery_output = self._run_discovery(
            entity_name=entity_name,
            domain_hint=domain_hint,
            country_hint=country_hint,
            skip_discovery=skip_discovery
        )

        # Step 0a: Appetite Check — pre-qualification gate
        appetite_result = evaluate_appetite(coverage, submission_data)
        if not appetite_result.fit:
            logger.info(
                "Submission outside appetite for %s: %s",
                coverage, "; ".join(appetite_result.reasons),
            )
            return WorkflowResult(
                entity_id=entity_id,
                coverage=coverage,
                decision=DecisionType.DECLINE,
                notes=[f"OUTSIDE_APPETITE: {r}" for r in appetite_result.reasons],
            )

        # Step 1: Load Configuration (compiled Pydantic models)
        if config is None:
            try:
                config = get_config(coverage)
            except ConfigQuarantinedError as e:
                logger.error(
                    "Cannot process %s/%s: config is quarantined — %s",
                    entity_id, coverage, e.reason,
                )
                return WorkflowResult(
                    entity_id=entity_id,
                    coverage=coverage,
                    decision=DecisionType.DECLINE,
                    notes=[
                        "CONFIG_QUARANTINED: Configuration has failed health "
                        "checks and is disabled. {}".format(e.reason)
                    ],
                )
            logger.debug(f"Loaded config: {config.config_id} v{config.metadata.version}")

        # Step 2: Create Model Data File
        model_id = self.data_manager.create_model(
            entity_id=entity_id,
            config=config,
            submission_data=submission_data,
            user=user,
        )

        # Step 3: Verify Minimum Viable Inputs
        if not skip_input_validation:
            is_valid, missing_fields = self.verify_inputs(submission_data, config)
            if not is_valid:
                logger.warning(f"Missing inputs: {missing_fields}")
                # Return partial result with missing inputs
                return WorkflowResult(
                    entity_id=entity_id,
                    coverage=coverage,
                    is_valid=False,
                    missing_inputs=missing_fields,
                    decision=DecisionType.REFER,
                    notes=["Incomplete submission - missing required inputs"],
                )

        # Determine entity locale for jurisdiction-aware routing
        # Priority: country_hint > submission_data.country > detected from domain > default
        entity_locale, locale_source = self._determine_locale(
            country_hint=country_hint,
            submission_data=submission_data,
            discovered_domain=discovery_output.discovered_domain if discovery_output else None,
        )

        # Create inference context for signal extraction
        # Include discovery data so extractors can use the discovered website
        context = InferenceContext(
            configuration={},
            coverage=config.coverage_id,
            config_name=config.config_id,
            discovered_website=discovery_output.discovered_website if discovery_output else None,
            discovered_domain=discovery_output.discovered_domain if discovery_output else None,
            corporate_identity={
                "legal_name": discovery_output.legal_name,
                "parent_company": discovery_output.parent_company,
                "industry": discovery_output.industry,
            } if discovery_output and discovery_output.legal_name else None,
            discovery_confidence=discovery_output.confidence_score / 100.0 if discovery_output else 1.0,
            discovery_method=discovery_output.discovery_method if discovery_output else None,
            discovery_warnings=discovery_output.warnings if discovery_output else [],
            # Locale context for routing
            entity_locale=entity_locale,
            entity_country=submission_data.get('country') or submission_data.get('country_name'),
            locale_source=locale_source,
        )

        # Phase 2: Pre-check signal cache freshness.
        # If cached signals are stale, trigger a synchronous refresh before scoring.
        self._ensure_signal_freshness(entity_id, config)

        # Steps 4-6: Score Entity (Signal Extraction + Composite + Conditions)
        scoring_result = self.scorer.score_entity(
            entity_id=entity_id,
            config=config,
            context=context,
        )

        # Phase 16: Calculate Loss Propensity (parallel to risk scoring)
        # Uses same signal outputs with loss-specific weighting
        loss_propensity_result = self._calculate_loss_propensity(
            signal_outputs=scoring_result.signal_outputs,
            config=config,
            previous_result=None,  # Could load from history
        )

        # Step 7: Evaluate Direct Queries
        query_result = self.query_evaluator.evaluate_queries(
            responses=direct_query_responses,
            config=config,
        )

        # Use categorical outputs from scorer, or override with provided selections
        categorical_outputs = scoring_result.categorical_outputs
        # TODO: Handle categorical_selections overrides

        # Step 10.5: Calculate Traditional Modifiers (Phase 7 - OPTIONAL)
        # These are calculated but applied within the pricer
        traditional_modifier_results = self._calculate_traditional_modifiers(
            entity_id=entity_id,
            coverage=coverage,
            submission_data=submission_data,
            context=context,
            config=config,
        )

        # Convert traditional modifier results to query_modifiers format
        traditional_modifiers_for_pricer = [
            {
                "name": r.modifier_type,
                "factor": r.factor,
                "confidence": r.confidence,
                "source": r.modifier_type,  # e.g. "exposure", "loss_history"
                "source_id": r.modifier_type,
            }
            for r in traditional_modifier_results
            if r.has_impact  # Only include modifiers with actual impact
        ]

        # Combine signal, query, and traditional modifiers
        all_modifiers = scoring_result.modifiers + query_result.modifiers + traditional_modifiers_for_pricer

        # Add loss propensity modifier if available and significant
        if loss_propensity_result and loss_propensity_result.combined_loss_modifier != 1.0:
            loss_modifier = {
                "name": "loss_propensity",
                "factor": loss_propensity_result.combined_loss_modifier,
                "confidence": loss_propensity_result.loss_confidence,
                "source": "loss_propensity",
                "source_id": "loss_propensity",
            }
            all_modifiers.append(loss_modifier)

        # Steps 8-12: Calculate Premium
        pricing_result = self.pricer.price_submission(
            pure_composite_score=scoring_result.pure_composite_score,
            signal_tier_overrides=scoring_result.tier_overrides,
            query_tier_overrides=query_result.tier_overrides,
            query_modifiers=all_modifiers,
            categorical_outputs=categorical_outputs,
            submission_data=submission_data,
            config=config,
        )

        # Combine referral reasons and notes
        all_referrals = scoring_result.referrals + query_result.referrals
        all_notes = scoring_result.notes + query_result.notes

        # Add loss propensity referrals if triggered
        if loss_propensity_result:
            if loss_propensity_result.referral_triggered:
                all_referrals.extend(loss_propensity_result.referral_reasons)
            if loss_propensity_result.flags:
                all_notes.extend([f"Loss flag: {f}" for f in loss_propensity_result.flags])

        # Step 13: Determine Decision
        decision, auto_approve = self.determine_decision(
            final_tier=pricing_result.final_tier,
            referral_reasons=all_referrals,
            config=config,
        )

        # Create Model Version (audit trail)
        model_version = self.data_manager.create_version(
            model_id=model_id,
            version_type="initial",
            user=user,
            submission_data=submission_data,
            direct_query_responses=direct_query_responses,
            categorical_selections=categorical_selections,
            signal_outputs=scoring_result.signal_outputs,
            categorical_outputs=scoring_result.categorical_outputs,
            group_scores=scoring_result.group_scores,
            pure_composite_score=scoring_result.pure_composite_score,
            signal_conditions=scoring_result.conditions_triggered,
            query_conditions=query_result.conditions_triggered,
            tier_overrides=pricing_result.tier_overrides_considered,
            score_based_tier=pricing_result.score_based_tier,
            final_tier=pricing_result.final_tier,
            tier_label=pricing_result.tier_label,
            tier_margin=pricing_result.tier_margin,
            base_premium=pricing_result.base_premium,
            base_premium_method=pricing_result.base_premium_method,
            base_premium_derivation=pricing_result.base_premium_derivation,
            modifiers_applied=pricing_result.modifiers_applied,
            premium_after_modifiers=pricing_result.premium_after_modifiers,
            final_premium=pricing_result.final_premium,
            uncapped_premium=pricing_result.uncapped_premium,
            decision=decision,
            auto_approve=auto_approve,
            referral_reasons=all_referrals,
            notes=all_notes,
            confidence=scoring_result.confidence,
            signal_coverage=scoring_result.signal_coverage,
        )

        # Determine recommended option via ROL-driven dual recommendation
        recommended_limit = 0.0
        recommended_premium = pricing_result.final_premium
        if pricing_result.limit_premiums:
            rol_validator = ROLValidator()
            rol_recommender = ROLRecommender(validator=rol_validator)
            requested_limit = int(submission_data.get("limit", 0))
            dual_rec = rol_recommender.recommend(
                limit_premiums=pricing_result.limit_premiums,
                requested_limit=requested_limit,
            )
            # Use upper recommendation as the primary recommendation
            recommended_limit = float(dual_rec.upper.limit)
            recommended_premium = dual_rec.upper.premium

        logger.info(
            f"Workflow complete: score={scoring_result.pure_composite_score:.0f}, "
            f"tier={pricing_result.final_tier} ({pricing_result.tier_label}), "
            f"decision={decision.value}, "
            f"premium={pricing_result.final_premium:.0f}"
        )

        # Add discovery output to model version for audit trail
        model_version.discovery_output = discovery_output

        # Add loss propensity outputs to model version (Phase 16)
        if loss_propensity_result:
            model_version.loss_propensity_score = loss_propensity_result.loss_propensity_score
            model_version.severity_propensity_score = loss_propensity_result.severity_propensity_score
            model_version.loss_propensity_band = loss_propensity_result.loss_propensity_band.value
            model_version.severity_propensity_band = loss_propensity_result.severity_propensity_band.value
            model_version.loss_confidence = loss_propensity_result.loss_confidence
            model_version.loss_cohort_code = loss_propensity_result.cohort_id
            model_version.loss_cohort_name = loss_propensity_result.cohort_name
            model_version.loss_cohort_confidence = loss_propensity_result.cohort_confidence
            model_version.loss_frequency_multiplier = loss_propensity_result.frequency_multiplier
            model_version.loss_severity_multiplier = loss_propensity_result.severity_multiplier
            model_version.loss_combined_modifier = loss_propensity_result.combined_loss_modifier
            # Persist loss group scores for full reconstructability
            model_version.loss_group_scores = {
                group_name: {
                    "frequency_score": round(loss_propensity_result.frequency_group_scores.get(group_name, 0.0), 2),
                    "severity_score": round(loss_propensity_result.severity_group_scores.get(group_name, 0.0), 2),
                    "confidence": round(loss_propensity_result.group_confidences.get(group_name, 0.0), 4),
                }
                for group_name in set(
                    list(loss_propensity_result.frequency_group_scores.keys())
                    + list(loss_propensity_result.severity_group_scores.keys())
                )
            }
            model_version.loss_trend_direction = loss_propensity_result.trend_direction.value
            model_version.loss_previous_score = loss_propensity_result.previous_combined_score
            model_version.loss_score_velocity = loss_propensity_result.combined_score_velocity
            # Frequency / severity split
            model_version.loss_previous_frequency_score = getattr(loss_propensity_result, 'previous_frequency_score', None)
            model_version.loss_previous_severity_score = getattr(loss_propensity_result, 'previous_severity_score', None)
            model_version.loss_frequency_velocity = getattr(loss_propensity_result, 'frequency_score_velocity', None)
            model_version.loss_severity_velocity = getattr(loss_propensity_result, 'severity_score_velocity', None)
            model_version.loss_frequency_trend_direction = getattr(loss_propensity_result, 'frequency_trend_direction', None)
            model_version.loss_severity_trend_direction = getattr(loss_propensity_result, 'severity_trend_direction', None)
            model_version.loss_last_refresh = loss_propensity_result.calculated_at
            model_version.correlation_matrix_version = loss_propensity_result.correlation_matrix_version

        # Add exposure assessment outputs to model version
        exposure_result = next(
            (r for r in traditional_modifier_results if r.modifier_type == "exposure"),
            None,
        )
        if exposure_result and exposure_result.has_impact:
            primary_exposure = exposure_result.components.get("primary_exposure", 0.0)
            model_version.exposure_value = primary_exposure
            model_version.exposure_modifier = exposure_result.factor
            model_version.exposure_magnitude_score = exposure_result.components.get(
                "size_factor", 1.0
            ) * 50  # normalize to 0-100 scale
            model_version.exposure_complexity_score = exposure_result.components.get(
                "complexity_score", None
            )
            model_version.exposure_assessment_method = (
                "streamlined" if exposure_result.components.get("mode", 0.0) == 0.0
                else "full"
            )
            # Persist component factors for transparency
            model_version.exposure_components = {
                k: v for k, v in exposure_result.components.items()
                if k not in ("primary_exposure", "mode")
            }
            # Map exposure value to band label for display context
            # Band modifier is the ACTUAL pricing factor — not a separate lookup
            _EXPOSURE_BAND_LABELS = [
                (1, "Minimal",    0,              0),
                (1, "Small",      0,              50_000_000),
                (2, "Mid-Market", 50_000_000,     500_000_000),
                (3, "Large",      500_000_000,    5_000_000_000),
                (4, "Major",      5_000_000_000,  50_000_000_000),
                (5, "Mega",       50_000_000_000, None),
            ]
            matched = _EXPOSURE_BAND_LABELS[-1]  # default to Mega
            if primary_exposure <= 0:
                matched = _EXPOSURE_BAND_LABELS[0]
            else:
                for band in _EXPOSURE_BAND_LABELS[1:]:
                    bid, label, bmin, bmax = band
                    if bmax is None or primary_exposure < bmax:
                        matched = band
                        break
            bid, blabel, bmin, bmax = matched
            model_version.exposure_band_id = bid
            model_version.exposure_band_label = blabel
            model_version.exposure_band_boundaries = {
                "min_value": bmin,
                "max_value": bmax,
                "modifier": exposure_result.factor,  # actual pricing factor, not a display value
            }

        return WorkflowResult(
            entity_id=entity_id,
            coverage=coverage,
            model_version=model_version,
            decision=decision,
            auto_approve=auto_approve,
            referral_reasons=all_referrals,
            notes=all_notes,
            recommended_limit=recommended_limit,
            recommended_premium=recommended_premium,
            composite_score=scoring_result.pure_composite_score,
            tier=pricing_result.final_tier,
            tier_label=pricing_result.tier_label,
            confidence=scoring_result.confidence,
            is_valid=True,
            # Discovery summary (Step 0)
            discovered_domain=discovery_output.discovered_domain if discovery_output else None,
            discovery_confidence=discovery_output.confidence.value if discovery_output else None,
            discovery_warnings=discovery_output.warnings if discovery_output else [],
        )

    def verify_inputs(
        self,
        submission_data: Dict[str, Any],
        config: CoverageConfig
    ) -> Tuple[bool, List[str]]:
        """
        Step 3: Verify minimum viable inputs are present.

        Args:
            submission_data: Provided submission data
            config: Coverage configuration

        Returns:
            Tuple of (is_valid, missing_fields)
        """
        missing = []

        # Check required inputs from config metadata
        mvi = config.metadata.minimum_viable_input
        if mvi:
            # Pydantic schema: list of MinimumViableInputField objects
            required = [item.field for item in mvi]
        else:
            # Default required fields
            required = ["entity_id", "limit"]

        for field in required:
            # Normalize field name (remove spaces, make lowercase)
            normalized = field.lower().replace(" ", "_").replace("(", "").replace(")", "")

            # Check various forms of the field
            found = False
            for key in submission_data.keys():
                if normalized in key.lower():
                    if submission_data[key]:  # Has a value
                        found = True
                        break

            if not found:
                missing.append(field)

        return len(missing) == 0, missing

    def determine_decision(
        self,
        final_tier: int,
        referral_reasons: List[str],
        config: CoverageConfig
    ) -> Tuple[DecisionType, bool]:
        """
        Step 13: Determine final decision.

        Decision logic:
        - APPROVE: auto_approve tier and no referrals
        - DECLINE: auto_decline tier or tier 5
        - REFER: requires underwriter review

        Args:
            final_tier: Final tier after overrides
            referral_reasons: Accumulated referral reasons
            config: Coverage configuration

        Returns:
            Tuple of (decision, auto_approve)
        """
        # Get tier band from compiled config
        tier_band = config.get_tier_band(final_tier)

        if tier_band is None:
            # Default to refer if no tier config
            return DecisionType.REFER, False

        # Check for auto-decline
        if tier_band.interpretation.action == TierAction.DECLINE:
            return DecisionType.DECLINE, False

        # Check for referral reasons
        if referral_reasons:
            return DecisionType.REFER, False

        # Check for auto-approve
        if tier_band.interpretation.action == TierAction.APPROVE:
            return DecisionType.APPROVE, True

        # Default to refer
        return DecisionType.REFER, False

    def _calculate_traditional_modifiers(
        self,
        entity_id: str,
        coverage: str,
        submission_data: Dict[str, Any],
        context: InferenceContext,
        config: Optional[CoverageConfig] = None,
    ) -> List[TraditionalModifierResult]:
        """
        Step 10.5: Calculate traditional pricing modifiers (Phase 7).

        Runs all configured traditional modifiers and collects results.
        Modifiers that lack data return neutral results (factor=1.0).

        Args:
            entity_id: The entity being priced
            coverage: Coverage type
            submission_data: Submission data from broker
            context: Inference context with discovery data
            config: Optional coverage configuration

        Returns:
            List of TraditionalModifierResult from each modifier
        """
        if not self.traditional_modifiers:
            return []

        results: List[TraditionalModifierResult] = []

        for modifier in self.traditional_modifiers:
            if not modifier.is_enabled:
                continue

            try:
                result = modifier.calculate(
                    entity_id=entity_id,
                    coverage=coverage,
                    submission_data=submission_data,
                    context=context,
                    config=config,
                )
                results.append(result)

                if result.has_impact:
                    logger.info(
                        f"Traditional modifier {result.modifier_type}: "
                        f"factor={result.factor:.3f}, confidence={result.confidence:.2f}"
                    )
                else:
                    logger.debug(
                        f"Traditional modifier {result.modifier_type} skipped: "
                        f"{result.notes[0] if result.notes else 'no data'}"
                    )

            except Exception as e:
                logger.error(f"Error in {modifier.modifier_type} modifier: {e}")
                # Add neutral result on error
                results.append(TraditionalModifierResult.neutral(
                    modifier.modifier_type,
                    f"Error: {str(e)}"
                ))

        return results

    def _run_discovery(
        self,
        entity_name: str,
        domain_hint: Optional[str] = None,
        country_hint: Optional[str] = None,
        skip_discovery: bool = False
    ) -> Optional[DiscoveryOutput]:
        """
        Step 0: Run website discovery for the entity.

        Identifies the correct corporate website before signal extraction
        begins. This enables extractors to fetch data from the entity's
        actual website rather than relying on guesses.

        Args:
            entity_name: Company name to search for
            domain_hint: Optional known domain (skips discovery if high confidence)
            country_hint: Optional country for regional TLD prioritization
            skip_discovery: If True, skip discovery entirely

        Returns:
            DiscoveryOutput with discovery results, or None if skipped
        """
        if skip_discovery:
            logger.debug(f"Discovery skipped for {entity_name}")
            return DiscoveryOutput(
                entity_name=entity_name,
                domain_hint=domain_hint,
                skipped=True
            )

        logger.info(f"Step 0: Discovering website for {entity_name}")
        start_time = time.time()

        try:
            # Run discovery
            result: DiscoveryResult = self.discovery_engine.discover(
                company_name=entity_name,
                domain_hint=domain_hint,
                country_hint=country_hint
            )

            execution_time_ms = (time.time() - start_time) * 1000

            # Map discovery confidence level to our enum
            confidence_map = {
                ConfidenceLevel.HIGH: DiscoveryConfidence.HIGH,
                ConfidenceLevel.MEDIUM: DiscoveryConfidence.MEDIUM,
                ConfidenceLevel.LOW: DiscoveryConfidence.LOW,
                ConfidenceLevel.UNVERIFIED: DiscoveryConfidence.UNVERIFIED,
            }

            # Extract primary website info
            primary = result.primary_website
            discovered_website = primary.url if primary else None
            discovered_domain = primary.domain if primary else None
            confidence_score = primary.confidence_score if primary else 0.0
            discovery_method = primary.discovery_method.value if primary else None

            # Extract corporate identity info
            identity = result.company_identity
            legal_name = identity.legal_name if identity else None
            parent_company = (
                identity.parent_company.input_name
                if identity and identity.parent_company else None
            )

            output = DiscoveryOutput(
                entity_name=entity_name,
                domain_hint=domain_hint,
                country_hint=country_hint,
                discovered_website=discovered_website,
                discovered_domain=discovered_domain,
                confidence=confidence_map.get(result.confidence, DiscoveryConfidence.UNVERIFIED),
                confidence_score=confidence_score,
                legal_name=legal_name,
                parent_company=parent_company,
                discovery_method=discovery_method,
                discovery_methods_used=[m.value for m in result.discovery_methods_used],
                execution_time_ms=execution_time_ms,
                requires_manual_review=result.requires_manual_review,
                review_reasons=result.manual_review_reasons,
                warnings=result.warnings,
                candidates_found=len(result.all_candidates),
            )

            logger.info(
                f"Discovery complete: {discovered_domain} "
                f"(confidence: {result.confidence.value}, "
                f"candidates: {len(result.all_candidates)})"
            )

            return output

        except Exception as e:
            logger.error(f"Discovery failed for {entity_name}: {e}")
            execution_time_ms = (time.time() - start_time) * 1000
            return DiscoveryOutput(
                entity_name=entity_name,
                domain_hint=domain_hint,
                country_hint=country_hint,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )

    def _ensure_signal_freshness(
        self,
        entity_id: str,
        config,
    ) -> None:
        """
        Phase 2: Check SignalCache freshness and trigger sync refresh if stale.

        Queries the telemetry layer to verify that cached signals are
        within their volatility-based TTL. If any signals are stale and
        the database is available, triggers a synchronous refresh so the
        subsequent scoring step gets up-to-date data.
        """
        try:
            from infrastructure.workers.telemetry import (
                check_signal_freshness,
                synchronous_refresh,
            )

            # Get signal IDs from compiled config
            signal_ids = [sig.id for sig in config.signal_registry
                          if sig.three_layer_assessment]
            if not signal_ids:
                return

            freshness = check_signal_freshness(entity_id, signal_ids)
            stale_ids = [sid for sid, is_fresh in freshness.items() if not is_fresh]

            if stale_ids:
                logger.info(
                    f"Entity {entity_id}: {len(stale_ids)}/{len(signal_ids)} "
                    f"signals stale, triggering sync refresh"
                )
                synchronous_refresh(entity_id, stale_ids, timeout_seconds=20)
        except Exception as e:
            # Non-fatal: scoring will still run with inference functions
            logger.debug(f"Signal freshness check skipped: {e}")

    def _determine_locale(
        self,
        country_hint: Optional[str],
        submission_data: Dict[str, Any],
        discovered_domain: Optional[str],
    ) -> tuple:
        """
        Determine entity locale for jurisdiction-aware routing.

        Priority order:
        1. country_hint parameter (explicit override)
        2. submission_data country/country_code field
        3. TLD detection from discovered domain
        4. Default to 'US'

        Args:
            country_hint: Explicit country hint
            submission_data: Submission data dict
            discovered_domain: Domain from discovery

        Returns:
            Tuple of (locale_code, source) where source is
            'hint', 'submission', 'domain', or 'default'
        """
        # 1. Check country_hint
        if country_hint:
            return country_hint.upper(), 'hint'

        # 2. Check submission_data for country fields
        country_code = submission_data.get('country_code') or submission_data.get('country')
        if country_code and isinstance(country_code, str) and len(country_code) <= 3:
            return country_code.upper(), 'submission'

        # 3. Detect from domain TLD
        if discovered_domain:
            # Import routing module for TLD detection
            try:
                from signals.routing import TLD_TO_LOCALE

                # Extract TLD
                parts = discovered_domain.lower().strip().split('.')

                # Check compound TLDs first (e.g., co.uk)
                if len(parts) >= 2:
                    compound_tld = '.'.join(parts[-2:])
                    if compound_tld in TLD_TO_LOCALE:
                        locale = TLD_TO_LOCALE[compound_tld]
                        if locale:  # Some TLDs map to None (generic)
                            return locale, 'domain'

                # Check simple TLD
                tld = parts[-1] if parts else None
                if tld and tld in TLD_TO_LOCALE:
                    locale = TLD_TO_LOCALE[tld]
                    if locale:
                        return locale, 'domain'
            except ImportError:
                logger.debug("Routing module not available for TLD detection")

        # 4. Default
        return 'US', 'default'

    def process_referral(
        self,
        model_id: str,
        reviewer: str,
        decision: str,
        adjustments: Optional[Dict[str, Any]] = None,
        notes: Optional[List[str]] = None
    ) -> WorkflowResult:
        """
        Handle referral review and create new model version.

        Args:
            model_id: The model being reviewed
            reviewer: User performing review
            decision: Review decision ('approve', 'decline', 'modify')
            adjustments: Optional adjustments (tier override, premium adjustment)
            notes: Optional reviewer notes

        Returns:
            WorkflowResult with updated assessment
        """
        adjustments = adjustments or {}
        notes = notes or []

        # Get latest version
        latest = self.data_manager.get_latest_version(model_id)

        # Determine new decision
        if decision == "approve":
            new_decision = DecisionType.APPROVE
            auto_approve = False  # Manual approval, not auto
        elif decision == "decline":
            new_decision = DecisionType.DECLINE
            auto_approve = False
        else:
            new_decision = DecisionType.REFER
            auto_approve = False

        # Apply adjustments
        final_tier = adjustments.get("tier_override", latest.final_tier)
        final_premium = adjustments.get("premium_override", latest.final_premium)

        # Create new version
        new_version = self.data_manager.create_version(
            model_id=model_id,
            version_type="referral_review",
            user=reviewer,
            submission_data=latest.submission_data,
            direct_query_responses=latest.direct_query_responses,
            categorical_selections=latest.categorical_selections,
            signal_outputs=latest.signal_outputs,
            categorical_outputs=latest.categorical_outputs,
            group_scores=latest.group_scores,
            pure_composite_score=latest.pure_composite_score,
            signal_conditions=latest.signal_conditions,
            query_conditions=latest.query_conditions,
            tier_overrides=latest.tier_overrides + ([adjustments.get("tier_override")] if "tier_override" in adjustments else []),
            score_based_tier=latest.score_based_tier,
            final_tier=final_tier,
            tier_label=latest.tier_label,
            base_premium=latest.base_premium,
            base_premium_method=latest.base_premium_method,
            modifiers_applied=latest.modifiers_applied,
            premium_after_modifiers=latest.premium_after_modifiers,
            final_premium=final_premium,
            decision=new_decision,
            auto_approve=auto_approve,
            referral_reasons=latest.referral_reasons,
            notes=latest.notes + notes + [f"Reviewed by {reviewer}: {decision}"],
            confidence=latest.confidence,
            signal_coverage=latest.signal_coverage,
        )

        return WorkflowResult(
            entity_id=latest.entity_id,
            coverage=latest.coverage,
            model_version=new_version,
            decision=new_decision,
            auto_approve=auto_approve,
            referral_reasons=latest.referral_reasons,
            notes=new_version.notes,
            recommended_premium=final_premium,
            composite_score=latest.pure_composite_score,
            tier=final_tier,
            tier_label=latest.tier_label,
            confidence=latest.confidence,
            is_valid=True,
        )


# Singleton instance for convenience
_default_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get the default WorkflowEngine instance."""
    global _default_engine
    if _default_engine is None:
        _default_engine = WorkflowEngine()
    return _default_engine


def run_assessment(
    entity_id: str,
    coverage: str,
    submission_data: Optional[Dict[str, Any]] = None,
    direct_query_responses: Optional[Dict[str, bool]] = None,
    user: str = "api",
    entity_name: Optional[str] = None,
    domain_hint: Optional[str] = None,
    country_hint: Optional[str] = None,
    skip_discovery: bool = False,
    skip_input_validation: bool = False,
) -> WorkflowResult:
    """
    Convenience function to run a full assessment.

    Args:
        entity_id: Entity to assess
        coverage: Coverage domain
        submission_data: Submission data
        direct_query_responses: Optional query responses
        user: User running assessment
        entity_name: Company name for discovery (defaults to entity_id)
        domain_hint: Optional domain hint (e.g., "example.com")
        country_hint: Optional country hint (e.g., "UK", "US")
        skip_discovery: Skip Step 0 discovery if domain is known
        skip_input_validation: Skip Step 3 minimum viable input validation

    Returns:
        WorkflowResult with complete assessment
    """
    engine = get_workflow_engine()
    return engine.run_workflow(
        entity_id=entity_id,
        coverage=coverage,
        submission_data=submission_data,
        direct_query_responses=direct_query_responses,
        user=user,
        entity_name=entity_name,
        domain_hint=domain_hint,
        country_hint=country_hint,
        skip_discovery=skip_discovery,
        skip_input_validation=skip_input_validation,
    )
