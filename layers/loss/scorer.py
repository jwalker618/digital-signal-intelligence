"""
Loss Correlation Scorer (Phase 16)

Calculates loss propensity scores from signal outputs.
Operates in parallel with risk scoring, using the same signal extraction
results but applying loss-specific weighting and correlation logic.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from .types import (
    LossCorrelationConfig,
    LossPropensityResult,
    LossSignalResult,
    LossPropensityBand,
    SeverityPropensityBand,
    TrendDirection,
    CorrelationType,
    CorrelationDirection,
)
from layers.risk.types import SignalOutput


logger = logging.getLogger("dsi.loss_scorer")


class LossCorrelationScorer:
    """
    Calculates loss propensity scores from signal outputs.

    Operates in parallel with risk scoring, using the same
    signal extraction results but applying loss-specific
    weighting and correlation logic.

    Key features:
    - Same signals, different weights (loss-correlated)
    - Direction-aware scoring (negative correlations inverted)
    - Frequency and severity separation
    - Cohort assignment based on signal patterns
    - Pricing modifier calculation with caps/floors
    - Trend analysis for continuous monitoring
    """

    def __init__(self, config: LossCorrelationConfig):
        """
        Initialize the scorer with configuration.

        Args:
            config: Loss correlation configuration from YAML
        """
        self.config = config
        self._build_signal_lookup()

    def _build_signal_lookup(self) -> None:
        """Build lookup table for signal configuration."""
        self.signal_config: Dict[str, Dict[str, Any]] = {}
        for group in self.config.correlation_groups:
            for feature in group.features:
                self.signal_config[feature.id] = {
                    "group": group.name,
                    "weight": feature.weight,
                    "group_weight": group.weight,
                    "correlation_type": feature.correlation_type,
                    "correlation_direction": feature.correlation_direction,
                    "normalizer": feature.normalizer,
                    "thresholds": feature.thresholds,
                    "lag_months": feature.lag_months,
                }

    def calculate_propensity(
        self,
        signal_outputs: List[SignalOutput],
        previous_result: Optional[LossPropensityResult] = None,
    ) -> LossPropensityResult:
        """
        Calculate loss propensity from signal outputs.

        Args:
            signal_outputs: Signal extraction results from main pipeline
            previous_result: Previous propensity result for trend analysis

        Returns:
            Complete loss propensity result
        """
        # Convert to loss signal results
        loss_signals = self._extract_loss_signals(signal_outputs)

        # Calculate group scores
        frequency_group_scores, severity_group_scores, group_confidences = (
            self._calculate_group_scores(loss_signals)
        )

        # Build group weights lookup from config
        group_weights: Dict[str, float] = {
            g.name: g.weight for g in self.config.correlation_groups
        }

        # Calculate composite scores
        loss_propensity_score = self._calculate_composite(
            frequency_group_scores,
            self.config.correlation_groups,
        )
        severity_propensity_score = self._calculate_composite(
            severity_group_scores,
            self.config.correlation_groups,
        )

        # Calculate confidence
        loss_confidence = self._calculate_confidence(group_confidences)

        # Map to bands
        loss_propensity_band = self._map_to_propensity_band(loss_propensity_score)
        severity_propensity_band = self._map_to_severity_band(severity_propensity_score)

        # Assign cohort
        cohort_id, cohort_name, cohort_confidence = self._assign_cohort(loss_signals)

        # Calculate pricing impact
        frequency_multiplier = self._get_frequency_multiplier(loss_propensity_band)
        severity_multiplier = self._get_severity_multiplier(severity_propensity_band)
        combined_modifier = self._calculate_combined_modifier(
            frequency_multiplier,
            severity_multiplier,
        )

        # Calculate trend
        trend_direction, score_velocity = self._calculate_trend(
            loss_propensity_score,
            previous_result,
        )

        # Evaluate referral triggers
        referral_triggered, referral_reasons, flags = self._evaluate_rules(
            loss_propensity_score,
            loss_propensity_band,
            loss_confidence,
            previous_result,
        )

        logger.info(
            f"Loss propensity calculated: score={loss_propensity_score:.1f}, "
            f"band={loss_propensity_band.value}, modifier={combined_modifier:.3f}"
        )

        return LossPropensityResult(
            loss_propensity_score=loss_propensity_score,
            severity_propensity_score=severity_propensity_score,
            loss_propensity_band=loss_propensity_band,
            severity_propensity_band=severity_propensity_band,
            loss_confidence=loss_confidence,
            cohort_id=cohort_id,
            cohort_name=cohort_name,
            cohort_confidence=cohort_confidence,
            group_scores={**frequency_group_scores, **severity_group_scores},
            group_confidences=group_confidences,
            group_weights=group_weights,
            frequency_group_scores=frequency_group_scores,
            severity_group_scores=severity_group_scores,
            frequency_multiplier=frequency_multiplier,
            severity_multiplier=severity_multiplier,
            combined_loss_modifier=combined_modifier,
            trend_direction=trend_direction,
            combined_score_velocity=score_velocity,
            days_since_last_assessment=self._days_since_last(previous_result),
            previous_combined_score=previous_result.loss_propensity_score if previous_result else None,
            referral_triggered=referral_triggered,
            referral_reasons=referral_reasons,
            flags=flags,
            signal_results=loss_signals,
            calculated_at=datetime.utcnow(),
            config_version=self.config.version,
            correlation_matrix_version=None,
        )

    def _extract_loss_signals(
        self,
        signal_outputs: List[SignalOutput],
    ) -> List[LossSignalResult]:
        """Extract loss-relevant signals from signal outputs."""
        loss_signals = []

        for output in signal_outputs:
            if output.signal_id in self.signal_config:
                config = self.signal_config[output.signal_id]

                # Apply direction adjustment
                # For negative correlations, invert the score
                normalized = output.raw_score
                if config["correlation_direction"] == CorrelationDirection.NEGATIVE:
                    normalized = 100 - normalized

                loss_signals.append(LossSignalResult(
                    signal_id=output.signal_id,
                    value=output.raw_score,
                    normalized_value=normalized,
                    confidence=output.confidence,
                    correlation_type=config["correlation_type"],
                    correlation_direction=config["correlation_direction"],
                    source_urls=output.data_sources,
                    extracted_at=output.extracted_at,
                ))

        return loss_signals

    def _calculate_group_scores(
        self,
        loss_signals: List[LossSignalResult],
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
        """Calculate frequency and severity scores for each group."""
        frequency_scores: Dict[str, float] = {}
        severity_scores: Dict[str, float] = {}
        confidences: Dict[str, float] = {}

        # Group signals by correlation group
        signals_by_group: Dict[str, List[LossSignalResult]] = {}
        for signal in loss_signals:
            group = self.signal_config[signal.signal_id]["group"]
            if group not in signals_by_group:
                signals_by_group[group] = []
            signals_by_group[group].append(signal)

        # Calculate weighted scores for each group
        for group_config in self.config.correlation_groups:
            group_name = group_config.name
            group_signals = signals_by_group.get(group_name, [])

            if not group_signals:
                continue

            freq_weighted_sum = 0.0
            freq_weight_total = 0.0
            sev_weighted_sum = 0.0
            sev_weight_total = 0.0
            conf_weighted_sum = 0.0
            conf_weight_total = 0.0

            for signal in group_signals:
                feature_config = self.signal_config[signal.signal_id]
                weight = feature_config["weight"]

                # Frequency contribution
                if signal.correlation_type in [CorrelationType.FREQUENCY, CorrelationType.BOTH]:
                    freq_weighted_sum += signal.normalized_value * weight
                    freq_weight_total += weight

                # Severity contribution
                if signal.correlation_type in [CorrelationType.SEVERITY, CorrelationType.BOTH]:
                    sev_weighted_sum += signal.normalized_value * weight
                    sev_weight_total += weight

                # Confidence tracking
                conf_weighted_sum += signal.confidence * weight
                conf_weight_total += weight

            if freq_weight_total > 0:
                frequency_scores[group_name] = freq_weighted_sum / freq_weight_total
            if sev_weight_total > 0:
                severity_scores[group_name] = sev_weighted_sum / sev_weight_total
            if conf_weight_total > 0:
                confidences[group_name] = conf_weighted_sum / conf_weight_total

        return frequency_scores, severity_scores, confidences

    def _calculate_composite(
        self,
        group_scores: Dict[str, float],
        groups: List,
    ) -> float:
        """Calculate weighted composite score."""
        weighted_sum = 0.0
        weight_total = 0.0

        for group in groups:
            if group.name in group_scores:
                weighted_sum += group_scores[group.name] * group.weight
                weight_total += group.weight

        if weight_total == 0:
            return 50.0  # Default to moderate

        return weighted_sum / weight_total

    def _map_to_propensity_band(self, score: float) -> LossPropensityBand:
        """Map score to propensity band."""
        for band in self.config.propensity_bands:
            if band.min_score <= score < band.max_score:
                return LossPropensityBand(band.name)

        # Default based on score
        if score < 20:
            return LossPropensityBand.VERY_LOW
        elif score < 40:
            return LossPropensityBand.LOW
        elif score < 60:
            return LossPropensityBand.MODERATE
        elif score < 80:
            return LossPropensityBand.ELEVATED
        else:
            return LossPropensityBand.HIGH

    def _map_to_severity_band(self, score: float) -> SeverityPropensityBand:
        """Map score to severity band."""
        for band in self.config.severity_bands:
            if band.min_score <= score < band.max_score:
                try:
                    return SeverityPropensityBand(band.name)
                except ValueError:
                    break

        # Default based on score
        if score < 20:
            return SeverityPropensityBand.MINIMAL
        elif score < 40:
            return SeverityPropensityBand.MODERATE
        elif score < 60:
            return SeverityPropensityBand.SIGNIFICANT
        elif score < 80:
            return SeverityPropensityBand.SEVERE
        else:
            return SeverityPropensityBand.CATASTROPHIC

    def _get_frequency_multiplier(self, band: LossPropensityBand) -> float:
        """Get frequency multiplier for band."""
        for band_config in self.config.propensity_bands:
            if band_config.name == band.value:
                return band_config.expected_frequency_multiplier

        # Default multipliers by band
        defaults = {
            LossPropensityBand.VERY_LOW: 0.60,
            LossPropensityBand.LOW: 0.80,
            LossPropensityBand.MODERATE: 1.00,
            LossPropensityBand.ELEVATED: 1.25,
            LossPropensityBand.HIGH: 1.50,
        }
        return defaults.get(band, 1.0)

    def _get_severity_multiplier(self, band: SeverityPropensityBand) -> float:
        """Get severity multiplier for band."""
        for band_config in self.config.severity_bands:
            if band_config.name == band.value:
                return band_config.expected_severity_multiplier

        # Default multipliers by band
        defaults = {
            SeverityPropensityBand.MINIMAL: 0.70,
            SeverityPropensityBand.MODERATE: 0.90,
            SeverityPropensityBand.SIGNIFICANT: 1.10,
            SeverityPropensityBand.SEVERE: 1.30,
            SeverityPropensityBand.CATASTROPHIC: 1.50,
        }
        return defaults.get(band, 1.0)

    def _calculate_combined_modifier(
        self,
        frequency_mult: float,
        severity_mult: float,
    ) -> float:
        """Calculate combined loss modifier."""
        combined = (
            frequency_mult * self.config.frequency_weight +
            severity_mult * self.config.severity_weight
        )

        # Apply caps and floors
        cap = max(self.config.frequency_impact_cap, self.config.severity_impact_cap)
        floor = min(self.config.frequency_impact_floor, self.config.severity_impact_floor)

        return max(floor, min(cap, combined))

    def _assign_cohort(
        self,
        loss_signals: List[LossSignalResult],
    ) -> Tuple[str, str, float]:
        """Assign entity to cohort based on signal pattern."""
        # Check predefined cohorts first
        for cohort in self.config.cohort_definitions:
            if self._matches_cohort_criteria(loss_signals, cohort.criteria):
                return cohort.id, cohort.name, 0.9

        # Default cohort
        return "default", "Standard", 0.5

    def _matches_cohort_criteria(
        self,
        signals: List[LossSignalResult],
        criteria: Dict[str, Any],
    ) -> bool:
        """Check if signals match cohort criteria."""
        signal_values = {s.signal_id: s.normalized_value for s in signals}

        for signal_id, condition in criteria.items():
            if signal_id not in signal_values:
                return False

            value = signal_values[signal_id]

            if isinstance(condition, str):
                if condition.startswith(">="):
                    if value < float(condition[2:]):
                        return False
                elif condition.startswith("<="):
                    if value > float(condition[2:]):
                        return False
                elif condition.startswith(">"):
                    if value <= float(condition[1:]):
                        return False
                elif condition.startswith("<"):
                    if value >= float(condition[1:]):
                        return False
            elif isinstance(condition, (int, float)):
                if value != condition:
                    return False

        return True

    def _calculate_trend(
        self,
        current_score: float,
        previous: Optional[LossPropensityResult],
    ) -> Tuple[TrendDirection, float]:
        """Calculate trend direction and velocity."""
        if previous is None:
            return TrendDirection.STABLE, 0.0

        days_elapsed = (datetime.utcnow() - previous.calculated_at).days
        if days_elapsed == 0:
            return TrendDirection.STABLE, 0.0

        score_delta = current_score - previous.loss_propensity_score
        velocity = score_delta / (days_elapsed / 30)  # points per month

        # Use thresholds to determine direction
        threshold = 5.0  # Minimum change to be considered significant
        if score_delta > threshold:
            direction = TrendDirection.DETERIORATING
        elif score_delta < -threshold:
            direction = TrendDirection.IMPROVING
        else:
            direction = TrendDirection.STABLE

        return direction, velocity

    def _evaluate_rules(
        self,
        score: float,
        band: LossPropensityBand,
        confidence: float,
        previous: Optional[LossPropensityResult],
    ) -> Tuple[bool, List[str], List[str]]:
        """Evaluate auto-apply rules."""
        referral_triggered = False
        referral_reasons: List[str] = []
        flags: List[str] = []

        for rule in self.config.auto_apply_rules:
            condition = rule.get("condition", "")
            if self._evaluate_condition(condition, score, band, confidence, previous):
                action = rule.get("action", "")
                reason = rule.get("reason", "Loss propensity rule triggered")

                if action == "refer":
                    referral_triggered = True
                    referral_reasons.append(reason)
                elif action == "flag":
                    flags.append(reason)

        # Standard referral triggers
        if band == LossPropensityBand.HIGH and confidence >= 0.7:
            if not referral_triggered:
                referral_triggered = True
                referral_reasons.append("High loss propensity with high confidence")

        return referral_triggered, referral_reasons, flags

    def _calculate_confidence(self, group_confidences: Dict[str, float]) -> float:
        """Calculate overall confidence."""
        if not group_confidences:
            return 0.0

        weighted_sum = 0.0
        weight_total = 0.0

        for group in self.config.correlation_groups:
            if group.name in group_confidences:
                weighted_sum += group_confidences[group.name] * group.weight
                weight_total += group.weight

        return weighted_sum / weight_total if weight_total > 0 else 0.0

    def _days_since_last(self, previous: Optional[LossPropensityResult]) -> int:
        """Calculate days since last assessment."""
        if previous is None:
            return 0
        return (datetime.utcnow() - previous.calculated_at).days

    def _evaluate_condition(
        self,
        condition: str,
        score: float,
        band: LossPropensityBand,
        confidence: float,
        previous: Optional[LossPropensityResult],
    ) -> bool:
        """Evaluate a rule condition safely."""
        if not condition:
            return False

        # Build context for evaluation
        context = {
            "loss_propensity_score": score,
            "loss_propensity_band": band.value,
            "loss_confidence": confidence,
            "loss_propensity_score_delta": (
                score - previous.loss_propensity_score
                if previous else 0
            ),
        }

        try:
            # Simple pattern matching for common conditions
            if ">=" in condition:
                parts = condition.split(">=")
                var_name = parts[0].strip()
                threshold = float(parts[1].strip())
                return context.get(var_name, 0) >= threshold
            elif "<=" in condition:
                parts = condition.split("<=")
                var_name = parts[0].strip()
                threshold = float(parts[1].strip())
                return context.get(var_name, 0) <= threshold
            elif ">" in condition:
                parts = condition.split(">")
                var_name = parts[0].strip()
                threshold = float(parts[1].strip())
                return context.get(var_name, 0) > threshold
            elif "<" in condition:
                parts = condition.split("<")
                var_name = parts[0].strip()
                threshold = float(parts[1].strip())
                return context.get(var_name, 0) < threshold
            elif "==" in condition:
                parts = condition.split("==")
                var_name = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                return str(context.get(var_name, "")) == value

            return False
        except (ValueError, KeyError, IndexError):
            logger.warning(f"Failed to evaluate condition: {condition}")
            return False
