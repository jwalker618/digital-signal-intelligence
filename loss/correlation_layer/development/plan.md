# Loss Signal Correlation Layer - Development Plan

## Overview

The Loss Signal Correlation Layer extends DSI from risk quality assessment to loss prediction. By correlating observable signals with historical loss outcomes, the system can infer loss propensity for new submissions, enable cohort-based pricing adjustments, and provide continuous risk monitoring.

This document provides the implementation plan for integrating the Loss Signal Correlation Layer into the existing DSI framework.

---

## Architecture Integration

The Loss Signal Correlation Layer integrates into the existing DSI architecture as a parallel processing path:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENHANCED DSI ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     SIGNAL EXTRACTION                     │   │
│  │                    (Steps 0-4 unchanged)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│              ┌───────────────┼───────────────┐                  │
│              │               │               │                  │
│              ▼               ▼               ▼                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ RISK SCORING │ │  EXPOSURE    │ │    LOSS      │            │
│  │              │ │  SHADOW      │ │ CORRELATION  │            │
│  │ Steps 5-6   │ │  LAYER       │ │    LAYER     │            │
│  │ Composite   │ │              │ │              │            │
│  │ + Conditions│ │ Exposure Band│ │ Propensity   │            │
│  │             │ │ + Complexity │ │ + Cohort     │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│              │               │               │                  │
│              └───────────────┼───────────────┘                  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    PRICING ENGINE                         │   │
│  │                                                           │   │
│  │  Risk Tier × Exposure Band × Loss Propensity → Premium   │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   DECISION + MONITORING                   │   │
│  │                                                           │   │
│  │  Decision + Continuous Loss Propensity Tracking          │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 15: Loss Signal Correlation Layer (NEW)

This phase implements the Loss Signal Correlation Layer following the pattern established by the Exposure Shadow Layer.

### 15.1 Core Types (`model/loss_correlation/types.py`)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

class CorrelationType(Enum):
    FREQUENCY = "frequency"
    SEVERITY = "severity"
    BOTH = "both"

class CorrelationDirection(Enum):
    POSITIVE = "positive"  # Higher signal = higher loss
    NEGATIVE = "negative"  # Higher signal = lower loss

