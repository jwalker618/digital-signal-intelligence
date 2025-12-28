"""
DSI Model Scorer

Executes signal scoring pipeline (Steps 4-6).

Step 4: Signal extraction - run all inference functions
Step 5: Pure composite score calculation
Step 6: Signal conditions evaluation
"""

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Callable

from .types import (
    CoverageConfig,
    SignalConfig,
    SignalGroupConfig,
    SignalCondition,
    SignalOutput,
    ScoringResult,
    ConditionAction,
)


class ModelScorer:
    """
    Executes signal scoring pipeline.
    
    Orchestrates extraction → aggregation → categorization → inference
    for all signals defined in configuration.
    """
    
    def __init__(
        self,
        inference_registry: dict[str, Callable] | None = None,
        max_workers: int = 8
    ):
        """
        Initialize scorer.
        
        Args:
            inference_registry: Dict mapping inference function names to callables
            max_workers: Max parallel workers for signal extraction
        """
        self.inference_registry = inference_registry or {}
        self.max_workers = max_workers
    
    def register_inference_function(self, name: str, func: Callable) -> None:
        """Register an inference function"""
        self.inference_registry[name] = func
    
    # =========================================================================
    # MAIN SCORING (Steps 4-6)
    # =========================================================================
    
    def score_entity(
        self,
        entity_id: str,
        config: CoverageConfig,
        submission_data: dict[str, Any] | None = None,
        parallel: bool = True
    ) -> ScoringResult:
        """
        Execute full scoring pipeline (Steps 4-6).
        
        Args:
            entity_id: Entity being scored
            config: Coverage configuration
            submission_data: Additional submission data for context
            parallel: Whether to run signals in parallel
        
        Returns:
            ScoringResult with all signal outputs and composite score
        """
        start_time = datetime.utcnow()
        
        result = ScoringResult(
            entity_id=entity_id,
            coverage=config.coverage,
            extraction_started_at=start_time
        )
        
        # Step 4: Extract all signals
        signal_outputs = self.extract_signals(
            entity_id=entity_id,
            config=config,
            submission_data=submission_data,
            parallel=parallel
        )
        result.signal_outputs = signal_outputs
        
        # Step 5: Calculate composite score
        composite_score, group_scores, confidence = self.calculate_composite(
            signal_outputs=signal_outputs,
            config=config
        )
        result.pure_composite_score = composite_score
        result.group_scores = group_scores
        result.aggregate_confidence = confidence
        
        # Step 6: Evaluate signal conditions
        conditions = self.evaluate_signal_conditions(
            signal_outputs=signal_outputs,
            group_scores=group_scores,
            config=config
        )
        
        result.signal_conditions_triggered = conditions['all_conditions']
        result.tier_overrides_from_signals = conditions['tier_overrides']
        result.referrals_from_signals = conditions['referrals']
        result.notes_from_signals = conditions['notes']
        
        # Complete timing
        end_time = datetime.utcnow()
        result.extraction_completed_at = end_time
        result.duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return result
    
    # =========================================================================
    # STEP 4: SIGNAL EXTRACTION
    # =========================================================================
    
    def extract_signals(
        self,
        entity_id: str,
        config: CoverageConfig,
        submission_data: dict[str, Any] | None = None,
        parallel: bool = True
    ) -> list[SignalOutput]:
        """
        Run all inference functions to extract signals.
        
        For each signal in config:
        1. Look up inference function in registry
        2. Execute function with entity_id and context
        3. Capture result as SignalOutput
        """
        submission_data = submission_data or {}
        signals_to_extract = []
        
        # Build list of signals to extract
        for group in config.signal_groups:
            for signal in group.signals:
                signals_to_extract.append({
                    'group': group,
                    'signal': signal,
                    'entity_id': entity_id,
                    'submission_data': submission_data
                })
        
        if parallel and len(signals_to_extract) > 1:
            return self._extract_parallel(signals_to_extract)
        else:
            return self._extract_sequential(signals_to_extract)
    
    def _extract_sequential(self, signals: list[dict]) -> list[SignalOutput]:
        """Extract signals one at a time"""
        outputs = []
        for item in signals:
            output = self._extract_single_signal(
                group=item['group'],
                signal=item['signal'],
                entity_id=item['entity_id'],
                submission_data=item['submission_data']
            )
            outputs.append(output)
        return outputs
    
    def _extract_parallel(self, signals: list[dict]) -> list[SignalOutput]:
        """Extract signals in parallel using ThreadPoolExecutor"""
        outputs = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._extract_single_signal,
                    group=item['group'],
                    signal=item['signal'],
                    entity_id=item['entity_id'],
                    submission_data=item['submission_data']
                ): item
                for item in signals
            }
            
            for future in as_completed(futures):
                try:
                    output = future.result()
                    outputs.append(output)
                except Exception as e:
                    # Log error and create failed signal output
                    item = futures[future]
                    outputs.append(self._create_failed_output(
                        group=item['group'],
                        signal=item['signal'],
                        error=str(e)
                    ))
        
        return outputs
    
    def _extract_single_signal(
        self,
        group: SignalGroupConfig,
        signal: SignalConfig,
        entity_id: str,
        submission_data: dict
    ) -> SignalOutput:
        """Extract a single signal"""
        func_name = signal.inference_function
        
        if func_name not in self.inference_registry:
            return self._create_failed_output(
                group=group,
                signal=signal,
                error=f"Inference function not found: {func_name}"
            )
        
        try:
            # Call inference function
            func = self.inference_registry[func_name]
            result = func(entity_id=entity_id, context=submission_data)
            
            # Extract score and confidence from result
            if isinstance(result, dict):
                raw_score = float(result.get('score', 0))
                confidence = float(result.get('confidence', 1.0))
                data_sources = result.get('data_sources', [])
            elif isinstance(result, (int, float)):
                raw_score = float(result)
                confidence = 1.0
                data_sources = []
            else:
                raw_score = 0.0
                confidence = 0.0
                data_sources = []
            
            # Clamp score to 0-100
            raw_score = max(0.0, min(100.0, raw_score))
            confidence = max(0.0, min(1.0, confidence))
            
            # Calculate weighted score
            # weighted_score = raw_score * signal_weight * group_weight * 10
            # This contributes directly to 0-1000 composite
            weighted_score = raw_score * signal.weight * group.weight * 10
            
            return SignalOutput(
                signal_id=str(uuid.uuid4()),
                signal_name=signal.name,
                group_name=group.name,
                raw_score=raw_score,
                confidence=confidence,
                signal_weight=signal.weight,
                group_weight=group.weight,
                weighted_score=weighted_score,
                data_sources=data_sources,
                extracted_at=datetime.utcnow()
            )
            
        except Exception as e:
            return self._create_failed_output(
                group=group,
                signal=signal,
                error=str(e)
            )
    
    def _create_failed_output(
        self,
        group: SignalGroupConfig,
        signal: SignalConfig,
        error: str
    ) -> SignalOutput:
        """Create a signal output for a failed extraction"""
        return SignalOutput(
            signal_id=str(uuid.uuid4()),
            signal_name=signal.name,
            group_name=group.name,
            raw_score=0.0,
            confidence=0.0,  # Zero confidence indicates failure
            signal_weight=signal.weight,
            group_weight=group.weight,
            weighted_score=0.0,
            data_sources=[],
            extracted_at=datetime.utcnow(),
            conditions_triggered=[{
                'type': 'extraction_error',
                'error': error
            }]
        )
    
    # =========================================================================
    # STEP 5: COMPOSITE SCORE CALCULATION
    # =========================================================================
    
    def calculate_composite(
        self,
        signal_outputs: list[SignalOutput],
        config: CoverageConfig
    ) -> tuple[float, dict[str, float], float]:
        """
        Calculate weighted composite score.
        
        Composite score = sum of all weighted signal scores (0-1000)
        
        Returns:
            Tuple of (composite_score, group_scores, aggregate_confidence)
        """
        # Group signals by their group
        signals_by_group: dict[str, list[SignalOutput]] = {}
        for output in signal_outputs:
            if output.group_name not in signals_by_group:
                signals_by_group[output.group_name] = []
            signals_by_group[output.group_name].append(output)
        
        # Calculate group scores
        group_scores: dict[str, float] = {}
        group_confidences: dict[str, float] = {}
        
        for group in config.signal_groups:
            group_outputs = signals_by_group.get(group.name, [])
            
            if not group_outputs:
                group_scores[group.name] = 0.0
                group_confidences[group.name] = 0.0
                continue
            
            # Sum weighted scores within group
            # Each signal's weighted_score already includes signal_weight * group_weight
            group_score = sum(o.weighted_score for o in group_outputs)
            group_scores[group.name] = group_score
            
            # Average confidence within group, weighted by signal weight
            total_weight = sum(o.signal_weight for o in group_outputs)
            if total_weight > 0:
                group_confidences[group.name] = sum(
                    o.confidence * o.signal_weight for o in group_outputs
                ) / total_weight
            else:
                group_confidences[group.name] = 0.0
        
        # Composite score is sum of group scores
        composite_score = sum(group_scores.values())
        
        # Clamp to 0-1000
        composite_score = max(0.0, min(1000.0, composite_score))
        
        # Aggregate confidence weighted by group weights
        total_group_weight = sum(g.weight for g in config.signal_groups)
        if total_group_weight > 0:
            aggregate_confidence = sum(
                group_confidences.get(g.name, 0) * g.weight
                for g in config.signal_groups
            ) / total_group_weight
        else:
            aggregate_confidence = 0.0
        
        return (composite_score, group_scores, aggregate_confidence)
    
    # =========================================================================
    # STEP 6: SIGNAL CONDITIONS EVALUATION
    # =========================================================================
    
    def evaluate_signal_conditions(
        self,
        signal_outputs: list[SignalOutput],
        group_scores: dict[str, float],
        config: CoverageConfig
    ) -> dict[str, list]:
        """
        Evaluate conditions defined at signal_group and signal_feature levels.
        
        Conditions can trigger:
        - (a) Tier override
        - (b) Referral
        - (c) Note
        
        Note: Signal conditions CANNOT trigger modifiers.
        
        Returns:
            Dict with keys: all_conditions, tier_overrides, referrals, notes
        """
        all_conditions = []
        tier_overrides = []
        referrals = []
        notes = []
        
        # Build lookup for signal outputs by name
        outputs_by_name = {o.signal_name: o for o in signal_outputs}
        
        # Evaluate group-level conditions
        for group in config.signal_groups:
            group_score = group_scores.get(group.name, 0)
            
            for condition in group.conditions:
                if self._evaluate_condition(condition, group_score):
                    triggered = {
                        'level': 'group',
                        'group': group.name,
                        'condition_type': condition.condition_type,
                        'condition_value': condition.condition_value,
                        'actual_value': group_score,
                        'action': condition.action.value,
                        'action_value': condition.action_value
                    }
                    all_conditions.append(triggered)
                    
                    self._apply_condition_action(
                        condition=condition,
                        tier_overrides=tier_overrides,
                        referrals=referrals,
                        notes=notes,
                        context=f"Group '{group.name}'"
                    )
        
        # Evaluate signal-level conditions
        for group in config.signal_groups:
            for signal in group.signals:
                output = outputs_by_name.get(signal.name)
                if not output:
                    continue
                
                for condition in signal.conditions:
                    if self._evaluate_condition(condition, output.raw_score):
                        triggered = {
                            'level': 'signal',
                            'group': group.name,
                            'signal': signal.name,
                            'condition_type': condition.condition_type,
                            'condition_value': condition.condition_value,
                            'actual_value': output.raw_score,
                            'action': condition.action.value,
                            'action_value': condition.action_value
                        }
                        all_conditions.append(triggered)
                        
                        # Also track on the signal output itself
                        output.conditions_triggered.append(triggered)
                        
                        self._apply_condition_action(
                            condition=condition,
                            tier_overrides=tier_overrides,
                            referrals=referrals,
                            notes=notes,
                            context=f"Signal '{signal.name}'"
                        )
        
        return {
            'all_conditions': all_conditions,
            'tier_overrides': tier_overrides,
            'referrals': referrals,
            'notes': notes
        }
    
    def _evaluate_condition(
        self,
        condition: SignalCondition,
        value: float
    ) -> bool:
        """
        Evaluate whether a condition is triggered.
        
        Supports condition types:
        - threshold_below: value < condition_value
        - threshold_above: value > condition_value
        - equals: value == condition_value
        - in_range: condition_value is [min, max], check if value in range
        """
        ctype = condition.condition_type.lower()
        cvalue = condition.condition_value
        
        if ctype == 'threshold_below':
            return value < float(cvalue)
        
        elif ctype == 'threshold_above':
            return value > float(cvalue)
        
        elif ctype == 'equals':
            if isinstance(cvalue, (int, float)):
                return abs(value - float(cvalue)) < 0.001
            return str(value) == str(cvalue)
        
        elif ctype == 'in_range':
            if isinstance(cvalue, (list, tuple)) and len(cvalue) == 2:
                return float(cvalue[0]) <= value <= float(cvalue[1])
            return False
        
        elif ctype == 'not_in_range':
            if isinstance(cvalue, (list, tuple)) and len(cvalue) == 2:
                return not (float(cvalue[0]) <= value <= float(cvalue[1]))
            return False
        
        elif ctype == 'in_list':
            if isinstance(cvalue, list):
                return value in cvalue
            return False
        
        # Unknown condition type - don't trigger
        return False
    
    def _apply_condition_action(
        self,
        condition: SignalCondition,
        tier_overrides: list[int],
        referrals: list[str],
        notes: list[str],
        context: str
    ) -> None:
        """Apply the action from a triggered condition"""
        if condition.action == ConditionAction.TIER_OVERRIDE:
            tier_overrides.append(int(condition.action_value))
        
        elif condition.action == ConditionAction.REFERRAL:
            reason = condition.action_value or f"Condition triggered by {context}"
            referrals.append(str(reason))
        
        elif condition.action == ConditionAction.NOTE:
            note = condition.action_value or f"Note from {context}"
            notes.append(str(note))
        
        # Signal conditions cannot trigger modifiers
        elif condition.action == ConditionAction.MODIFIER:
            # This should have been caught during config parsing
            pass
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_signal_breakdown(
        self,
        result: ScoringResult
    ) -> dict[str, Any]:
        """
        Get detailed breakdown of scoring for audit/debug.
        """
        groups = {}
        
        for output in result.signal_outputs:
            if output.group_name not in groups:
                groups[output.group_name] = {
                    'group_weight': output.group_weight,
                    'group_score': result.group_scores.get(output.group_name, 0),
                    'signals': []
                }
            
            groups[output.group_name]['signals'].append({
                'name': output.signal_name,
                'raw_score': output.raw_score,
                'confidence': output.confidence,
                'weight': output.signal_weight,
                'weighted_score': output.weighted_score,
                'conditions_triggered': output.conditions_triggered
            })
        
        return {
            'entity_id': result.entity_id,
            'coverage': result.coverage,
            'composite_score': result.pure_composite_score,
            'aggregate_confidence': result.aggregate_confidence,
            'groups': groups,
            'conditions_summary': {
                'tier_overrides': result.tier_overrides_from_signals,
                'referrals': result.referrals_from_signals,
                'notes': result.notes_from_signals
            },
            'duration_ms': result.duration_ms
        }
