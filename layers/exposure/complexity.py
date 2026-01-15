"""
Exposure Complexity Scorer (Phase 17)

Calculates exposure complexity score measuring how distributed,
interconnected, and structurally complex the exposure is.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    ExposureConfig,
    ExposureGroupConfig,
    ExposureFeatureConfig,
    ExposureSignalOutput,
    ExposureGroupScore,
    ComplexityResult,
    ComplexityCategory,
    ProxyTier,
)


class ComplexityScorer:
    """
    Calculate exposure complexity score.

    Complexity has four components:
    - Geographic: Number of countries/regions, dispersion
    - Structural: Number of subsidiaries, organizational depth
    - Technical: Technology heterogeneity, system diversity
    - Regulatory: Number of regulatory jurisdictions

    Higher complexity = more potential for accumulation,
    coordination challenges, and systemic risk.

    Usage:
        config = ExposureConfig.from_dict(yaml_data)
        scorer = ComplexityScorer(config)
        result = scorer.score(signal_outputs)
    """

    # Default component weights
    DEFAULT_WEIGHTS = {
        "geographic": 0.30,
        "structural": 0.25,
        "technical": 0.25,
        "regulatory": 0.20,
    }

    def __init__(self, config: ExposureConfig):
        """
        Initialize complexity scorer.

        Args:
            config: Exposure configuration from YAML
        """
        self.config = config

        # Sort complexity groups by weight
        self._sorted_groups = sorted(
            config.complexity_groups,
            key=lambda g: g.weight,
            reverse=True
        )

        # Build signal-to-config lookup
        self._signal_config: Dict[str, ExposureFeatureConfig] = {}
        for group in config.complexity_groups:
            for feature in group.features:
                self._signal_config[feature.id] = feature

        # Build category lookup sorted by min_score
        self._sorted_categories = sorted(
            config.complexity_categories,
            key=lambda c: c.min_score
        )

    def score(
        self,
        signal_outputs: List[Any],
    ) -> ComplexityResult:
        """
        Calculate complexity from signal outputs.

        Args:
            signal_outputs: Signal extraction results (SignalOutput objects)

        Returns:
            ComplexityResult with score, category, and component breakdown
        """
        # Extract complexity-relevant signals
        complexity_signals = self._extract_complexity_signals(signal_outputs)

        if not complexity_signals:
            return self._create_default_result()

        # Calculate group scores
        group_scores = self._calculate_group_scores(complexity_signals)

        # Calculate component scores
        geographic_score = self._calculate_component_score(group_scores, "geographic")
        structural_score = self._calculate_component_score(group_scores, "structural")
        technical_score = self._calculate_component_score(group_scores, "technical")
        regulatory_score = self._calculate_component_score(group_scores, "regulatory")

        # Calculate composite score and confidence
        score, confidence = self._calculate_composite(group_scores)

        # Map to complexity category
        category = self._map_to_category(score)

        # Get complexity modifier
        complexity_modifier = self._get_complexity_modifier(category)

        return ComplexityResult(
            score=round(score, 2),
            category=category,
            confidence=round(confidence, 3),
            geographic_score=round(geographic_score, 2),
            structural_score=round(structural_score, 2),
            technical_score=round(technical_score, 2),
            regulatory_score=round(regulatory_score, 2),
            group_scores={gs.group_name: gs.score for gs in group_scores},
            signals_used=[s.signal_id for s in complexity_signals if s.confidence > 0],
            complexity_modifier=complexity_modifier,
            calculated_at=datetime.utcnow(),
        )

    def _extract_complexity_signals(
        self,
        signal_outputs: List[Any]
    ) -> List[ExposureSignalOutput]:
        """Extract complexity-relevant signals from full signal outputs."""
        complexity_signals = []

        for signal in signal_outputs:
            signal_id = getattr(signal, 'signal_id', None)
            if signal_id and signal_id in self._signal_config:
                feature_config = self._signal_config[signal_id]

                raw_value = getattr(signal, 'raw_score', 0.0)
                normalized = self._normalize_value(raw_value, feature_config.normalizer)

                complexity_signals.append(ExposureSignalOutput(
                    signal_id=signal_id,
                    raw_value=raw_value,
                    normalized_value=normalized,
                    confidence=getattr(signal, 'confidence', 0.0),
                    proxy_tier=feature_config.proxy_tier,
                    data_sources=getattr(signal, 'data_sources', []),
                    extracted_at=getattr(signal, 'extracted_at', datetime.utcnow()),
                ))

        return complexity_signals

    def _normalize_value(self, value: float, normalizer: str) -> float:
        """Normalize a value based on the specified method."""
        if normalizer == "linear":
            return max(0, min(100, value))
        elif normalizer == "log_scale":
            import math
            if value <= 0:
                return 0.0
            return min(100, math.log10(value + 1) * 25)
        elif normalizer == "count_to_score":
            # Convert counts to complexity score
            # 1 = 20, 2-3 = 40, 4-6 = 60, 7-10 = 80, 11+ = 100
            if value <= 1:
                return 20.0
            elif value <= 3:
                return 40.0
            elif value <= 6:
                return 60.0
            elif value <= 10:
                return 80.0
            else:
                return 100.0
        else:
            return max(0, min(100, value))

    def _calculate_group_scores(
        self,
        signals: List[ExposureSignalOutput]
    ) -> List[ExposureGroupScore]:
        """Calculate weighted scores for each complexity group."""
        group_scores = []
        signal_map = {s.signal_id: s for s in signals}

        for group in self._sorted_groups:
            contributing = []
            weighted_sum = 0.0
            weight_sum = 0.0
            confidence_sum = 0.0

            for feature in group.features:
                signal = signal_map.get(feature.id)
                if signal and signal.confidence > 0:
                    contributing.append(feature.id)
                    weighted_sum += signal.normalized_value * feature.weight * signal.confidence
                    weight_sum += feature.weight * signal.confidence
                    confidence_sum += signal.confidence * feature.weight

            if weight_sum > 0:
                group_score = weighted_sum / weight_sum
                total_weight = sum(f.weight for f in group.features)
                group_confidence = confidence_sum / total_weight if total_weight > 0 else 0.0
            else:
                group_score = 0.0
                group_confidence = 0.0

            group_scores.append(ExposureGroupScore(
                group_name=group.name,
                score=round(group_score, 2),
                confidence=round(group_confidence, 3),
                weight=group.weight,
                signals_available=len(contributing),
                signals_total=len(group.features),
                contributing_signals=tuple(contributing),
                proxy_tier=ProxyTier.INFERRED_PROXY,
            ))

        return group_scores

    def _calculate_component_score(
        self,
        group_scores: List[ExposureGroupScore],
        component: str
    ) -> float:
        """Calculate score for a specific complexity component."""
        # Find groups that map to this component
        component_groups = [
            gs for gs in group_scores
            if component in gs.group_name.lower()
        ]

        if not component_groups:
            return 0.0

        # Weighted average
        total_weight = sum(gs.weight for gs in component_groups)
        if total_weight == 0:
            return 0.0

        return sum(gs.score * gs.weight for gs in component_groups) / total_weight

    def _calculate_composite(
        self,
        group_scores: List[ExposureGroupScore]
    ) -> Tuple[float, float]:
        """
        Calculate composite complexity score and confidence.

        Returns: (score, confidence)
        """
        weighted_sum = 0.0
        weight_sum = 0.0
        confidence_sum = 0.0
        total_weight = 0.0

        for gs in group_scores:
            if gs.confidence > 0:
                weighted_sum += gs.score * gs.weight * gs.confidence
                weight_sum += gs.weight * gs.confidence
                confidence_sum += gs.confidence * gs.weight
            total_weight += gs.weight

        if weight_sum == 0:
            return (0.0, 0.0)

        score = weighted_sum / weight_sum
        confidence = confidence_sum / total_weight if total_weight > 0 else 0.0

        return (score, confidence)

    def _map_to_category(self, score: float) -> ComplexityCategory:
        """Map complexity score to category."""
        for cat_config in self._sorted_categories:
            if cat_config.min_score <= score < cat_config.max_score:
                return ComplexityCategory(cat_config.name)

        # Default mapping if no config
        if score < 20:
            return ComplexityCategory.SIMPLE
        elif score < 40:
            return ComplexityCategory.MODERATE
        elif score < 60:
            return ComplexityCategory.COMPLEX
        elif score < 80:
            return ComplexityCategory.HIGHLY_COMPLEX
        else:
            return ComplexityCategory.EXTREMELY_COMPLEX

    def _get_complexity_modifier(self, category: ComplexityCategory) -> float:
        """Get pricing modifier for complexity category."""
        for cat_config in self._sorted_categories:
            if cat_config.name == category.value:
                return cat_config.complexity_modifier

        # Default modifiers
        default_modifiers = {
            ComplexityCategory.SIMPLE: 0.90,
            ComplexityCategory.MODERATE: 1.00,
            ComplexityCategory.COMPLEX: 1.15,
            ComplexityCategory.HIGHLY_COMPLEX: 1.35,
            ComplexityCategory.EXTREMELY_COMPLEX: 1.60,
        }
        return default_modifiers.get(category, 1.0)

    def _create_default_result(self) -> ComplexityResult:
        """Create default result when no signals available."""
        return ComplexityResult(
            score=30.0,
            category=ComplexityCategory.MODERATE,
            confidence=0.0,
            geographic_score=0.0,
            structural_score=0.0,
            technical_score=0.0,
            regulatory_score=0.0,
            complexity_modifier=1.0,
            calculated_at=datetime.utcnow(),
        )