class LossPropensityBand(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"

class SeverityPropensityBand(Enum):
    MINIMAL = "minimal"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    SEVERE = "severe"
    CATASTROPHIC = "catastrophic"

class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DETERIORATING = "deteriorating"

@dataclass
class LossSignalResult:
    """Output from a loss-predictive signal extraction"""
    signal_id: str
    value: Any
    normalized_value: float  # 0-100
    confidence: float  # 0-1
    correlation_type: CorrelationType
    correlation_direction: CorrelationDirection
    source_urls: List[str]
    extracted_at: datetime
    notes: Optional[str] = None

@dataclass
class LossCorrelationFeatureConfig:
    """Configuration for a single loss-predictive signal"""
    id: str
    weight: float
    correlation_type: CorrelationType
    correlation_direction: CorrelationDirection
    normalizer: str
    thresholds: Optional[List[float]] = None
    percentiles: Optional[List[float]] = None
    mapping: Optional[Dict[str, float]] = None
    cap: Optional[float] = None
    lag_months: Optional[int] = None

@dataclass
class LossCorrelationGroupConfig:
    """Configuration for a group of loss-predictive signals"""
    name: str
    weight: float
    confidence_threshold: float
    features: List[LossCorrelationFeatureConfig]

@dataclass
class PropensityBandConfig:
    """Configuration for a loss propensity band"""
    name: str
    min_score: float
    max_score: float
    expected_frequency_multiplier: float
    expected_severity_multiplier: float

@dataclass
class CohortDefinition:
    """Definition of a signal-derived peer cohort"""
    id: str
    name: str
    criteria: Dict[str, Any]
    historical_frequency: Optional[float] = None
    historical_severity: Optional[float] = None
    member_count: Optional[int] = None
    calibration_date: Optional[datetime] = None

@dataclass
class LossCorrelationConfig:
    """Complete loss correlation configuration from YAML"""
    enabled: bool
    version: str
    correlation_groups: List[LossCorrelationGroupConfig]
    propensity_band_mapping_method: str
    propensity_bands: List[PropensityBandConfig]
    severity_bands: List[PropensityBandConfig]
    cohort_definitions: List[CohortDefinition]
    pricing_integration_method: str
    frequency_impact_cap: float
    frequency_impact_floor: float
    severity_impact_cap: float
    severity_impact_floor: float
    frequency_weight: float
    severity_weight: float
    auto_apply_rules: List[Dict]
    monitoring_config: Dict

@dataclass
class LossPropensityResult:
    """Complete output from loss propensity calculation"""
    # Primary scores
    loss_propensity_score: float  # 0-100
    severity_propensity_score: float  # 0-100
    loss_propensity_band: LossPropensityBand
    severity_propensity_band: SeverityPropensityBand
    loss_confidence: float  # 0-1
    
    # Cohort assignment
    cohort_id: str
    cohort_name: str
    cohort_confidence: float
    
    # Component scores
    group_scores: Dict[str, float]
    group_confidences: Dict[str, float]
    frequency_group_scores: Dict[str, float]
    severity_group_scores: Dict[str, float]
    
    # Pricing impact
    frequency_multiplier: float
    severity_multiplier: float
    combined_loss_modifier: float
    
    # Monitoring
    trend_direction: TrendDirection
    score_velocity: float  # points per month
    days_since_last_assessment: int
    previous_score: Optional[float]
    
    # Referral triggers
    referral_triggered: bool
    referral_reasons: List[str]
    flags: List[str]
    
    # Audit trail
    signal_results: List[LossSignalResult]
    calculated_at: datetime
    config_version: str
    correlation_matrix_version: Optional[str]

@dataclass
class CorrelationMatrixEntry:
    """Entry in the loss correlation matrix"""
    signal_id: str
    frequency_correlation: float  # -1 to 1
    severity_correlation: float  # -1 to 1
    information_value: float  # 0 to 1
    stability_score: float  # 0 to 1
    sample_size: int
    last_updated: datetime
    interaction_effects: List[Dict[str, Any]]

@dataclass
class CorrelationMatrix:
    """Complete correlation matrix for a coverage"""
    coverage: str
    version: str
    created_at: datetime
    observation_period_start: datetime
    observation_period_end: datetime
    policy_count: int
    claim_count: int
    entries: List[CorrelationMatrixEntry]
    cohort_calibrations: List[Dict[str, Any]]
```

### 15.2 Loss Correlation Scorer (`model/loss_correlation/scorer.py`)

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .types import (
    LossCorrelationConfig,
    LossPropensityResult,
    LossSignalResult,
    LossPropensityBand,
    SeverityPropensityBand,
    TrendDirection,
    CorrelationType,
    CorrelationDirection
)
from ..types import SignalOutput

class LossCorrelationScorer:
    """
    Calculates loss propensity scores from signal outputs.
    
    Operates in parallel with risk scoring, using the same
    signal extraction results but applying loss-specific
    weighting and correlation logic.
    """
    
    def __init__(self, config: LossCorrelationConfig):
        self.config = config
        self._build_signal_lookup()
    
    def _build_signal_lookup(self):
        """Build lookup table for signal configuration"""
        self.signal_config = {}
        for group in self.config.correlation_groups:
            for feature in group.features:
                self.signal_config[feature.id] = {
                    'group': group.name,
                    'weight': feature.weight,
                    'group_weight': group.weight,
                    'correlation_type': feature.correlation_type,
                    'correlation_direction': feature.correlation_direction,
                    'normalizer': feature.normalizer,
                    'thresholds': feature.thresholds,
                    'lag_months': feature.lag_months
                }
    
    def calculate_propensity(
        self,
        signal_outputs: List[SignalOutput],
        previous_result: Optional[LossPropensityResult] = None
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
        frequency_group_scores, severity_group_scores, group_confidences = \
            self._calculate_group_scores(loss_signals)
        
        # Calculate composite scores
        loss_propensity_score = self._calculate_composite(
            frequency_group_scores, 
            self.config.correlation_groups
        )
        severity_propensity_score = self._calculate_composite(
            severity_group_scores,
            self.config.correlation_groups
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
            severity_multiplier
        )
        
        # Calculate trend
        trend_direction, score_velocity = self._calculate_trend(
            loss_propensity_score, 
            previous_result
        )
        
        # Evaluate referral triggers
        referral_triggered, referral_reasons, flags = self._evaluate_rules(
            loss_propensity_score,
            loss_propensity_band,
            loss_confidence,
            previous_result
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
            frequency_group_scores=frequency_group_scores,
            severity_group_scores=severity_group_scores,
            frequency_multiplier=frequency_multiplier,
            severity_multiplier=severity_multiplier,
            combined_loss_modifier=combined_modifier,
            trend_direction=trend_direction,
            score_velocity=score_velocity,
            days_since_last_assessment=self._days_since_last(previous_result),
            previous_score=previous_result.loss_propensity_score if previous_result else None,
            referral_triggered=referral_triggered,
            referral_reasons=referral_reasons,
            flags=flags,
            signal_results=loss_signals,
            calculated_at=datetime.utcnow(),
            config_version=self.config.version,
            correlation_matrix_version=None  # Set if using calibrated matrix
        )
    
    def _extract_loss_signals(
        self, 
        signal_outputs: List[SignalOutput]
    ) -> List[LossSignalResult]:
        """Extract loss-relevant signals from signal outputs"""
        loss_signals = []
        
        for output in signal_outputs:
            if output.signal_id in self.signal_config:
                config = self.signal_config[output.signal_id]
                
                # Apply direction adjustment
                normalized = output.raw_score
                if config['correlation_direction'] == CorrelationDirection.NEGATIVE:
                    normalized = 100 - normalized
                
                loss_signals.append(LossSignalResult(
                    signal_id=output.signal_id,
                    value=output.raw_score,
                    normalized_value=normalized,
                    confidence=output.confidence,
                    correlation_type=config['correlation_type'],
                    correlation_direction=config['correlation_direction'],
                    source_urls=output.data_sources,
                    extracted_at=output.extracted_at
                ))
        
        return loss_signals
    
    def _calculate_group_scores(
        self, 
        loss_signals: List[LossSignalResult]
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
        """Calculate frequency and severity scores for each group"""
        frequency_scores = {}
        severity_scores = {}
        confidences = {}
        
        # Group signals by correlation group
        signals_by_group = {}
        for signal in loss_signals:
            group = self.signal_config[signal.signal_id]['group']
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
                weight = feature_config['weight']
                
                if signal.correlation_type in [CorrelationType.FREQUENCY, CorrelationType.BOTH]:
                    freq_weighted_sum += signal.normalized_value * weight
                    freq_weight_total += weight
                
                if signal.correlation_type in [CorrelationType.SEVERITY, CorrelationType.BOTH]:
                    sev_weighted_sum += signal.normalized_value * weight
                    sev_weight_total += weight
                
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
        groups: List
    ) -> float:
        """Calculate weighted composite score"""
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
        """Map score to propensity band"""
        for band in self.config.propensity_bands:
            if band.min_score <= score < band.max_score:
                return LossPropensityBand(band.name)
        return LossPropensityBand.MODERATE
    
    def _map_to_severity_band(self, score: float) -> SeverityPropensityBand:
        """Map score to severity band"""
        for band in self.config.severity_bands:
            if band.min_score <= score < band.max_score:
                return SeverityPropensityBand(band.name)
        return SeverityPropensityBand.MODERATE
    
    def _get_frequency_multiplier(self, band: LossPropensityBand) -> float:
        """Get frequency multiplier for band"""
        for band_config in self.config.propensity_bands:
            if band_config.name == band.value:
                return band_config.expected_frequency_multiplier
        return 1.0
    
    def _get_severity_multiplier(self, band: SeverityPropensityBand) -> float:
        """Get severity multiplier for band"""
        for band_config in self.config.severity_bands:
            if band_config.name == band.value:
                return band_config.expected_severity_multiplier
        return 1.0
    
    def _calculate_combined_modifier(
        self, 
        frequency_mult: float, 
        severity_mult: float
    ) -> float:
        """Calculate combined loss modifier"""
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
        loss_signals: List[LossSignalResult]
    ) -> Tuple[str, str, float]:
        """Assign entity to cohort based on signal pattern"""
        # Check predefined cohorts first
        for cohort in self.config.cohort_definitions:
            if self._matches_cohort_criteria(loss_signals, cohort.criteria):
                return cohort.id, cohort.name, 0.9
        
        # Default cohort
        return "default", "Standard", 0.5
    
    def _matches_cohort_criteria(
        self, 
        signals: List[LossSignalResult], 
        criteria: Dict[str, Any]
    ) -> bool:
        """Check if signals match cohort criteria"""
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
        
        return True
    
    def _calculate_trend(
        self, 
        current_score: float,
        previous: Optional[LossPropensityResult]
    ) -> Tuple[TrendDirection, float]:
        """Calculate trend direction and velocity"""
        if previous is None:
            return TrendDirection.STABLE, 0.0
        
        days_elapsed = (datetime.utcnow() - previous.calculated_at).days
        if days_elapsed == 0:
            return TrendDirection.STABLE, 0.0
        
        score_delta = current_score - previous.loss_propensity_score
        velocity = score_delta / (days_elapsed / 30)  # points per month
        
        if score_delta > 5:
            direction = TrendDirection.DETERIORATING
        elif score_delta < -5:
            direction = TrendDirection.IMPROVING
        else:
            direction = TrendDirection.STABLE
        
        return direction, velocity
    
    def _evaluate_rules(
        self,
        score: float,
        band: LossPropensityBand,
        confidence: float,
        previous: Optional[LossPropensityResult]
    ) -> Tuple[bool, List[str], List[str]]:
        """Evaluate auto-apply rules"""
        referral_triggered = False
        referral_reasons = []
        flags = []
        
        for rule in self.config.auto_apply_rules:
            if self._evaluate_condition(rule['condition'], score, band, confidence, previous):
                if rule['action'] == 'refer':
                    referral_triggered = True
                    referral_reasons.append(rule.get('reason', 'Loss propensity rule triggered'))
                elif rule['action'] == 'flag':
                    flags.append(rule.get('reason', 'Loss propensity flag'))
        
        return referral_triggered, referral_reasons, flags
    
    def _calculate_confidence(self, group_confidences: Dict[str, float]) -> float:
        """Calculate overall confidence"""
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
        """Calculate days since last assessment"""
        if previous is None:
            return 0
        return (datetime.utcnow() - previous.calculated_at).days
    
    def _evaluate_condition(
        self,
        condition: str,
        score: float,
        band: LossPropensityBand,
        confidence: float,
        previous: Optional[LossPropensityResult]
    ) -> bool:
        """Evaluate a rule condition"""
        # Simple condition evaluation - extend as needed
        context = {
            'loss_propensity_score': score,
            'loss_propensity_band': band.value,
            'loss_confidence': confidence,
            'loss_propensity_score_delta': (
                score - previous.loss_propensity_score 
                if previous else 0
            )
        }
        
        try:
            # Safe evaluation of simple conditions
            return eval(condition, {"__builtins__": {}}, context)
        except:
            return False
```

### 15.3 Correlation Matrix Manager (`model/loss_correlation/matrix.py`)

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from scipy import stats

from .types import CorrelationMatrix, CorrelationMatrixEntry

class CorrelationMatrixManager:
    """
    Manages the loss correlation matrix - the empirically-derived
    relationships between signals and loss outcomes.
    
    This component requires historical policy + loss data for calibration.
    """
    
    def __init__(self, coverage: str):
        self.coverage = coverage
        self.matrix: Optional[CorrelationMatrix] = None
    
    def calibrate(
        self,
        policies: List[Dict],  # Policy data with signal snapshots
        losses: List[Dict],    # Loss data linked to policies
        observation_start: datetime,
        observation_end: datetime
    ) -> CorrelationMatrix:
        """
        Calibrate correlation matrix from historical data.
        
        Args:
            policies: List of policies with signal snapshots at bind
            losses: List of losses linked to policy IDs
            observation_start: Start of observation period
            observation_end: End of observation period
            
        Returns:
            Calibrated correlation matrix
        """
        # Link losses to policies
        policy_outcomes = self._link_losses_to_policies(policies, losses)
        
        # Extract signal IDs from first policy
        signal_ids = list(policies[0].get('signals', {}).keys())
        
        entries = []
        for signal_id in signal_ids:
            entry = self._calculate_signal_correlation(
                signal_id, 
                policy_outcomes
            )
            if entry is not None:
                entries.append(entry)
        
        # Calculate cohort calibrations
        cohort_calibrations = self._calibrate_cohorts(policy_outcomes)
        
        self.matrix = CorrelationMatrix(
            coverage=self.coverage,
            version=datetime.utcnow().strftime("%Y-%m-%d"),
            created_at=datetime.utcnow(),
            observation_period_start=observation_start,
            observation_period_end=observation_end,
            policy_count=len(policies),
            claim_count=len(losses),
            entries=entries,
            cohort_calibrations=cohort_calibrations
        )
        
        return self.matrix
    
    def _link_losses_to_policies(
        self, 
        policies: List[Dict], 
        losses: List[Dict]
    ) -> List[Dict]:
        """Link losses to policies and create outcome records"""
        loss_by_policy = {}
        for loss in losses:
            policy_id = loss['policy_id']
            if policy_id not in loss_by_policy:
                loss_by_policy[policy_id] = []
            loss_by_policy[policy_id].append(loss)
        
        outcomes = []
        for policy in policies:
            policy_id = policy['policy_id']
            policy_losses = loss_by_policy.get(policy_id, [])
            
            outcomes.append({
                'policy_id': policy_id,
                'signals': policy.get('signals', {}),
                'has_loss': len(policy_losses) > 0,
                'loss_count': len(policy_losses),
                'total_incurred': sum(l.get('incurred', 0) for l in policy_losses),
                'max_severity': max((l.get('incurred', 0) for l in policy_losses), default=0)
            })
        
        return outcomes
    
    def _calculate_signal_correlation(
        self, 
        signal_id: str, 
        outcomes: List[Dict]
    ) -> Optional[CorrelationMatrixEntry]:
        """Calculate correlation for a single signal"""
        # Extract signal values and outcomes
        signal_values = []
        has_loss = []
        loss_amounts = []
        
        for outcome in outcomes:
            if signal_id in outcome['signals']:
                signal_values.append(outcome['signals'][signal_id])
                has_loss.append(1 if outcome['has_loss'] else 0)
                if outcome['has_loss']:
                    loss_amounts.append(outcome['total_incurred'])
        
        if len(signal_values) < 30:  # Minimum sample size
            return None
        
        # Calculate frequency correlation
        freq_corr, freq_pvalue = stats.pearsonr(signal_values, has_loss)
        
        # Calculate severity correlation (only for policies with losses)
        if len(loss_amounts) >= 10:
            loss_signal_values = [
                v for v, h in zip(signal_values, has_loss) if h == 1
            ]
            sev_corr, sev_pvalue = stats.pearsonr(loss_signal_values, loss_amounts)
        else:
            sev_corr = 0.0
        
        # Calculate information value
        iv = self._calculate_information_value(signal_values, has_loss)
        
        # Assess stability (would need multiple time periods)
        stability = 0.8  # Placeholder
        
        return CorrelationMatrixEntry(
            signal_id=signal_id,
            frequency_correlation=freq_corr,
            severity_correlation=sev_corr,
            information_value=iv,
            stability_score=stability,
            sample_size=len(signal_values),
            last_updated=datetime.utcnow(),
            interaction_effects=[]
        )
    
    def _calculate_information_value(
        self, 
        signal_values: List[float], 
        outcomes: List[int]
    ) -> float:
        """Calculate information value for predictive power"""
        # Bin signal values into deciles
        bins = np.percentile(signal_values, [10, 20, 30, 40, 50, 60, 70, 80, 90])
        binned = np.digitize(signal_values, bins)
        
        total_good = sum(1 for o in outcomes if o == 0)
        total_bad = sum(1 for o in outcomes if o == 1)
        
        if total_good == 0 or total_bad == 0:
            return 0.0
        
        iv = 0.0
        for b in range(len(bins) + 1):
            bin_outcomes = [o for v, o in zip(binned, outcomes) if v == b]
            if not bin_outcomes:
                continue
            
            good_pct = sum(1 for o in bin_outcomes if o == 0) / total_good
            bad_pct = sum(1 for o in bin_outcomes if o == 1) / total_bad
            
            if good_pct > 0 and bad_pct > 0:
                iv += (good_pct - bad_pct) * np.log(good_pct / bad_pct)
        
        return abs(iv)
    
    def _calibrate_cohorts(self, outcomes: List[Dict]) -> List[Dict]:
        """Calibrate cohort loss experience"""
        # Group by cohort and calculate loss metrics
        # Implementation depends on cohort definition method
        return []
    
    def get_signal_correlation(
        self, 
        signal_id: str
    ) -> Optional[CorrelationMatrixEntry]:
        """Get correlation entry for a signal"""
        if self.matrix is None:
            return None
        
        for entry in self.matrix.entries:
            if entry.signal_id == signal_id:
                return entry
        return None
    
    def get_high_correlation_signals(
        self, 
        min_correlation: float = 0.2,
        correlation_type: str = 'frequency'
    ) -> List[CorrelationMatrixEntry]:
        """Get signals with high correlation to loss"""
        if self.matrix is None:
            return []
        
        results = []
        for entry in self.matrix.entries:
            if correlation_type == 'frequency':
                if abs(entry.frequency_correlation) >= min_correlation:
                    results.append(entry)
            elif correlation_type == 'severity':
                if abs(entry.severity_correlation) >= min_correlation:
                    results.append(entry)
        
        return sorted(results, key=lambda e: abs(e.frequency_correlation), reverse=True)
```

### 15.4 Monitoring Engine (`model/loss_correlation/monitoring.py`)

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .types import LossPropensityResult, TrendDirection
from .scorer import LossCorrelationScorer

@dataclass
class DeteriorationAlert:
    """Alert for deteriorating loss propensity"""
    entity_id: str
    alert_type: str  # 'warning', 'critical'
    current_score: float
    previous_score: float
    score_delta: float
    days_elapsed: int
    current_band: str
    previous_band: str
    trigger_reason: str
    recommended_action: str
    created_at: datetime

@dataclass
class MonitoringResult:
    """Result of monitoring check"""
    entity_id: str
    current_result: LossPropensityResult
    previous_result: Optional[LossPropensityResult]
    alerts: List[DeteriorationAlert]
    refresh_recommended: bool
    next_refresh_date: datetime

class LossMonitoringEngine:
    """
    Continuous monitoring of loss propensity for in-force policies.
    
    Detects deterioration, triggers alerts, and recommends actions.
    """
    
    def __init__(
        self,
        scorer: LossCorrelationScorer,
        deterioration_threshold: float = 15.0,
        improvement_threshold: float = 15.0,
        refresh_frequency_days: int = 30
    ):
        self.scorer = scorer
        self.deterioration_threshold = deterioration_threshold
        self.improvement_threshold = improvement_threshold
        self.refresh_frequency_days = refresh_frequency_days
        
        # Cache of previous results by entity
        self.result_cache: Dict[str, LossPropensityResult] = {}
    
    def check_entity(
        self,
        entity_id: str,
        signal_outputs: List,
        force_refresh: bool = False
    ) -> MonitoringResult:
        """
        Check an entity's loss propensity and generate alerts.
        
        Args:
            entity_id: Entity identifier
            signal_outputs: Current signal extraction results
            force_refresh: Force recalculation regardless of cache
            
        Returns:
            Monitoring result with alerts and recommendations
        """
        previous_result = self.result_cache.get(entity_id)
        
        # Check if refresh is needed
        refresh_needed = force_refresh or self._needs_refresh(previous_result)
        
        if not refresh_needed and previous_result is not None:
            return MonitoringResult(
                entity_id=entity_id,
                current_result=previous_result,
                previous_result=None,
                alerts=[],
                refresh_recommended=False,
                next_refresh_date=self._next_refresh_date(previous_result)
            )
        
        # Calculate new propensity
        current_result = self.scorer.calculate_propensity(
            signal_outputs, 
            previous_result
        )
        
        # Generate alerts
        alerts = self._generate_alerts(entity_id, current_result, previous_result)
        
        # Update cache
        self.result_cache[entity_id] = current_result
        
        return MonitoringResult(
            entity_id=entity_id,
            current_result=current_result,
            previous_result=previous_result,
            alerts=alerts,
            refresh_recommended=len(alerts) > 0,
            next_refresh_date=self._next_refresh_date(current_result)
        )
    
    def _needs_refresh(self, previous: Optional[LossPropensityResult]) -> bool:
        """Check if refresh is needed based on time"""
        if previous is None:
            return True
        
        days_elapsed = (datetime.utcnow() - previous.calculated_at).days
        return days_elapsed >= self.refresh_frequency_days
    
    def _next_refresh_date(self, result: LossPropensityResult) -> datetime:
        """Calculate next recommended refresh date"""
        base_date = result.calculated_at
        
        # More frequent refresh for deteriorating risks
        if result.trend_direction == TrendDirection.DETERIORATING:
            days = self.refresh_frequency_days // 2
        else:
            days = self.refresh_frequency_days
        
        return base_date + timedelta(days=days)
    
    def _generate_alerts(
        self,
        entity_id: str,
        current: LossPropensityResult,
        previous: Optional[LossPropensityResult]
    ) -> List[DeteriorationAlert]:
        """Generate alerts based on changes"""
        alerts = []
        
        if previous is None:
            return alerts
        
        score_delta = current.loss_propensity_score - previous.loss_propensity_score
        days_elapsed = (current.calculated_at - previous.calculated_at).days
        
        # Check for significant deterioration
        if score_delta >= self.deterioration_threshold:
            alert_type = 'critical' if score_delta >= self.deterioration_threshold * 1.5 else 'warning'
            
            alerts.append(DeteriorationAlert(
                entity_id=entity_id,
                alert_type=alert_type,
                current_score=current.loss_propensity_score,
                previous_score=previous.loss_propensity_score,
                score_delta=score_delta,
                days_elapsed=days_elapsed,
                current_band=current.loss_propensity_band.value,
                previous_band=previous.loss_propensity_band.value,
                trigger_reason=f"Loss propensity increased by {score_delta:.1f} points",
                recommended_action=self._get_recommended_action(current, score_delta),
                created_at=datetime.utcnow()
            ))
        
        # Check for band migration
        if current.loss_propensity_band != previous.loss_propensity_band:
            band_order = ['very_low', 'low', 'moderate', 'elevated', 'high']
            current_idx = band_order.index(current.loss_propensity_band.value)
            previous_idx = band_order.index(previous.loss_propensity_band.value)
            
            if current_idx > previous_idx:  # Deteriorated
                alerts.append(DeteriorationAlert(
                    entity_id=entity_id,
                    alert_type='warning',
                    current_score=current.loss_propensity_score,
                    previous_score=previous.loss_propensity_score,
                    score_delta=score_delta,
                    days_elapsed=days_elapsed,
                    current_band=current.loss_propensity_band.value,
                    previous_band=previous.loss_propensity_band.value,
                    trigger_reason=f"Loss propensity band changed from {previous.loss_propensity_band.value} to {current.loss_propensity_band.value}",
                    recommended_action="Review risk and consider renewal terms adjustment",
                    created_at=datetime.utcnow()
                ))
        
        return alerts
    
    def _get_recommended_action(
        self, 
        result: LossPropensityResult, 
        score_delta: float
    ) -> str:
        """Get recommended action based on current state"""
        if result.loss_propensity_band.value == 'high':
            return "Immediate underwriter review required. Consider non-renewal or significant terms adjustment."
        elif result.loss_propensity_band.value == 'elevated':
            return "Flag for renewal review. Consider risk improvement outreach."
        elif score_delta >= 20:
            return "Significant deterioration detected. Investigate cause and monitor closely."
        else:
            return "Continue standard monitoring. Note change for renewal consideration."
    
    def get_portfolio_alerts(
        self,
        min_severity: str = 'warning'
    ) -> List[DeteriorationAlert]:
        """Get all active alerts across portfolio"""
        # This would query from persistent storage in production
        all_alerts = []
        for entity_id, result in self.result_cache.items():
            if result.referral_triggered:
                # Generate summary alerts
                pass
        return all_alerts
    
    def get_deteriorating_entities(
        self,
        min_score_delta: float = 10.0
    ) -> List[str]:
        """Get list of entities showing deterioration"""
        deteriorating = []
        for entity_id, result in self.result_cache.items():
            if result.trend_direction == TrendDirection.DETERIORATING:
                if result.score_velocity >= min_score_delta / 30:  # per month
                    deteriorating.append(entity_id)
        return deteriorating
```

### 15.5 File Structure for Phase 15

```
technical_pricing/
├── model/
│   ├── loss_correlation/
│   │   ├── __init__.py
│   │   ├── types.py              # All dataclasses and enums
│   │   ├── scorer.py             # Loss propensity calculation
│   │   ├── matrix.py             # Correlation matrix management
│   │   ├── monitoring.py         # Continuous monitoring engine
│   │   └── integration.py        # Pricing integration patterns
│   └── ...
```

### 15.6 Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Create loss correlation types | `model/loss_correlation/types.py` | 🔲 Not Started |
| Implement LossCorrelationScorer | `model/loss_correlation/scorer.py` | 🔲 Not Started |
| Implement CorrelationMatrixManager | `model/loss_correlation/matrix.py` | 🔲 Not Started |
| Implement LossMonitoringEngine | `model/loss_correlation/monitoring.py` | 🔲 Not Started |
| Add pricing integration | `model/loss_correlation/integration.py` | 🔲 Not Started |
| Extend YAML config schema | `coverages/*/config.yaml` | 🔲 Not Started |
| Extend ModelVersion for loss data | `model/types.py` | 🔲 Not Started |
| Integrate into workflow | `model/workflow.py` | 🔲 Not Started |
| Add unit tests | `tests/unit/test_loss_correlation.py` | 🔲 Not Started |
| Add integration tests | `tests/integration/test_loss_workflow.py` | 🔲 Not Started |

---

## YAML Configuration Extension

Add to each coverage config.yaml:

```yaml
loss_correlation:
  enabled: true
  version: "2026-01-08"
  
  correlation_groups:
    - name: loss_technical_infrastructure
      weight: 0.35
      confidence_threshold: 0.7
      features:
        - id: security_header_completeness
          weight: 0.30
          correlation_type: both
          correlation_direction: negative
          normalizer: linear
          lag_months: 6
        # ... additional features
        
  propensity_band_mapping:
    method: fixed_threshold
    bands:
      - name: very_low
        min_score: 0
        max_score: 20
        expected_frequency_multiplier: 0.60
        expected_severity_multiplier: 0.70
      # ... additional bands
      
  pricing_integration:
    method: multiplicative
    frequency_impact_cap: 1.50
    frequency_impact_floor: 0.70
    frequency_weight: 0.60
    severity_weight: 0.40
    
  monitoring:
    refresh_frequency: monthly
    deterioration_threshold: 15
```

---

## Model Version Extensions

Add to ModelVersion dataclass:

```python
# Loss Propensity Outputs
loss_propensity_score: Optional[float] = None
severity_propensity_score: Optional[float] = None
loss_propensity_band: Optional[str] = None
severity_propensity_band: Optional[str] = None
loss_confidence: Optional[float] = None

# Cohort Assignment
loss_cohort_id: Optional[str] = None
loss_cohort_name: Optional[str] = None

# Pricing Impact
loss_frequency_multiplier: Optional[float] = None
loss_severity_multiplier: Optional[float] = None
loss_combined_modifier: Optional[float] = None

# Monitoring
loss_trend_direction: Optional[str] = None
loss_previous_score: Optional[float] = None
loss_score_velocity: Optional[float] = None
```

---

## Workflow Integration

Modify `model/workflow.py` to include loss correlation:

```python
def run_workflow(self, ...):
    # ... existing Steps 0-6 ...
    
    # NEW: Calculate loss propensity (parallel to risk scoring)
    if self.loss_correlation_scorer and config.loss_correlation.enabled:
        loss_result = self.loss_correlation_scorer.calculate_propensity(
            scoring_result.signal_outputs,
            previous_loss_result  # From model history if available
        )
    else:
        loss_result = None
    
    # ... Step 7: Query evaluation ...
    
    # ... Steps 8-12: Pricing ...
    # Modify pricing to include loss modifier
    if loss_result:
        base_premium *= loss_result.combined_loss_modifier
    
    # ... Step 13: Decision ...
    # Include loss referrals in decision
    if loss_result and loss_result.referral_triggered:
        referral_reasons.extend(loss_result.referral_reasons)
```

---

## Critical Rules for Loss Correlation Layer

1. **Parallel processing**: Loss correlation runs alongside risk scoring, not in sequence
2. **Same signals, different weights**: Uses same extracted signals with loss-specific weighting
3. **Direction matters**: Negative correlation signals are inverted before scoring
4. **Confidence gates decisions**: Low confidence prevents automatic pricing adjustments
5. **Caps and floors apply**: Pricing impact is bounded to prevent extreme adjustments
6. **Cohorts are signal-derived**: Not based on industry code or traditional segmentation
7. **Trend monitoring is continuous**: Not just at bind and renewal
8. **Correlation matrix requires calibration**: Initial weights are hypotheses, validated against loss data
9. **Deterioration triggers action**: Not just observation
10. **Full auditability**: Every pricing adjustment traces to signal patterns
