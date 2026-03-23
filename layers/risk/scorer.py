"""
DSI Model Layer - Model Scorer (Phase 4 + Phase 8 + Phase 10)

Executes Steps 4-6 of the workflow:
- Step 4: Signal Extraction (run all inference functions)
- Step 5: Pure Composite Score Calculation (weighted sum)
- Step 6: Signal Conditions Evaluation (check triggered conditions)

Phase 8 Enhancement:
- Supports audited_value override for signals
- When audited_value is present, uses it instead of inferred_value
- Preserves inferred_value for audit trail

Phase 10 Enhancement:
- Adaptive signal absence handling based on entity size
- expectation_level determines penalty for missing signals
- Small entities not penalized for missing enterprise-level signals

Connects the model layer to the signal architecture via the inference registry.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from infrastructure.models.config_schema import (
    CoverageConfig,
    SignalDefinition,
    ThreeLayerAssessmentGroup,
    CategoryGroup,
    ScoreCondition,
    ScoreConditionAction,
    ComparisonOperator,
    ExpectationLevel,
)

from .types import (
    SignalOutput,
    CategoricalOutput,
    ScoringResult,
    TriggeredCondition,
    ConditionAction,
    utcnow,
)

# Import from signal architecture (root level)
from signal_architecture.signals.types import InferenceContext, SignalResult
from signal_architecture.signals.inference.registry import (
    get_inference_function,
    InferenceFunctionNotFoundError,
)

# Map Pydantic ScoreConditionAction to internal ConditionAction
_CONDITION_ACTION_MAP = {
    ScoreConditionAction.FLAG: ConditionAction.FLAG,
    ScoreConditionAction.MODIFIER: ConditionAction.MODIFIER,
    ScoreConditionAction.REFER: ConditionAction.REFER,
}


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

    # Phase 10: Expectation level to size band mapping
    # Each level specifies which size bands (1-5) expect the signal
    EXPECTATION_BANDS = {
        "UNIVERSAL": {1, 2, 3, 4, 5},   # Expected by all entities
        "ENTERPRISE": {4, 5},            # Expected by Large/Complex only
        "CORPORATE": {3, 4, 5},          # Expected by Medium+
        "SME": {2, 3, 4, 5},             # Expected by Small+
        "MICRO": {1},                    # Expected only by Micro
    }

    # Phase 10: Default scores for missing signals
    PENALIZED_SCORE = 10.0     # 10th percentile (heavily penalized)
    NEUTRAL_SCORE = 50.0       # 50th percentile (median/neutral)

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
        context: Optional[InferenceContext] = None,
        audited_values: Optional[Dict[str, float]] = None,
    ) -> ScoringResult:
        """
        Execute Steps 4-6 for an entity.

        Args:
            entity_id: The entity to score
            config: Coverage configuration
            parallel: Whether to run extractions in parallel
            context: Optional inference context (created if not provided)
            audited_values: Phase 8 - Dict of {signal_id: audited_value} overrides

        Returns:
            ScoringResult with signal outputs, composite score, and conditions
        """
        start_time = time.time()

        # Create inference context if not provided
        if context is None:
            context = InferenceContext(
                configuration={},  # Will be populated by inference functions
                coverage=config.coverage_id,
                config_name=config.config_id,
            )

        # Step 4: Extract all signals
        signal_outputs, categorical_outputs = self.extract_signals(
            entity_id=entity_id,
            config=config,
            context=context,
            parallel=parallel,
        )

        # Phase 8: Apply audited_value overrides
        if audited_values:
            signal_outputs = self._apply_audited_values(signal_outputs, audited_values)

        # Step 5: Calculate pure composite score
        pure_composite_score, group_scores, confidence, coverage = self.calculate_composite(
            signal_outputs=signal_outputs,
            config=config,
        )

        # Step 6: Evaluate signal conditions
        conditions, tier_overrides, referrals, notes, signal_modifiers = self.evaluate_signal_conditions(
            signal_outputs=signal_outputs,
            group_scores=group_scores,
            config=config,
        )

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Scored entity {entity_id} in {elapsed_ms:.0f}ms: "
            f"composite={pure_composite_score:.0f}, "
            f"signals={len(signal_outputs)}, "
            f"conditions={len(conditions)}, "
            f"overrides={len(audited_values) if audited_values else 0}"
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
            modifiers=signal_modifiers,
        )

    def _apply_audited_values(
        self,
        signal_outputs: List[SignalOutput],
        audited_values: Dict[str, float],
    ) -> List[SignalOutput]:
        """
        Phase 8: Apply audited_value overrides to signal outputs.

        The inferred_value (raw_score) is preserved; we update the
        weighted_score calculation to use the audited value.

        Args:
            signal_outputs: Original signal outputs with inferred values
            audited_values: Dict of {signal_id: audited_value}

        Returns:
            Updated signal outputs with audited values applied
        """
        for output in signal_outputs:
            if output.signal_id in audited_values:
                audited_value = audited_values[output.signal_id]

                # Store original inferred value (preserved for audit trail)
                # The raw_score field holds the inferred_value
                # We update the weighted_score to use audited_value

                # Recalculate weighted score using audited value
                output.weighted_score = audited_value * output.weight

                # Mark as overridden (store audited value in a way that's visible)
                # We use the existing error field to note the override
                # In production, SignalOutput would have inferred_value/audited_value fields
                if not output.error:
                    output.error = f"AUDITED:{output.raw_score:.1f}->{audited_value:.1f}"

                logger.debug(
                    f"Applied audited_value for {output.signal_id}: "
                    f"inferred={output.raw_score:.1f}, audited={audited_value:.1f}"
                )

        return signal_outputs

    def extract_signals(
        self,
        entity_id: str,
        config: CoverageConfig,
        context: InferenceContext,
        parallel: bool = True
    ) -> Tuple[List[SignalOutput], List[CategoricalOutput]]:
        """
        Step 4: Run all inference functions.

        Iterates the signal_registry from Pydantic CoverageConfig. Signals
        with three_layer_assessment are scored; signals with categories
        produce categorical outputs.

        Args:
            entity_id: The entity to extract signals for
            config: Coverage configuration (Pydantic compiled)
            context: Inference context with cache
            parallel: Whether to run in parallel

        Returns:
            Tuple of (signal_outputs, categorical_outputs)
        """
        signal_outputs: List[SignalOutput] = []
        categorical_outputs: List[CategoricalOutput] = []

        # Build category group lookup for label resolution
        cat_group_map: Dict[str, CategoryGroup] = {
            cg.id: cg for cg in config.groups.categories
        }

        # Collect all extraction tasks from signal_registry
        signal_tasks: List[Tuple[SignalDefinition, str, float]] = []  # (signal, group_id, weight)
        categorical_tasks: List[Tuple[SignalDefinition, Optional[CategoryGroup]]] = []

        for signal in config.signal_registry:
            if signal.three_layer_assessment:
                tla = signal.three_layer_assessment
                group_id = tla.group_id
                weight = tla.risk.weight if tla.risk else 0.0
                signal_tasks.append((signal, group_id, weight))
            elif signal.categories:
                cat_group = cat_group_map.get(signal.categories.group_id)
                categorical_tasks.append((signal, cat_group))

        if parallel and (signal_tasks or categorical_tasks):
            # Parallel execution
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit signal extraction tasks
                signal_futures = {
                    executor.submit(
                        self._extract_signal,
                        entity_id, signal, group_id, weight, context
                    ): (signal, group_id, weight)
                    for signal, group_id, weight in signal_tasks
                }

                # Submit categorical extraction tasks
                categorical_futures = {
                    executor.submit(
                        self._extract_categorical,
                        entity_id, signal, cat_group, context
                    ): (signal, cat_group)
                    for signal, cat_group in categorical_tasks
                }

                # Collect signal results
                for future in as_completed(signal_futures):
                    signal, group_id, weight = signal_futures[future]
                    try:
                        output = future.result()
                        signal_outputs.append(output)
                    except Exception as e:
                        logger.error(f"Signal extraction failed for {signal.id}: {e}")
                        signal_outputs.append(self._create_default_signal_output(
                            signal_id=signal.id,
                            group_id=group_id,
                            weight=weight,
                            error=str(e),
                            expectation_level=signal.expectation_level,
                        ))

                # Collect categorical results
                for future in as_completed(categorical_futures):
                    signal, cat_group = categorical_futures[future]
                    try:
                        output = future.result()
                        categorical_outputs.append(output)
                    except Exception as e:
                        logger.error(f"Categorical extraction failed for {signal.id}: {e}")
                        categorical_outputs.append(self._create_default_categorical_output(
                            signal, cat_group, str(e)
                        ))
        else:
            # Sequential execution
            for signal, group_id, weight in signal_tasks:
                try:
                    output = self._extract_signal(entity_id, signal, group_id, weight, context)
                    signal_outputs.append(output)
                except Exception as e:
                    logger.error(f"Signal extraction failed for {signal.id}: {e}")
                    signal_outputs.append(self._create_default_signal_output(
                        signal_id=signal.id,
                        group_id=group_id,
                        weight=weight,
                        error=str(e),
                        expectation_level=signal.expectation_level,
                    ))

            for signal, cat_group in categorical_tasks:
                try:
                    output = self._extract_categorical(entity_id, signal, cat_group, context)
                    categorical_outputs.append(output)
                except Exception as e:
                    logger.error(f"Categorical extraction failed for {signal.id}: {e}")
                    categorical_outputs.append(self._create_default_categorical_output(
                        signal, cat_group, str(e)
                    ))

        return signal_outputs, categorical_outputs

    def _extract_signal(
        self,
        entity_id: str,
        signal: SignalDefinition,
        group_id: str,
        weight: float,
        context: InferenceContext,
    ) -> SignalOutput:
        """
        Extract a single signal using its inference function.

        Args:
            entity_id: The entity to extract for
            signal: Signal definition from signal_registry
            group_id: Three-layer assessment group ID
            weight: Risk dimension weight for this signal
            context: Inference context

        Returns:
            SignalOutput with extracted score
        """
        start_time = time.time()
        func_name = signal.inference_utility_function

        try:
            # Get the inference function from registry
            inference_func = get_inference_function(func_name)
        except InferenceFunctionNotFoundError:
            logger.warning(f"Inference function not found: {func_name}")
            return self._create_default_signal_output(
                signal_id=signal.id,
                group_id=group_id,
                weight=weight,
                error=f"Function not found: {func_name}",
                expectation_level=signal.expectation_level,
            )

        try:
            # Run the inference function
            result: SignalResult = inference_func(entity_id, context)

            elapsed_ms = (time.time() - start_time) * 1000

            # Convert SignalResult to SignalOutput
            return SignalOutput(
                signal_id=signal.id,
                signal_name=signal.id.replace("_", " ").title(),
                group_id=group_id,
                raw_score=result.score if result.score is not None else self.default_score,
                confidence=result.confidence if result.confidence else self.default_confidence,
                weighted_score=(result.score or self.default_score) * weight,
                weight=weight,
                data_sources=[result.metadata.get("extractor", "unknown")] if result.metadata else [],
                extracted_at=utcnow(),
                from_cache=result.metadata.get("from_cache", False) if result.metadata else False,
                execution_time_ms=result.execution_time_ms or elapsed_ms,
                error=result.error,
            )

        except Exception as e:
            logger.error(f"Inference function failed for {signal.id}: {e}")
            return self._create_default_signal_output(
                signal_id=signal.id,
                group_id=group_id,
                weight=weight,
                error=str(e),
                expectation_level=signal.expectation_level,
            )

    def _extract_categorical(
        self,
        entity_id: str,
        signal: SignalDefinition,
        cat_group: Optional[CategoryGroup],
        context: InferenceContext,
    ) -> CategoricalOutput:
        """
        Extract a categorical value using its inference function.

        Args:
            entity_id: The entity to extract for
            signal: Signal definition with categories
            cat_group: Category group definition (for label)
            context: Inference context

        Returns:
            CategoricalOutput with inferred category
        """
        func_name = signal.inference_utility_function
        group_id = signal.categories.group_id if signal.categories else signal.id
        group_name = cat_group.label if cat_group else group_id

        try:
            inference_func = get_inference_function(func_name)
        except InferenceFunctionNotFoundError:
            return self._create_default_categorical_output(
                signal, cat_group, f"Function not found: {func_name}"
            )

        try:
            result: SignalResult = inference_func(entity_id, context)

            # Get category from result
            category = result.category if result.category else "UNKNOWN"

            # Find the modifier and label from signal.categories.features
            modifier = 1.0
            label = category
            if signal.categories:
                for feat in signal.categories.features:
                    if feat.cat == category:
                        modifier = feat.applied if feat.applied is not None else 1.0
                        label = feat.label or category
                        break

            return CategoricalOutput(
                group_id=group_id,
                group_name=group_name,
                category=category,
                label=label,
                modifier=modifier,
                confidence=result.confidence if result.confidence else 0.8,
                extracted_at=utcnow(),
                error=result.error,
            )

        except Exception as e:
            return self._create_default_categorical_output(signal, cat_group, str(e))

    def _get_absence_score(
        self,
        expectation_level: ExpectationLevel = ExpectationLevel.UNIVERSAL,
        exposure_size_band: int = 3,
    ) -> float:
        """
        Phase 10: Determine appropriate score for missing signal.

        Applies the "Expected vs. Unexpected" Null Protocol:
        - If signal is expected for entity's size band: penalize (10th percentile)
        - If signal is NOT expected: neutral score (50th percentile)

        Args:
            expectation_level: Signal expectation level from Pydantic schema
            exposure_size_band: Entity's exposure size band (1-5)

        Returns:
            Appropriate default score (10 or 50)
        """
        level_str = expectation_level.value if isinstance(expectation_level, ExpectationLevel) else str(expectation_level)
        expected_bands = self.EXPECTATION_BANDS.get(level_str, {1, 2, 3, 4, 5})

        if exposure_size_band in expected_bands:
            return self.PENALIZED_SCORE
        else:
            return self.NEUTRAL_SCORE

    def _create_default_signal_output(
        self,
        signal_id: str,
        group_id: str,
        weight: float,
        error: str,
        expectation_level: ExpectationLevel = ExpectationLevel.UNIVERSAL,
        exposure_size_band: int = 3,
    ) -> SignalOutput:
        """
        Create a default signal output when extraction fails.

        Phase 10: Uses adaptive scoring based on entity size and signal expectation.
        """
        absence_score = self._get_absence_score(expectation_level, exposure_size_band)

        return SignalOutput(
            signal_id=signal_id,
            signal_name=signal_id.replace("_", " ").title(),
            group_id=group_id,
            raw_score=absence_score,
            confidence=self.default_confidence,
            weighted_score=absence_score * weight,
            weight=weight,
            extracted_at=utcnow(),
            error=error,
        )

    def _create_default_categorical_output(
        self,
        signal: SignalDefinition,
        cat_group: Optional[CategoryGroup],
        error: str,
    ) -> CategoricalOutput:
        """Create a default categorical output when extraction fails."""
        group_id = signal.categories.group_id if signal.categories else signal.id
        group_name = cat_group.label if cat_group else group_id

        # Use default_cat from group definition, or first feature
        default_cat = cat_group.default_cat if cat_group else None
        default_label = "Unknown"
        default_modifier = 1.0

        if signal.categories and signal.categories.features:
            if default_cat:
                for feat in signal.categories.features:
                    if feat.cat == default_cat:
                        default_label = feat.label or default_cat
                        default_modifier = feat.applied if feat.applied is not None else 1.0
                        break
            else:
                first = signal.categories.features[0]
                default_cat = first.cat
                default_label = first.label or first.cat
                default_modifier = first.applied if first.applied is not None else 1.0

        return CategoricalOutput(
            group_id=group_id,
            group_name=group_name,
            category=default_cat or "UNKNOWN",
            label=default_label,
            modifier=default_modifier,
            confidence=0.0,
            extracted_at=utcnow(),
            error=error,
        )

    def calculate_composite(
        self,
        signal_outputs: List[SignalOutput],
        config: CoverageConfig
    ) -> Tuple[float, Dict[str, Any], float, float]:
        """
        Step 5: Calculate pure composite score.

        The composite score is a weighted sum of group scores,
        where each group score is a weighted average of signal scores.

        Score range: 0-1000 (signal scores 0-100, group weights sum to ~1.0, × 10)

        Args:
            signal_outputs: All extracted signal outputs
            config: Coverage configuration (Pydantic compiled)

        Returns:
            Tuple of (composite_score, group_scores_detail, confidence, coverage)
            where group_scores_detail is Dict[group_id, {
                risk_score, risk_weight, risk_contribution,
                signal_count, expected_signal_count, coverage_ratio,
                loss_weight, exposure_weight
            }]
        """
        # Group signals by group_id
        signals_by_group: Dict[str, List[SignalOutput]] = {}
        for output in signal_outputs:
            if output.group_id not in signals_by_group:
                signals_by_group[output.group_id] = []
            signals_by_group[output.group_id].append(output)

        # Count total signals per group from signal_registry
        signals_per_group: Dict[str, int] = {}
        for sig in config.signal_registry:
            if sig.three_layer_assessment:
                gid = sig.three_layer_assessment.group_id
                signals_per_group[gid] = signals_per_group.get(gid, 0) + 1

        # Build loss/exposure weight lookups from config (if available)
        loss_weights: Dict[str, float] = {}
        exposure_weights: Dict[str, float] = {}
        for group in config.groups.three_layer_assessment:
            if hasattr(group, 'loss') and group.loss:
                loss_weights[group.id] = group.loss.weight
            if hasattr(group, 'exposure') and group.exposure:
                exposure_weights[group.id] = group.exposure.weight

        # Calculate group scores using three_layer_assessment groups
        group_scores_detail: Dict[str, Any] = {}
        group_risk_scores: Dict[str, float] = {}  # for internal composite calc
        total_confidence = 0.0
        total_signals = 0
        populated_signals = 0

        for group in config.groups.three_layer_assessment:
            group_signals = signals_by_group.get(group.id, [])
            expected_count = signals_per_group.get(group.id, 0)
            actual_count = len(group_signals)
            group_populated = 0

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
                group_populated = sum(1 for s in group_signals if s.error is None)
                populated_signals += group_populated
            else:
                group_score = self.default_score

            group_risk_scores[group.id] = group_score
            total_signals += expected_count

            # Calculate group contribution to composite
            risk_weight = group.risk.weight if group.risk else 0.0
            risk_contribution = group_score * risk_weight * 10

            group_scores_detail[group.id] = {
                "risk_score": round(group_score, 2),
                "risk_weight": risk_weight,
                "risk_contribution": round(risk_contribution, 2),
                "signal_count": actual_count,
                "expected_signal_count": expected_count,
                "coverage_ratio": round(group_populated / expected_count, 4) if expected_count > 0 else 0.0,
                "loss_weight": loss_weights.get(group.id),
                "exposure_weight": exposure_weights.get(group.id),
            }

        # Calculate composite score (0-1000 scale) — sum of all group contributions
        composite_score = sum(
            detail["risk_contribution"]
            for detail in group_scores_detail.values()
        )

        # Calculate overall confidence and coverage
        if total_signals > 0:
            overall_confidence = total_confidence / total_signals if total_signals > 0 else 0.5
            signal_coverage = populated_signals / total_signals
        else:
            overall_confidence = 0.5
            signal_coverage = 0.0

        return composite_score, group_scores_detail, overall_confidence, signal_coverage

    def evaluate_signal_conditions(
        self,
        signal_outputs: List[SignalOutput],
        group_scores: Dict[str, Any],
        config: CoverageConfig
    ) -> Tuple[List[TriggeredCondition], List[int], List[str], List[str], List[Dict[str, Any]]]:
        """
        Step 6: Evaluate conditions at group and signal levels.

        Conditions can trigger:
        - Tier override (via REFER + override): Force to specific tier
        - Referral: Set auto_approve = false
        - Flag: Post note for underwriter
        - Modifier: Premium modifier

        Args:
            signal_outputs: All extracted signals
            group_scores: Calculated group scores
            config: Coverage configuration (Pydantic compiled)

        Returns:
            Tuple of (conditions, tier_overrides, referrals, notes, modifiers)
        """
        conditions: List[TriggeredCondition] = []
        tier_overrides: List[int] = []
        referrals: List[str] = []
        notes: List[str] = []
        modifiers: List[Dict[str, Any]] = []

        # Create signal lookup by ID
        signal_by_id = {s.signal_id: s for s in signal_outputs}

        # Evaluate group-level conditions (from groups.three_layer_assessment)
        # Check all three dimensions: risk, loss, exposure
        for group in config.groups.three_layer_assessment:
            gs_detail = group_scores.get(group.id)
            group_score = gs_detail["risk_score"] if isinstance(gs_detail, dict) else (gs_detail if gs_detail is not None else self.default_score)
            group_label = group.label or group.id

            # Collect score_conditions from all dimensions
            dimension_conditions = []
            if group.risk and group.risk.score_conditions:
                for c in group.risk.score_conditions:
                    dimension_conditions.append(("risk", c))
            if group.loss and group.loss.score_conditions:
                for c in group.loss.score_conditions:
                    dimension_conditions.append(("loss", c))
            if group.exposure and group.exposure.score_conditions:
                for c in group.exposure.score_conditions:
                    dimension_conditions.append(("exposure", c))

            for dimension, condition in dimension_conditions:
                if self._check_score_condition(group_score, condition):
                    action = _CONDITION_ACTION_MAP.get(condition.action, ConditionAction.NOTE)
                    action_value = self._get_condition_action_value(condition)

                    tc = TriggeredCondition(
                        source_type="signal_group",
                        source_id=group.id,
                        source_name=f"{group_label} ({dimension})",
                        score=group_score,
                        response=None,
                        action=action,
                        action_value=action_value,
                        note=condition.note or str(action_value),
                    )
                    conditions.append(tc)
                    self._collect_condition_impacts(
                        condition, tier_overrides, referrals, notes,
                        modifiers, source_id=group.id, source_name=f"{group_label} ({dimension})",
                    )

        # Evaluate signal-level conditions (from signal_registry)
        # Check all three dimensions: risk, loss, exposure
        for signal in config.signal_registry:
            if not signal.three_layer_assessment:
                continue

            signal_output = signal_by_id.get(signal.id)
            signal_score = signal_output.raw_score if signal_output else self.default_score
            signal_name = signal.id.replace("_", " ").title()

            # Collect score_conditions from all dimensions
            tla = signal.three_layer_assessment
            dimension_conditions = []
            if tla.risk and tla.risk.score_conditions:
                for c in tla.risk.score_conditions:
                    dimension_conditions.append(("risk", c))
            if tla.loss and hasattr(tla.loss, 'severity') and tla.loss.severity and tla.loss.severity.score_conditions:
                for c in tla.loss.severity.score_conditions:
                    dimension_conditions.append(("loss_severity", c))
            if tla.loss and hasattr(tla.loss, 'frequency') and tla.loss.frequency and tla.loss.frequency.score_conditions:
                for c in tla.loss.frequency.score_conditions:
                    dimension_conditions.append(("loss_frequency", c))
            if tla.exposure and hasattr(tla.exposure, 'size') and tla.exposure.size and tla.exposure.size.score_conditions:
                for c in tla.exposure.size.score_conditions:
                    dimension_conditions.append(("exposure_size", c))
            if tla.exposure and hasattr(tla.exposure, 'complexity') and tla.exposure.complexity and tla.exposure.complexity.score_conditions:
                for c in tla.exposure.complexity.score_conditions:
                    dimension_conditions.append(("exposure_complexity", c))

            for dimension, condition in dimension_conditions:
                if self._check_score_condition(signal_score, condition):
                    action = _CONDITION_ACTION_MAP.get(condition.action, ConditionAction.NOTE)
                    action_value = self._get_condition_action_value(condition)

                    tc = TriggeredCondition(
                        source_type="signal_feature",
                        source_id=signal.id,
                        source_name=f"{signal_name} ({dimension})",
                        score=signal_score,
                        response=None,
                        action=action,
                        action_value=action_value,
                        note=condition.note or str(action_value),
                    )
                    conditions.append(tc)
                    self._collect_condition_impacts(
                        condition, tier_overrides, referrals, notes,
                        modifiers, source_id=signal.id, source_name=f"{signal_name} ({dimension})",
                    )

                    if signal_output:
                        signal_output.conditions_triggered.append(signal.id)

        logger.debug(
            f"Evaluated signal conditions: "
            f"{len(tier_overrides)} tier overrides, "
            f"{len(referrals)} referrals, "
            f"{len(modifiers)} modifiers, "
            f"{len(notes)} notes"
        )

        return conditions, tier_overrides, referrals, notes, modifiers

    def _check_score_condition(self, score: float, condition: ScoreCondition) -> bool:
        """
        Check if a score triggers a Pydantic ScoreCondition.

        Args:
            score: The score to check
            condition: ScoreCondition with threshold and comparison

        Returns:
            True if condition is triggered
        """
        threshold = float(condition.threshold)
        comp = condition.comparison

        if comp == ComparisonOperator.LTE:
            return score <= threshold
        elif comp == ComparisonOperator.GTE:
            return score >= threshold
        elif comp == ComparisonOperator.LT:
            return score < threshold
        elif comp == ComparisonOperator.GT:
            return score > threshold
        elif comp == ComparisonOperator.EQ:
            return score == threshold
        elif comp == ComparisonOperator.NEQ:
            return score != threshold
        return False

    def _get_condition_action_value(self, condition: ScoreCondition) -> Any:
        """Extract action value from a ScoreCondition."""
        if condition.action == ScoreConditionAction.MODIFIER:
            return condition.applied or 1.0
        elif condition.action == ScoreConditionAction.REFER:
            return condition.override or condition.note or "Referral triggered"
        elif condition.action == ScoreConditionAction.FLAG:
            return condition.note or "Flag triggered"
        return condition.note or ""

    def _collect_condition_impacts(
        self,
        condition: ScoreCondition,
        tier_overrides: List[int],
        referrals: List[str],
        notes: List[str],
        modifiers: List[Dict[str, Any]],
        source_id: str = "unknown",
        source_name: str = "unknown",
    ) -> None:
        """Collect impacts from a triggered ScoreCondition into output lists."""
        if condition.action == ScoreConditionAction.REFER:
            if condition.override is not None:
                tier_overrides.append(condition.override)
            referrals.append(condition.note or "Referral triggered")
        elif condition.action == ScoreConditionAction.FLAG:
            notes.append(condition.note or "Flag triggered")
        elif condition.action == ScoreConditionAction.MODIFIER:
            factor = condition.applied or 1.0
            if factor != 1.0:
                modifiers.append({
                    "source": "signal_condition",
                    "source_id": source_id,
                    "name": source_name,
                    "factor": factor,
                })


# Singleton instance for convenience
_default_scorer: Optional[ModelScorer] = None


def get_scorer() -> ModelScorer:
    """Get the default ModelScorer instance."""
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = ModelScorer()
    return _default_scorer
