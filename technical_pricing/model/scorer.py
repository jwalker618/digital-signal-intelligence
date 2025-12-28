"""
DSI Model Layer - Model Scorer (Phase 4)

Executes Steps 4-6 of the workflow:
- Step 4: Signal Extraction (run all inference functions)
- Step 5: Pure Composite Score Calculation (weighted sum)
- Step 6: Signal Conditions Evaluation (check triggered conditions)

Connects the model layer to the signal architecture via the inference registry.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Any

from .types import (
    CoverageConfig,
    SignalGroupConfig,
    SignalFeatureConfig,
    SignalOutput,
    CategoricalOutput,
    ScoringResult,
    TriggeredCondition,
    ConditionAction,
    utcnow,
)

# Import from signal architecture
from ..signals.types import InferenceContext, SignalResult
from ..signals.inference.registry import (
    get_inference_function,
    InferenceFunctionNotFoundError,
)


logger = logging.getLogger("dsi.scorer")


class ScoringError(Exception):
    """Raised when scoring fails."""
    pass


class ModelScorer:
    """
    Executes signal scoring pipeline (Steps 4-6).

    This class bridges the model layer to the signal architecture,
    orchestrating extraction and scoring for all signals defined in config.
    """

    def __init__(
        self,
        max_workers: int = 10,
        default_score: float = 50.0,
        default_confidence: float = 0.5
    ):
        """
        Initialize ModelScorer.

        Args:
            max_workers: Maximum parallel workers for signal extraction
            default_score: Default score when extraction fails
            default_confidence: Default confidence when extraction fails
        """
        self.max_workers = max_workers
        self.default_score = default_score
        self.default_confidence = default_confidence

    def score_entity(
        self,
        entity_id: str,
        config: CoverageConfig,
        parallel: bool = True,
        context: Optional[InferenceContext] = None
    ) -> ScoringResult:
        """
        Execute Steps 4-6 for an entity.

        Args:
            entity_id: The entity to score
            config: Coverage configuration
            parallel: Whether to run extractions in parallel
            context: Optional inference context (created if not provided)

        Returns:
            ScoringResult with signal outputs, composite score, and conditions
        """
        start_time = time.time()

        # Create inference context if not provided
        if context is None:
            context = InferenceContext(
                configuration={},  # Will be populated by inference functions
                coverage=config.coverage,
                config_name=config.configuration,
            )

        # Step 4: Extract all signals
        signal_outputs, categorical_outputs = self.extract_signals(
            entity_id=entity_id,
            config=config,
            context=context,
            parallel=parallel,
        )

        # Step 5: Calculate pure composite score
        pure_composite_score, group_scores, confidence, coverage = self.calculate_composite(
            signal_outputs=signal_outputs,
            config=config,
        )

        # Step 6: Evaluate signal conditions
        conditions, tier_overrides, referrals, notes = self.evaluate_signal_conditions(
            signal_outputs=signal_outputs,
            group_scores=group_scores,
            config=config,
        )

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Scored entity {entity_id} in {elapsed_ms:.0f}ms: "
            f"composite={pure_composite_score:.0f}, "
            f"signals={len(signal_outputs)}, "
            f"conditions={len(conditions)}"
        )

        return ScoringResult(
            signal_outputs=signal_outputs,
            categorical_outputs=categorical_outputs,
            group_scores=group_scores,
            pure_composite_score=pure_composite_score,
            confidence=confidence,
            signal_coverage=coverage,
            conditions_triggered=conditions,
            tier_overrides=tier_overrides,
            referrals=referrals,
            notes=notes,
        )

    def extract_signals(
        self,
        entity_id: str,
        config: CoverageConfig,
        context: InferenceContext,
        parallel: bool = True
    ) -> Tuple[List[SignalOutput], List[CategoricalOutput]]:
        """
        Step 4: Run all inference functions.

        Args:
            entity_id: The entity to extract signals for
            config: Coverage configuration
            context: Inference context with cache
            parallel: Whether to run in parallel

        Returns:
            Tuple of (signal_outputs, categorical_outputs)
        """
        signal_outputs: List[SignalOutput] = []
        categorical_outputs: List[CategoricalOutput] = []

        # Collect all extraction tasks
        signal_tasks = []
        categorical_tasks = []

        # From signal groups and features
        for group in config.signal_groups:
            for feature in group.features:
                if feature.inference_function:
                    signal_tasks.append((group, feature))

        # From categorical groups
        for cat_group in config.categorical_groups:
            if cat_group.inference_function:
                categorical_tasks.append(cat_group)

        if parallel and (signal_tasks or categorical_tasks):
            # Parallel execution
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit signal extraction tasks
                signal_futures = {
                    executor.submit(
                        self._extract_signal,
                        entity_id, group, feature, context
                    ): (group, feature)
                    for group, feature in signal_tasks
                }

                # Submit categorical extraction tasks
                categorical_futures = {
                    executor.submit(
                        self._extract_categorical,
                        entity_id, cat_group, context
                    ): cat_group
                    for cat_group in categorical_tasks
                }

                # Collect signal results
                for future in as_completed(signal_futures):
                    group, feature = signal_futures[future]
                    try:
                        output = future.result()
                        signal_outputs.append(output)
                    except Exception as e:
                        logger.error(f"Signal extraction failed for {feature.id}: {e}")
                        signal_outputs.append(self._create_default_signal_output(
                            group, feature, str(e)
                        ))

                # Collect categorical results
                for future in as_completed(categorical_futures):
                    cat_group = categorical_futures[future]
                    try:
                        output = future.result()
                        categorical_outputs.append(output)
                    except Exception as e:
                        logger.error(f"Categorical extraction failed for {cat_group.id}: {e}")
                        categorical_outputs.append(self._create_default_categorical_output(
                            cat_group, str(e)
                        ))
        else:
            # Sequential execution
            for group, feature in signal_tasks:
                try:
                    output = self._extract_signal(entity_id, group, feature, context)
                    signal_outputs.append(output)
                except Exception as e:
                    logger.error(f"Signal extraction failed for {feature.id}: {e}")
                    signal_outputs.append(self._create_default_signal_output(
                        group, feature, str(e)
                    ))

            for cat_group in categorical_tasks:
                try:
                    output = self._extract_categorical(entity_id, cat_group, context)
                    categorical_outputs.append(output)
                except Exception as e:
                    logger.error(f"Categorical extraction failed for {cat_group.id}: {e}")
                    categorical_outputs.append(self._create_default_categorical_output(
                        cat_group, str(e)
                    ))

        return signal_outputs, categorical_outputs

    def _extract_signal(
        self,
        entity_id: str,
        group: SignalGroupConfig,
        feature: SignalFeatureConfig,
        context: InferenceContext
    ) -> SignalOutput:
        """
        Extract a single signal using its inference function.

        Args:
            entity_id: The entity to extract for
            group: Signal group configuration
            feature: Signal feature configuration
            context: Inference context

        Returns:
            SignalOutput with extracted score
        """
        start_time = time.time()

        try:
            # Get the inference function from registry
            inference_func = get_inference_function(feature.inference_function)
        except InferenceFunctionNotFoundError:
            logger.warning(f"Inference function not found: {feature.inference_function}")
            return self._create_default_signal_output(
                group, feature, f"Function not found: {feature.inference_function}"
            )

        try:
            # Run the inference function
            result: SignalResult = inference_func(entity_id, context)

            elapsed_ms = (time.time() - start_time) * 1000

            # Convert SignalResult to SignalOutput
            return SignalOutput(
                signal_id=feature.id,
                signal_name=feature.name,
                group_id=group.id,
                raw_score=result.score if result.score is not None else self.default_score,
                confidence=result.confidence if result.confidence else self.default_confidence,
                weighted_score=(result.score or self.default_score) * feature.weight,
                weight=feature.weight,
                data_sources=[result.metadata.get("extractor", "unknown")] if result.metadata else [],
                extracted_at=utcnow(),
                from_cache=result.metadata.get("from_cache", False) if result.metadata else False,
                execution_time_ms=result.execution_time_ms or elapsed_ms,
                error=result.error,
            )

        except Exception as e:
            logger.error(f"Inference function failed for {feature.id}: {e}")
            return self._create_default_signal_output(group, feature, str(e))

    def _extract_categorical(
        self,
        entity_id: str,
        cat_group,  # CategoricalGroupConfig
        context: InferenceContext
    ) -> CategoricalOutput:
        """
        Extract a categorical value using its inference function.

        Args:
            entity_id: The entity to extract for
            cat_group: Categorical group configuration
            context: Inference context

        Returns:
            CategoricalOutput with inferred category
        """
        try:
            inference_func = get_inference_function(cat_group.inference_function)
        except InferenceFunctionNotFoundError:
            return self._create_default_categorical_output(
                cat_group, f"Function not found: {cat_group.inference_function}"
            )

        try:
            result: SignalResult = inference_func(entity_id, context)

            # Get category from result
            category = result.category if result.category else "UNKNOWN"

            # Find the modifier for this category
            modifier = cat_group.get_modifier(category)

            # Find the label
            label = category
            for val in cat_group.values:
                if val.category == category:
                    label = val.label
                    break

            return CategoricalOutput(
                group_id=cat_group.id,
                group_name=cat_group.name,
                category=category,
                label=label,
                modifier=modifier,
                confidence=result.confidence if result.confidence else 0.8,
                extracted_at=utcnow(),
                error=result.error,
            )

        except Exception as e:
            return self._create_default_categorical_output(cat_group, str(e))

    def _create_default_signal_output(
        self,
        group: SignalGroupConfig,
        feature: SignalFeatureConfig,
        error: str
    ) -> SignalOutput:
        """Create a default signal output when extraction fails."""
        return SignalOutput(
            signal_id=feature.id,
            signal_name=feature.name,
            group_id=group.id,
            raw_score=self.default_score,
            confidence=self.default_confidence,
            weighted_score=self.default_score * feature.weight,
            weight=feature.weight,
            extracted_at=utcnow(),
            error=error,
        )

    def _create_default_categorical_output(
        self,
        cat_group,
        error: str
    ) -> CategoricalOutput:
        """Create a default categorical output when extraction fails."""
        # Use first value as default
        default_cat = cat_group.values[0] if cat_group.values else None

        return CategoricalOutput(
            group_id=cat_group.id,
            group_name=cat_group.name,
            category=default_cat.category if default_cat else "UNKNOWN",
            label=default_cat.label if default_cat else "Unknown",
            modifier=default_cat.modifier if default_cat else 1.0,
            confidence=0.0,
            extracted_at=utcnow(),
            error=error,
        )

    def calculate_composite(
        self,
        signal_outputs: List[SignalOutput],
        config: CoverageConfig
    ) -> Tuple[float, Dict[str, float], float, float]:
        """
        Step 5: Calculate pure composite score.

        The composite score is a weighted sum of group scores,
        where each group score is a weighted sum of signal scores.

        Score range: 0-1000 (signal scores 0-100 multiplied by 10)

        Args:
            signal_outputs: All extracted signal outputs
            config: Coverage configuration

        Returns:
            Tuple of (composite_score, group_scores, confidence, coverage)
        """
        # Group signals by group_id
        signals_by_group: Dict[str, List[SignalOutput]] = {}
        for output in signal_outputs:
            if output.group_id not in signals_by_group:
                signals_by_group[output.group_id] = []
            signals_by_group[output.group_id].append(output)

        # Calculate group scores
        group_scores: Dict[str, float] = {}
        total_confidence = 0.0
        total_signals = 0
        populated_signals = 0

        for group in config.signal_groups:
            group_signals = signals_by_group.get(group.id, [])

            if group_signals:
                # Weighted average within group
                total_weighted = sum(s.raw_score * s.weight for s in group_signals)
                total_weight = sum(s.weight for s in group_signals)

                if total_weight > 0:
                    group_score = total_weighted / total_weight
                else:
                    group_score = self.default_score

                # Track confidence
                group_confidence = sum(s.confidence for s in group_signals) / len(group_signals)
                total_confidence += group_confidence * len(group_signals)
                populated_signals += sum(1 for s in group_signals if s.error is None)
            else:
                group_score = self.default_score
                group_confidence = 0.0

            group_scores[group.id] = group_score
            total_signals += len(group.features)

        # Calculate composite score (0-1000 scale)
        composite_score = 0.0
        for group in config.signal_groups:
            group_score = group_scores.get(group.id, self.default_score)
            # Group score (0-100) * group weight * 10 = contribution to 0-1000 scale
            composite_score += group_score * group.weight * 10

        # Calculate overall confidence and coverage
        if total_signals > 0:
            overall_confidence = total_confidence / total_signals if total_signals > 0 else 0.5
            signal_coverage = populated_signals / total_signals
        else:
            overall_confidence = 0.5
            signal_coverage = 0.0

        return composite_score, group_scores, overall_confidence, signal_coverage

    def evaluate_signal_conditions(
        self,
        signal_outputs: List[SignalOutput],
        group_scores: Dict[str, float],
        config: CoverageConfig
    ) -> Tuple[List[TriggeredCondition], List[int], List[str], List[str]]:
        """
        Step 6: Evaluate conditions at signal_group and signal_feature levels.

        Conditions can trigger:
        - Tier override: Force to specific tier
        - Referral: Set auto_approve = false
        - Note: Post note for underwriter

        Args:
            signal_outputs: All extracted signals
            group_scores: Calculated group scores
            config: Coverage configuration

        Returns:
            Tuple of (conditions, tier_overrides, referrals, notes)
        """
        conditions: List[TriggeredCondition] = []
        tier_overrides: List[int] = []
        referrals: List[str] = []
        notes: List[str] = []

        # Create signal lookup by ID
        signal_by_id = {s.signal_id: s for s in signal_outputs}

        # Evaluate group-level conditions
        for group in config.signal_groups:
            if group.score_condition and group.conditions:
                group_score = group_scores.get(group.id, self.default_score)

                for condition in group.conditions:
                    triggered = self._check_condition(group_score, condition)

                    if triggered:
                        tc = TriggeredCondition(
                            source_type="signal_group",
                            source_id=group.id,
                            source_name=group.name,
                            score=group_score,
                            response=None,
                            action=condition.action,
                            action_value=condition.action_value,
                            note=f"{group.name}: {condition.action_value}" if condition.action == ConditionAction.NOTE else str(condition.action_value),
                        )
                        conditions.append(tc)

                        # Collect impacts
                        if condition.action == ConditionAction.TIER_OVERRIDE:
                            tier_overrides.append(int(condition.action_value))
                        elif condition.action == ConditionAction.REFERRAL:
                            referrals.append(str(condition.action_value))
                        elif condition.action == ConditionAction.NOTE:
                            notes.append(str(condition.action_value))

        # Evaluate feature-level conditions
        for group in config.signal_groups:
            for feature in group.features:
                if feature.score_condition and feature.conditions:
                    signal_output = signal_by_id.get(feature.id)
                    signal_score = signal_output.raw_score if signal_output else self.default_score

                    for condition in feature.conditions:
                        triggered = self._check_condition(signal_score, condition)

                        if triggered:
                            tc = TriggeredCondition(
                                source_type="signal_feature",
                                source_id=feature.id,
                                source_name=feature.name,
                                score=signal_score,
                                response=None,
                                action=condition.action,
                                action_value=condition.action_value,
                                note=f"{feature.name}: {condition.action_value}" if condition.action == ConditionAction.NOTE else str(condition.action_value),
                            )
                            conditions.append(tc)

                            # Collect impacts
                            if condition.action == ConditionAction.TIER_OVERRIDE:
                                tier_overrides.append(int(condition.action_value))
                            elif condition.action == ConditionAction.REFERRAL:
                                referrals.append(str(condition.action_value))
                            elif condition.action == ConditionAction.NOTE:
                                notes.append(str(condition.action_value))

                            # Also add conditions triggered from signal output
                            if signal_output:
                                signal_output.conditions_triggered.append(feature.id)

        logger.debug(
            f"Evaluated signal conditions: "
            f"{len(tier_overrides)} tier overrides, "
            f"{len(referrals)} referrals, "
            f"{len(notes)} notes"
        )

        return conditions, tier_overrides, referrals, notes

    def _check_condition(self, score: float, condition) -> bool:
        """
        Check if a score triggers a condition.

        Args:
            score: The score to check
            condition: SignalCondition to evaluate

        Returns:
            True if condition is triggered
        """
        if condition.condition_type == "max":
            threshold = float(condition.condition_value)
            if condition.inclusive:
                return score <= threshold
            else:
                return score < threshold

        elif condition.condition_type == "min":
            threshold = float(condition.condition_value)
            if condition.inclusive:
                return score >= threshold
            else:
                return score > threshold

        elif condition.condition_type == "equals":
            return score == float(condition.condition_value)

        elif condition.condition_type == "threshold":
            # Legacy support - treat as max
            threshold = float(condition.condition_value)
            return score < threshold

        return False


# Singleton instance for convenience
_default_scorer: Optional[ModelScorer] = None


def get_scorer() -> ModelScorer:
    """Get the default ModelScorer instance."""
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = ModelScorer()
    return _default_scorer
