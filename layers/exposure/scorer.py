"""
Exposure Magnitude Scorer (Phase 17)

Calculates exposure magnitude score from observable signals,
enabling TIV estimation without client-provided data.
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
    ExposureResult,
    ExposureBand,
    ProxyTier,
)


class ExposureScorer:
    """
    Calculate exposure magnitude from observable signals.

    Uses a tiered proxy hierarchy:
    - Tier 1: Direct observables (market cap, regulatory filings)
    - Tier 2: Inferred proxies (digital footprint, network signals)
    - Tier 3: Cohort inference (peer group matching)
    - Tier 4: Unknown (insufficient data)

    Outputs bounded ranges rather than point estimates to
    acknowledge uncertainty.

    Usage:
        config = ExposureConfig.from_dict(yaml_data)
        scorer = ExposureScorer(config)
        result = scorer.score(signal_outputs)
    """

    def __init__(self, config: ExposureConfig):
        """
        Initialize exposure scorer.

        Args:
            config: Exposure configuration from YAML
        """
        self.config = config

        # Sort groups by weight for deterministic ordering
        self._sorted_groups = sorted(
            config.exposure_groups,
            key=lambda g: g.weight,
            reverse=True
        )

        # Build signal-to-config lookup
        self._signal_config: Dict[str, ExposureFeatureConfig] = {}
        for group in config.exposure_groups:
            for feature in group.features:
                self._signal_config[feature.id] = feature

        # Build band lookup sorted by min_score
        self._sorted_bands = sorted(
            config.exposure_bands,
            key=lambda b: b.min_score
        )

    def score(
        self,
        signal_outputs: List[Any],
        cohort_prior: Optional[Dict[str, Any]] = None
    ) -> ExposureResult:
        """
        Calculate exposure magnitude from signal outputs.

        Args:
            signal_outputs: Signal extraction results (SignalOutput objects)
            cohort_prior: Optional cohort prior for fallback estimation

        Returns:
            ExposureResult with score, band, confidence, and implied TIV range
        """
        # Convert signal outputs to exposure signal outputs
        exposure_signals = self._extract_exposure_signals(signal_outputs)

        if not exposure_signals:
            return self._create_unknown_result(cohort_prior)

        # Determine overall proxy tier
        proxy_tier = self._determine_proxy_tier(exposure_signals)

        # Calculate group scores
        group_scores = self._calculate_group_scores(exposure_signals)

        # Calculate composite score and confidence
        score, confidence = self._calculate_composite(group_scores)

        # Calculate bounded range
        range_low, range_high = self._calculate_range(score, confidence)

        # Map to exposure band
        band = self._map_to_band(score)

        # Get implied TIV range
        tiv_low, tiv_high = self._get_implied_tiv(band, range_low, range_high)

        # Get exposure modifier
        exposure_modifier = self._get_exposure_modifier(band)

        # Apply cohort prior if confidence is low
        cohort_applied = False
        cohort_id = None
        cohort_name = None

        if confidence < 0.5 and cohort_prior:
            score, confidence, band = self._apply_cohort_prior(
                score, confidence, cohort_prior
            )
            cohort_applied = True
            cohort_id = cohort_prior.get("cohort_id")
            cohort_name = cohort_prior.get("name")

        # Check for referral triggers
        referral_triggered, referral_reasons = self._check_referral_triggers(
            band, confidence, proxy_tier
        )

        # Collect flags
        flags = self._collect_flags(band, confidence, proxy_tier)

        return ExposureResult(
            score=round(score, 2),
            band=band,
            confidence=round(confidence, 3),
            proxy_tier=proxy_tier,
            range_low=round(range_low, 2),
            range_high=round(range_high, 2),
            implied_tiv_low=tiv_low,
            implied_tiv_high=tiv_high,
            group_scores={gs.group_name: gs.score for gs in group_scores},
            signals_used=[s.signal_id for s in exposure_signals if s.confidence > 0],
            signals_available=len([s for s in exposure_signals if s.confidence > 0]),
            signals_total=len(self._signal_config),
            cohort_id=cohort_id,
            cohort_name=cohort_name,
            cohort_prior_applied=cohort_applied,
            exposure_modifier=exposure_modifier,
            calculated_at=datetime.utcnow(),
            referral_triggered=referral_triggered,
            referral_reasons=referral_reasons,
            flags=flags,
        )

    def _extract_exposure_signals(
        self,
        signal_outputs: List[Any]
    ) -> List[ExposureSignalOutput]:
        """Extract exposure-relevant signals from full signal outputs."""
        exposure_signals = []

        for signal in signal_outputs:
            signal_id = getattr(signal, 'signal_id', None)
            if signal_id and signal_id in self._signal_config:
                feature_config = self._signal_config[signal_id]

                # Normalize the value based on configured normalizer
                raw_value = getattr(signal, 'raw_score', 0.0)
                normalized = self._normalize_value(raw_value, feature_config.normalizer)

                exposure_signals.append(ExposureSignalOutput(
                    signal_id=signal_id,
                    raw_value=raw_value,
                    normalized_value=normalized,
                    confidence=getattr(signal, 'confidence', 0.0),
                    proxy_tier=feature_config.proxy_tier,
                    data_sources=getattr(signal, 'data_sources', []),
                    extracted_at=getattr(signal, 'extracted_at', datetime.utcnow()),
                ))

        return exposure_signals

    def _normalize_value(self, value: float, normalizer: str) -> float:
        """Normalize a value based on the specified method."""
        if normalizer == "linear":
            # Assume value is already 0-100
            return max(0, min(100, value))
        elif normalizer == "log_scale":
            # Log scale for values that can vary widely
            import math
            if value <= 0:
                return 0.0
            return min(100, math.log10(value + 1) * 25)
        elif normalizer == "percentile":
            # Assume value is a percentile (0-100)
            return max(0, min(100, value))
        elif normalizer == "binary":
            # Binary: presence = 100, absence = 0
            return 100.0 if value > 0 else 0.0
        else:
            return max(0, min(100, value))

    def _determine_proxy_tier(
        self,
        signals: List[ExposureSignalOutput]
    ) -> ProxyTier:
        """
        Determine overall proxy tier based on available signals.

        Tier 1 signals override lower tiers if available with high confidence.
        """
        tier1_signals = [
            s for s in signals
            if s.proxy_tier == ProxyTier.DIRECT_OBSERVABLE
            and s.confidence > 0.8
        ]

        tier2_signals = [
            s for s in signals
            if s.proxy_tier == ProxyTier.INFERRED_PROXY
            and s.confidence > 0.5
        ]

        if tier1_signals:
            return ProxyTier.DIRECT_OBSERVABLE

        if len(tier2_signals) >= 4:
            avg_confidence = sum(s.confidence for s in tier2_signals) / len(tier2_signals)
            if avg_confidence >= 0.6:
                return ProxyTier.INFERRED_PROXY

        # Check if cohort inference is possible
        available_count = sum(1 for s in signals if s.confidence > 0)
        if available_count >= 2:
            return ProxyTier.COHORT_INFERENCE

        return ProxyTier.UNKNOWN

    def _calculate_group_scores(
        self,
        signals: List[ExposureSignalOutput]
    ) -> List[ExposureGroupScore]:
        """Calculate weighted scores for each signal group."""
        group_scores = []

        # Build signal lookup
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

            # Determine group proxy tier
            group_tier = self._determine_group_tier(
                [signal_map.get(f.id) for f in group.features if signal_map.get(f.id)]
            )

            group_scores.append(ExposureGroupScore(
                group_name=group.name,
                score=round(group_score, 2),
                confidence=round(group_confidence, 3),
                weight=group.weight,
                signals_available=len(contributing),
                signals_total=len(group.features),
                contributing_signals=tuple(contributing),
                proxy_tier=group_tier,
            ))

        return group_scores

    def _determine_group_tier(
        self,
        signals: List[Optional[ExposureSignalOutput]]
    ) -> ProxyTier:
        """Determine proxy tier for a signal group."""
        valid_signals = [s for s in signals if s and s.confidence > 0]
        if not valid_signals:
            return ProxyTier.UNKNOWN

        # Use best (lowest) tier among contributing signals
        tiers = [s.proxy_tier for s in valid_signals]
        return min(tiers, key=lambda t: t.value)

    def _calculate_composite(
        self,
        group_scores: List[ExposureGroupScore]
    ) -> Tuple[float, float]:
        """
        Calculate composite exposure score and confidence.

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

    def _calculate_range(
        self,
        point_estimate: float,
        confidence: float
    ) -> Tuple[float, float]:
        """
        Calculate bounded range based on confidence.

        Lower confidence = wider range.
        Max uncertainty is ±30 points at 0 confidence.
        """
        # Uncertainty factor: 30 points at 0 confidence, 5 points at 1.0 confidence
        uncertainty = 5 + (1 - confidence) * 25

        range_low = max(0, point_estimate - uncertainty)
        range_high = min(100, point_estimate + uncertainty)

        return (range_low, range_high)

    def _map_to_band(self, score: float) -> ExposureBand:
        """Map exposure score to band."""
        for band_config in self._sorted_bands:
            if band_config.min_score <= score < band_config.max_score:
                return ExposureBand(band_config.name)

        # Default to last band if score exceeds all
        if self._sorted_bands:
            return ExposureBand(self._sorted_bands[-1].name)

        return ExposureBand.MEDIUM

    def _get_implied_tiv(
        self,
        band: ExposureBand,
        range_low: float,
        range_high: float
    ) -> Tuple[float, float]:
        """Get implied TIV range for band."""
        for band_config in self._sorted_bands:
            if band_config.name == band.value:
                return (band_config.implied_tiv_low, band_config.implied_tiv_high)

        # Default TIV ranges by band
        default_tiv = {
            ExposureBand.MICRO: (0, 1_000_000),
            ExposureBand.SMALL: (1_000_000, 10_000_000),
            ExposureBand.MEDIUM: (10_000_000, 50_000_000),
            ExposureBand.LARGE: (50_000_000, 250_000_000),
            ExposureBand.VERY_LARGE: (250_000_000, 1_000_000_000),
        }
        return default_tiv.get(band, (0, 50_000_000))

    def _get_exposure_modifier(self, band: ExposureBand) -> float:
        """Get pricing modifier for exposure band."""
        for band_config in self._sorted_bands:
            if band_config.name == band.value:
                return band_config.exposure_modifier

        # Default modifiers
        default_modifiers = {
            ExposureBand.MICRO: 0.50,
            ExposureBand.SMALL: 0.75,
            ExposureBand.MEDIUM: 1.00,
            ExposureBand.LARGE: 1.50,
            ExposureBand.VERY_LARGE: 2.50,
        }
        return default_modifiers.get(band, 1.0)

    def _apply_cohort_prior(
        self,
        score: float,
        confidence: float,
        cohort_prior: Dict[str, Any]
    ) -> Tuple[float, float, ExposureBand]:
        """Apply cohort prior when confidence is low."""
        prior_score = cohort_prior.get("prior_score", 50.0)
        prior_confidence = cohort_prior.get("confidence", 0.5)

        # Weighted average of signal score and prior
        # Weight by confidence levels
        total_conf = confidence + prior_confidence
        if total_conf > 0:
            blended_score = (score * confidence + prior_score * prior_confidence) / total_conf
            blended_confidence = (confidence + prior_confidence) / 2
        else:
            blended_score = prior_score
            blended_confidence = prior_confidence

        blended_band = self._map_to_band(blended_score)

        return (blended_score, blended_confidence, blended_band)

    def _check_referral_triggers(
        self,
        band: ExposureBand,
        confidence: float,
        proxy_tier: ProxyTier
    ) -> Tuple[bool, List[str]]:
        """Check if referral should be triggered."""
        reasons = []

        # High exposure + low confidence = referral
        if band in [ExposureBand.LARGE, ExposureBand.VERY_LARGE] and confidence < 0.6:
            reasons.append(f"High exposure band ({band.value}) with low confidence ({confidence:.2f})")

        # Unknown proxy tier with medium+ exposure
        if proxy_tier == ProxyTier.UNKNOWN and band not in [ExposureBand.MICRO, ExposureBand.SMALL]:
            reasons.append(f"Insufficient data for exposure estimation (band: {band.value})")

        return (len(reasons) > 0, reasons)

    def _collect_flags(
        self,
        band: ExposureBand,
        confidence: float,
        proxy_tier: ProxyTier
    ) -> List[str]:
        """Collect flags for underwriter attention."""
        flags = []

        if confidence < 0.5:
            flags.append("Low confidence in exposure estimate")

        if proxy_tier == ProxyTier.COHORT_INFERENCE:
            flags.append("Exposure based on cohort inference (limited direct signals)")

        if band == ExposureBand.VERY_LARGE:
            flags.append("Very large exposure - verify with additional data")

        return flags

    def _create_unknown_result(
        self,
        cohort_prior: Optional[Dict[str, Any]] = None
    ) -> ExposureResult:
        """Create result when no exposure signals available."""
        if cohort_prior:
            prior_score = cohort_prior.get("prior_score", 50.0)
            prior_band = ExposureBand(cohort_prior.get("prior_band", "medium"))
            prior_confidence = cohort_prior.get("confidence", 0.3)
            tiv_low, tiv_high = self._get_implied_tiv(prior_band, 0, 100)
            modifier = self._get_exposure_modifier(prior_band)

            return ExposureResult(
                score=prior_score,
                band=prior_band,
                confidence=prior_confidence,
                proxy_tier=ProxyTier.COHORT_INFERENCE,
                range_low=max(0, prior_score - 30),
                range_high=min(100, prior_score + 30),
                implied_tiv_low=tiv_low,
                implied_tiv_high=tiv_high,
                cohort_id=cohort_prior.get("cohort_id"),
                cohort_name=cohort_prior.get("name"),
                cohort_prior_applied=True,
                exposure_modifier=modifier,
                referral_triggered=True,
                referral_reasons=["Exposure based solely on cohort prior - verify manually"],
            )

        return ExposureResult(
            score=50.0,
            band=ExposureBand.MEDIUM,
            confidence=0.0,
            proxy_tier=ProxyTier.UNKNOWN,
            range_low=0.0,
            range_high=100.0,
            implied_tiv_low=0,
            implied_tiv_high=100_000_000,
            exposure_modifier=1.0,
            referral_triggered=True,
            referral_reasons=["Unable to estimate exposure - no signals available"],
        )
