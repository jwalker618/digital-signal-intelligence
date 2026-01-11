# DSI Exposure Shadow Layer — Development Plan 

## Continuation of Phase 15.6: Exposure Scorer

### 10.2 File: `exposure/scorer.py` (continued)

```python
    def _determine_proxy_tier(
        self,
        signals: List[ExposureSignalOutput]
    ) -> ProxyTier:
        """
        Determine overall proxy tier based on available signals.
        """
        tier1_signals = [s for s in signals 
                        if s.proxy_tier == ProxyTier.DIRECT_OBSERVABLE 
                        and s.confidence > 0.8]
        tier2_signals = [s for s in signals 
                        if s.proxy_tier == ProxyTier.INFERRED_PROXY 
                        and s.confidence > 0.5]
        
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
                group_confidence = confidence_sum / sum(f.weight for f in group.features)
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
                proxy_tier=group_tier
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
        
        # Use lowest (best) tier among contributing signals
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
```

---

## 11. Phase 15.7: Complexity Scorer

### 11.1 Purpose

The ComplexityScorer calculates exposure complexity from complexity signals, measuring geographic, structural, technical, and regulatory complexity.

### 11.2 File: `exposure/complexity.py`

```python
"""
Exposure Complexity Scorer

Calculates exposure complexity score measuring how distributed,
interconnected, and structurally complex the exposure is.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from exposure.types import (
    ComplexityCategory,
    ComplexityResult,
    ExposureConfig,
    ExposureGroupConfig,
)
from signals.inference.registry import get_inference_function
from signals.types import InferenceContext, InferenceResult


class ComplexityScorer:
    """
    Calculate exposure complexity score.
    
    Complexity has four components:
    - Geographic: Number of countries/regions, dispersion
    - Structural: Number of subsidiaries, organizational depth
    - Technical: Technology heterogeneity, system diversity
    - Regulatory: Number of regulatory jurisdictions
    
    Usage:
        scorer = ComplexityScorer(config)
        result = scorer.score(entity_id, context)
    """
    
    # Component weights (configurable in YAML)
    DEFAULT_WEIGHTS = {
        "geographic": 0.30,
        "structural": 0.25,
        "technical": 0.25,
        "regulatory": 0.20,
    }
    
    def __init__(self, config: ExposureConfig):
        """Initialize with configuration."""
        self.config = config
        self._complexity_groups = [
            g for g in config.complexity_groups
            if g.signal_type == "complexity"
        ]
        self._thresholds = config.complexity_thresholds
    
    def score(
        self,
        entity_id: str,
        context: InferenceContext
    ) -> ComplexityResult:
        """
        Calculate complexity score for an entity.
        
        Args:
            entity_id: Entity identifier
            context: Inference context
        
        Returns:
            ComplexityResult with score, category, and components
        """
        # Calculate component scores
        geographic = self._calculate_geographic_complexity(entity_id, context)
        structural = self._calculate_structural_complexity(entity_id, context)
        technical = self._calculate_technical_complexity(entity_id, context)
        regulatory = self._calculate_regulatory_complexity(entity_id, context)
        
        # Get weights
        weights = self._get_weights()
        
        # Calculate composite
        components = {
            "geographic": geographic,
            "structural": structural,
            "technical": technical,
            "regulatory": regulatory,
        }
        
        composite = sum(
            components[k]["score"] * weights[k]
            for k in components
        )
        
        confidence = sum(
            components[k]["confidence"] * weights[k]
            for k in components
        ) / sum(weights.values())
        
        # Map to category
        category = self._map_to_category(composite)
        
        # Extract complexity factors
        factors = self._extract_factors(components)
        
        return ComplexityResult(
            score=round(composite, 2),
            category=category,
            confidence=round(confidence, 3),
            geographic_score=round(geographic["score"], 2),
            structural_score=round(structural["score"], 2),
            technical_score=round(technical["score"], 2),
            regulatory_score=round(regulatory["score"], 2),
            factors=tuple(factors),
            assessed_at=datetime.utcnow()
        )
    
    def _get_weights(self) -> Dict[str, float]:
        """Get component weights from config or defaults."""
        # Look for weights in complexity groups
        weights = self.DEFAULT_WEIGHTS.copy()
        
        for group in self._complexity_groups:
            component = group.name.replace("complexity_", "")
            if component in weights:
                weights[component] = group.weight
        
        return weights
    
    def _calculate_geographic_complexity(
        self,
        entity_id: str,
        context: InferenceContext
    ) -> Dict[str, float]:
        """Calculate geographic complexity component."""
        signals = [
            ("complexity_country_count", 0.6),
            ("complexity_regulatory_jurisdiction_count", 0.4),
        ]
        return self._calculate_component(entity_id, context, signals)
    
    def _calculate_structural_complexity(
        self,
        entity_id: str,
        context: InferenceContext
    ) -> Dict[str, float]:
        """Calculate structural complexity component."""
        signals = [
            ("complexity_subsidiary_count", 0.5),
            ("complexity_acquisition_frequency", 0.5),
        ]
        return self._calculate_component(entity_id, context, signals)
    
    def _calculate_technical_complexity(
        self,
        entity_id: str,
        context: InferenceContext
    ) -> Dict[str, float]:
        """Calculate technical complexity component."""
        signals = [
            ("complexity_technology_heterogeneity", 0.6),
            ("complexity_product_line_count", 0.4),
        ]
        return self._calculate_component(entity_id, context, signals)
    
    def _calculate_regulatory_complexity(
        self,
        entity_id: str,
        context: InferenceContext
    ) -> Dict[str, float]:
        """Calculate regulatory complexity component."""
        signals = [
            ("complexity_regulatory_jurisdiction_count", 0.6),
            ("complexity_supply_chain_depth", 0.4),
        ]
        return self._calculate_component(entity_id, context, signals)
    
    def _calculate_component(
        self,
        entity_id: str,
        context: InferenceContext,
        signals: List[Tuple[str, float]]
    ) -> Dict[str, float]:
        """Calculate a single complexity component."""
        weighted_sum = 0.0
        weight_sum = 0.0
        confidence_sum = 0.0
        
        for signal_id, weight in signals:
            try:
                inference_fn = get_inference_function(signal_id)
                result = inference_fn(entity_id, context)
                
                if result.confidence > 0:
                    weighted_sum += result.score * weight * result.confidence
                    weight_sum += weight * result.confidence
                    confidence_sum += result.confidence * weight
            except Exception:
                continue
        
        if weight_sum == 0:
            return {"score": 0.0, "confidence": 0.0}
        
        return {
            "score": weighted_sum / weight_sum,
            "confidence": confidence_sum / sum(w for _, w in signals)
        }
    
    def _map_to_category(self, score: float) -> ComplexityCategory:
        """Map complexity score to category."""
        if score < self._thresholds.get("moderate", 20):
            return ComplexityCategory.SIMPLE
        elif score < self._thresholds.get("complex", 40):
            return ComplexityCategory.MODERATE
        elif score < self._thresholds.get("highly_complex", 60):
            return ComplexityCategory.COMPLEX
        elif score < self._thresholds.get("extremely_complex", 80):
            return ComplexityCategory.HIGHLY_COMPLEX
        else:
            return ComplexityCategory.EXTREMELY_COMPLEX
    
    def _extract_factors(
        self,
        components: Dict[str, Dict[str, float]]
    ) -> List[str]:
        """Extract human-readable complexity factors."""
        factors = []
        
        if components["geographic"]["score"] > 60:
            factors.append("High geographic dispersion")
        if components["structural"]["score"] > 60:
            factors.append("Complex organizational structure")
        if components["technical"]["score"] > 60:
            factors.append("Heterogeneous technology environment")
        if components["regulatory"]["score"] > 60:
            factors.append("Multi-jurisdictional regulatory exposure")
        
        return factors
```

---

## 12. Phase 15.8: Band Mapping and Cohort Priors

### 12.1 Purpose

Implement score-to-band mapping with both fixed threshold and cohort quantile methods, plus cohort prior management.

### 12.2 File: `exposure/band_mapper.py`

```python
"""
Exposure Band Mapper

Maps exposure scores to categorical bands using either fixed thresholds
or cohort quantile methods.
"""

from typing import Dict, List, Optional, Tuple

from exposure.types import (
    ExposureBand,
    ExposureBandConfig,
    ExposureConfig,
)


class BandMapper:
    """
    Map exposure scores to categorical bands.
    
    Supports two methods:
    1. fixed_threshold: Compare score to configured thresholds
    2. cohort_quantile: Use cohort percentiles for mapping
    
    Usage:
        mapper = BandMapper(config)
        band = mapper.map_score_to_band(72.5)
        tiv_range = mapper.get_implied_tiv_range(band)
    """
    
    def __init__(self, config: ExposureConfig):
        """Initialize with exposure configuration."""
        self.config = config
        self.method = config.band_mapping_method
        self._bands = sorted(config.bands, key=lambda b: b.min_score)
    
    def map_score_to_band(
        self,
        score: float,
        cohort_id: Optional[str] = None
    ) -> ExposureBand:
        """
        Map exposure score to band.
        
        Args:
            score: Exposure score (0-100)
            cohort_id: Cohort ID for quantile method (optional)
        
        Returns:
            ExposureBand enum value
        """
        if self.method == "cohort_quantile" and cohort_id:
            return self._map_cohort_quantile(score, cohort_id)
        else:
            return self._map_fixed_threshold(score)
    
    def _map_fixed_threshold(self, score: float) -> ExposureBand:
        """Map using fixed score thresholds."""
        for band_config in self._bands:
            if band_config.min_score <= score < band_config.max_score:
                return ExposureBand(band_config.name)
        
        # Handle edge case: score exactly 100
        if score >= 100:
            return ExposureBand(self._bands[-1].name)
        
        # Default to first band
        return ExposureBand(self._bands[0].name)
    
    def _map_cohort_quantile(
        self,
        score: float,
        cohort_id: str
    ) -> ExposureBand:
        """
        Map using cohort percentile distribution.
        
        Requires CohortManager to provide percentile lookup.
        Falls back to fixed threshold if cohort not found.
        """
        # This would integrate with CohortManager
        # For now, fall back to fixed threshold
        return self._map_fixed_threshold(score)
    
    def get_implied_tiv_range(
        self,
        band: ExposureBand
    ) -> Optional[Tuple[float, float]]:
        """
        Get implied TIV range for a band.
        
        Returns: (low, high) in dollars, or None if not configured
        """
        for band_config in self._bands:
            if band_config.name == band.value:
                return (band_config.implied_tiv_low, band_config.implied_tiv_high)
        return None
    
    def get_implied_tiv_string(self, band: ExposureBand) -> str:
        """Get human-readable TIV range string."""
        for band_config in self._bands:
            if band_config.name == band.value:
                return band_config.implied_tiv_range
        return "Unknown"
    
    def get_band_config(self, band: ExposureBand) -> Optional[ExposureBandConfig]:
        """Get configuration for a specific band."""
        for band_config in self._bands:
            if band_config.name == band.value:
                return band_config
        return None
```

### 12.3 File: `exposure/cohort_manager.py`

```python
"""
Cohort Prior Manager

Manages historical cohort data for exposure calibration using the
cohort quantile mapping method.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
import math

from exposure.types import CohortPrior, ExposureBand


class CohortManager:
    """
    Manage cohort priors for exposure calibration.
    
    Cohorts are defined by:
    - Sector (industry classification)
    - Region (geographic area)
    - Digital footprint band (size proxy)
    
    Each cohort stores:
    - Historical TIV distribution
    - Historical exposure score distribution
    - Mapping from score percentile to implied TIV
    
    Usage:
        manager = CohortManager()
        prior = manager.get_prior("technology", "north_america", "medium")
        tiv_range = manager.calculate_implied_tiv(72.5, prior)
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize cohort manager.
        
        Args:
            storage_path: Path to cohort prior storage (database or file)
        """
        self.storage_path = storage_path
        self._cohorts: Dict[str, CohortPrior] = {}
        self._load_cohorts()
    
    def _load_cohorts(self) -> None:
        """Load cohort priors from storage."""
        # In production, load from database
        # For now, initialize with empty dict
        pass
    
    def get_prior(
        self,
        sector: str,
        region: str,
        digital_footprint_band: str
    ) -> Optional[CohortPrior]:
        """
        Get cohort prior matching criteria.
        
        Args:
            sector: Industry sector
            region: Geographic region
            digital_footprint_band: Size band from digital signals
        
        Returns:
            CohortPrior if found, None otherwise
        """
        cohort_id = self._make_cohort_id(sector, region, digital_footprint_band)
        return self._cohorts.get(cohort_id)
    
    def _make_cohort_id(
        self,
        sector: str,
        region: str,
        digital_footprint_band: str
    ) -> str:
        """Generate cohort ID from dimensions."""
        return f"{sector}_{region}_{digital_footprint_band}".lower()
    
    def add_observation(
        self,
        sector: str,
        region: str,
        digital_footprint_band: str,
        exposure_score: float,
        actual_tiv: float
    ) -> None:
        """
        Add an observation to a cohort.
        
        Call this when actual TIV becomes known (e.g., after policy binding).
        
        Args:
            sector: Industry sector
            region: Geographic region
            digital_footprint_band: Size band
            exposure_score: Calculated exposure score
            actual_tiv: Verified actual TIV
        """
        cohort_id = self._make_cohort_id(sector, region, digital_footprint_band)
        
        if cohort_id not in self._cohorts:
            self._cohorts[cohort_id] = CohortPrior(
                cohort_id=cohort_id,
                sector=sector,
                region=region,
                digital_footprint_band=digital_footprint_band
            )
        
        cohort = self._cohorts[cohort_id]
        cohort.tiv_distribution.append(actual_tiv)
        cohort.exposure_score_distribution.append(exposure_score)
        cohort.sample_size += 1
        cohort.last_updated = datetime.utcnow()
        cohort.update_confidence()
    
    def calculate_implied_tiv(
        self,
        exposure_score: float,
        cohort: CohortPrior
    ) -> Tuple[float, float]:
        """
        Calculate implied TIV range from exposure score using cohort.
        
        Args:
            exposure_score: Calculated exposure score (0-100)
            cohort: Cohort prior to use
        
        Returns:
            (low_estimate, high_estimate) in dollars
        """
        if cohort.sample_size < 10:
            # Insufficient data for reliable estimate
            return (0.0, float('inf'))
        
        # Find percentile of score within cohort
        score_percentile = self._calculate_percentile(
            exposure_score,
            cohort.exposure_score_distribution
        )
        
        # Map to TIV percentile range (with uncertainty)
        low_percentile = max(0, score_percentile - 0.10)
        high_percentile = min(1, score_percentile + 0.10)
        
        sorted_tivs = sorted(cohort.tiv_distribution)
        low_idx = int(low_percentile * len(sorted_tivs))
        high_idx = min(int(high_percentile * len(sorted_tivs)), len(sorted_tivs) - 1)
        
        return (sorted_tivs[low_idx], sorted_tivs[high_idx])
    
    def _calculate_percentile(
        self,
        value: float,
        distribution: List[float]
    ) -> float:
        """Calculate percentile rank of value in distribution."""
        if not distribution:
            return 0.5
        
        count_below = sum(1 for v in distribution if v <= value)
        return count_below / len(distribution)
    
    def get_cohort_percentile(
        self,
        exposure_score: float,
        cohort: CohortPrior
    ) -> float:
        """Get entity's percentile within cohort."""
        return self._calculate_percentile(
            exposure_score,
            cohort.exposure_score_distribution
        )
    
    def save_cohorts(self) -> None:
        """Persist cohort priors to storage."""
        # In production, save to database
        pass
```

---

## 13. Phase 15.9: YAML Configuration Schema

### 13.1 Purpose

Define the complete YAML schema for exposure configuration and provide example configurations for each coverage.

### 13.2 Schema Definition

```yaml
# EXPOSURE CONFIGURATION SCHEMA
# This schema extends the coverage config.yaml files

exposure:
  # Master enable/disable
  enabled: boolean  # Default: true
  
  # Configuration version for tracking changes
  version: string  # Format: "YYYY-MM-DD"
  
  # Exposure magnitude signal groups
  signal_groups:
    - name: string  # Group identifier (e.g., "exposure_digital_footprint")
      signal_type: "exposure"  # Must be "exposure" for magnitude signals
      weight: float  # Weight in composite (0-1), all groups must sum to 1.0
      confidence_threshold: float  # Minimum confidence for group to contribute (0-1)
      priority: integer  # Lower = higher priority for tier selection (default: 99)
      features:
        - id: string  # Signal identifier (must match inference function)
          weight: float  # Weight within group (0-1), features must sum to 1.0
          normalizer: string  # Type: log_scale, linear, capped, percentile, categorical
          normalizer_params:  # Parameters vary by normalizer type
            # For log_scale:
            base: float  # Logarithm base (default: 10)
            scale: float  # Multiplier for normalized value
            # For linear:
            min: float  # Minimum input value (maps to 0)
            max: float  # Maximum input value (maps to 100)
            # For capped:
            cap: float  # Values above cap all map to 100
            # For percentile:
            distribution: string  # Reference distribution identifier
            # For categorical:
            mapping: object  # Value -> score mapping
          proxy_tier: integer  # 1=direct, 2=inferred, 3=cohort, 4=unknown
          conditions:  # Optional signal-level conditions
            - condition_type: string
              condition_value: any
              action: string
              action_value: any
  
  # Complexity signal groups
  complexity_groups:
    - name: string  # Group identifier (e.g., "complexity_geographic")
      signal_type: "complexity"  # Must be "complexity"
      weight: float  # Weight in composite
      features:
        # Same structure as exposure features
  
  # Band mapping configuration
  exposure_band_mapping:
    method: string  # "fixed_threshold" or "cohort_quantile"
    bands:
      - name: string  # Band name (micro, small, medium, large, very_large)
        min_score: float  # Minimum score for band (inclusive)
        max_score: float  # Maximum score for band (exclusive, except last)
        implied_tiv_range: string  # Human-readable range (e.g., "$10M - $50M")
        implied_tiv_low: float  # Low end in dollars
        implied_tiv_high: float  # High end in dollars
  
  # Complexity category thresholds
  complexity_thresholds:
    moderate: float  # Score threshold for MODERATE (default: 20)
    complex: float  # Score threshold for COMPLEX (default: 40)
    highly_complex: float  # Score threshold for HIGHLY_COMPLEX (default: 60)
    extremely_complex: float  # Score threshold for EXTREMELY_COMPLEX (default: 80)
  
  # Auto-apply rules
  auto_apply_rules:
    - id: string  # Rule identifier
      condition: string  # Python expression evaluated with context
      action: string  # refer, tier_floor, tier_ceiling, modifier, note, decline
      value: any  # Action-specific value
      reason: string  # Human-readable reason

# Pricing integration
pricing:
  exposure_integration: string  # "parallel", "embedded", or "grid"
  
  # For parallel integration
  exposure_modifiers:
    micro: float  # Modifier for micro band (e.g., 0.80 = 20% credit)
    small: float
    medium: float  # Typically 1.0 (base)
    large: float
    very_large: float
  
  complexity_modifiers:
    simple: float
    moderate: float  # Typically 1.0 (base)
    complex: float
    highly_complex: float
    extremely_complex: float
  
  # For grid integration
  pricing_grid:
    tier1:
      micro:
        simple: float  # Rate
        moderate: float
        complex: float
        highly_complex: float
        extremely_complex: float
      small:
        # ...
      # ...
    tier2:
      # ...
    # ...
```

### 13.3 Example: Cyber Coverage Exposure Configuration

```yaml
# coverages/cyber/config.yaml (exposure section)

exposure:
  enabled: true
  version: "2025-01-01"
  
  signal_groups:
    # Digital footprint is highly relevant for cyber
    - name: exposure_digital_footprint
      signal_type: exposure
      weight: 0.40
      confidence_threshold: 0.5
      priority: 2
      features:
        - id: domain_count
          weight: 0.20
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 25
          proxy_tier: 2
        - id: subdomain_complexity
          weight: 0.25
          normalizer: capped
          normalizer_params:
            cap: 500
          proxy_tier: 2
        - id: tech_stack_count
          weight: 0.35
          normalizer: capped
          normalizer_params:
            cap: 50
          proxy_tier: 2
        - id: web_reach_proxy
          weight: 0.20
          normalizer: percentile
          proxy_tier: 2
    
    # Network authority
    - name: exposure_network_authority
      signal_type: exposure
      weight: 0.25
      confidence_threshold: 0.5
      priority: 2
      features:
        - id: marquee_partner_count
          weight: 0.40
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 30
          proxy_tier: 2
        - id: systemic_link_score
          weight: 0.35
          normalizer: linear
          normalizer_params:
            min: 0
            max: 100
          proxy_tier: 2
        - id: regulatory_citation_count
          weight: 0.25
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 25
          proxy_tier: 2
    
    # Direct scale proxies (Tier 1 when available)
    - name: exposure_scale_direct
      signal_type: exposure
      weight: 0.25
      confidence_threshold: 0.7
      priority: 1  # High priority - use if available
      features:
        - id: public_revenue
          weight: 0.40
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 8.33  # $10B = 100
          proxy_tier: 1
        - id: public_assets
          weight: 0.30
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 8.33
          proxy_tier: 1
        - id: registered_employee_count
          weight: 0.30
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 16.67  # 1M employees = 100
          proxy_tier: 1
    
    # Geographic presence
    - name: exposure_geographic
      signal_type: exposure
      weight: 0.10
      confidence_threshold: 0.5
      priority: 2
      features:
        - id: location_count
          weight: 0.60
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 30
          proxy_tier: 2
        - id: high_intensity_location_pct
          weight: 0.40
          normalizer: linear
          normalizer_params:
            min: 0
            max: 100
          proxy_tier: 2
  
  complexity_groups:
    - name: complexity_geographic
      signal_type: complexity
      weight: 0.30
      features:
        - id: country_count
          weight: 0.60
          normalizer: threshold_bucket
          normalizer_params:
            thresholds: [2, 5, 15, 50]
        - id: regulatory_jurisdiction_count
          weight: 0.40
          normalizer: threshold_bucket
          normalizer_params:
            thresholds: [2, 4, 8, 15]
    
    - name: complexity_structural
      signal_type: complexity
      weight: 0.25
      features:
        - id: subsidiary_count
          weight: 0.50
          normalizer: threshold_bucket
          normalizer_params:
            thresholds: [2, 5, 15, 50]
        - id: acquisition_frequency
          weight: 0.50
          normalizer: threshold_bucket
          normalizer_params:
            thresholds: [0.5, 1, 2, 5]
    
    - name: complexity_technical
      signal_type: complexity
      weight: 0.30
      features:
        - id: technology_heterogeneity
          weight: 0.60
          normalizer: linear
          normalizer_params:
            min: 0
            max: 100
        - id: product_line_count
          weight: 0.40
          normalizer: threshold_bucket
          normalizer_params:
            thresholds: [2, 5, 10, 25]
    
    - name: complexity_operational
      signal_type: complexity
      weight: 0.15
      features:
        - id: supply_chain_depth
          weight: 0.50
          normalizer: threshold_bucket
          normalizer_params:
            thresholds: [2, 3, 5, 8]
        - id: customer_concentration
          weight: 0.50
          normalizer: inverted_linear
          normalizer_params:
            min: 0
            max: 100
  
  exposure_band_mapping:
    method: fixed_threshold
    bands:
      - name: micro
        min_score: 0
        max_score: 15
        implied_tiv_range: "$0 - $1M"
        implied_tiv_low: 0
        implied_tiv_high: 1000000
      - name: small
        min_score: 15
        max_score: 35
        implied_tiv_range: "$1M - $10M"
        implied_tiv_low: 1000000
        implied_tiv_high: 10000000
      - name: medium
        min_score: 35
        max_score: 60
        implied_tiv_range: "$10M - $50M"
        implied_tiv_low: 10000000
        implied_tiv_high: 50000000
      - name: large
        min_score: 60
        max_score: 85
        implied_tiv_range: "$50M - $250M"
        implied_tiv_low: 50000000
        implied_tiv_high: 250000000
      - name: very_large
        min_score: 85
        max_score: 100
        implied_tiv_range: "$250M+"
        implied_tiv_low: 250000000
        implied_tiv_high: 10000000000
  
  complexity_thresholds:
    moderate: 20
    complex: 40
    highly_complex: 60
    extremely_complex: 80
  
  auto_apply_rules:
    - id: high_exposure_low_confidence
      condition: "exposure_band in ['large', 'very_large'] and exposure_confidence < 0.6"
      action: refer
      reason: "High inferred exposure with low confidence requires verification"
    
    - id: unknown_proxy_tier
      condition: "proxy_tier == 'unknown'"
      action: refer
      reason: "Insufficient data for exposure estimation"
    
    - id: extreme_complexity
      condition: "complexity_category == 'extremely_complex'"
      action: refer
      reason: "Extremely complex exposure structure requires specialist review"
    
    - id: very_large_tier_floor
      condition: "exposure_band == 'very_large' and tier < 3"
      action: tier_floor
      value: 3
      reason: "Minimum tier for very large exposures"

pricing:
  exposure_integration: parallel
  
  exposure_modifiers:
    micro: 0.80
    small: 0.90
    medium: 1.00
    large: 1.15
    very_large: 1.35
  
  complexity_modifiers:
    simple: 0.95
    moderate: 1.00
    complex: 1.10
    highly_complex: 1.25
    extremely_complex: 1.50
```

### 13.4 Coverage-Specific Weight Variations

| Signal Group | Cyber | Marine | FI | Energy | Aerospace | D&O | PI |
|--------------|-------|--------|-----|--------|-----------|-----|-----|
| digital_footprint | 0.40 | 0.15 | 0.25 | 0.20 | 0.20 | 0.30 | 0.35 |
| network_authority | 0.25 | 0.20 | 0.35 | 0.25 | 0.25 | 0.30 | 0.25 |
| scale_direct | 0.25 | 0.15 | 0.30 | 0.25 | 0.30 | 0.30 | 0.25 |
| geographic | 0.10 | 0.20 | 0.10 | 0.30 | 0.25 | 0.10 | 0.15 |
| fleet_scale | - | 0.30 | - | - | - | - | - |

---

## 14. Phase 15.10: Workflow Integration

### 14.1 Purpose

Integrate exposure scoring into the existing 14-step DSI workflow, adding steps 5b, 5c, 9b, and 9c.

### 14.2 Modifications to `model/workflow.py`

```python
# Add to imports
from exposure import (
    ExposureScorer,
    ComplexityScorer,
    BandMapper,
    CohortManager,
    ExposureRulesEngine,
    CombinedExposureAssessment,
)
from exposure.types import ExposureConfig

# Modify WorkflowEngine.__init__
class WorkflowEngine:
    def __init__(
        self,
        config_manager: ConfigManager,
        data_manager: ModelDataManager,
        scorer: ModelScorer,
        query_evaluator: QueryEvaluator,
        pricer: ModelPricer,
        discovery_engine: WebsiteDiscoveryEngine = None,
        # NEW: Exposure components
        exposure_scorer: ExposureScorer = None,
        complexity_scorer: ComplexityScorer = None,
        exposure_rules_engine: ExposureRulesEngine = None,
    ):
        self.config_manager = config_manager
        self.data_manager = data_manager
        self.scorer = scorer
        self.query_evaluator = query_evaluator
        self.pricer = pricer
        self.discovery_engine = discovery_engine or WebsiteDiscoveryEngine()
        
        # Exposure components (initialized per-coverage later)
        self._exposure_scorer = exposure_scorer
        self._complexity_scorer = complexity_scorer
        self._exposure_rules_engine = exposure_rules_engine

    def run_workflow(
        self,
        entity_name: str,
        coverage: str,
        submission_data: dict,
        direct_query_responses: dict[str, bool],
        categorical_selections: dict[str, str],
        user: str,
        domain_hint: str = None,
        country_hint: str = None,
        skip_discovery: bool = False,
    ) -> WorkflowResult:
        """
        Execute complete workflow including exposure assessment.
        
        Extended Steps:
        - Step 5a: Risk composite score calculation
        - Step 5b: Exposure magnitude score calculation (NEW)
        - Step 5c: Exposure complexity score calculation (NEW)
        - Step 9b: Final exposure band capture (NEW)
        - Step 9c: Final complexity category capture (NEW)
        """
        # Step 0: Discovery
        if not skip_discovery:
            discovery = self.discovery_engine.discover(
                entity_name,
                domain_hint=domain_hint,
                country_hint=country_hint
            )
            entity_id = discovery.primary_website.domain
            submission_data["discovered_website"] = discovery.primary_website.url
            submission_data["discovery_confidence"] = discovery.confidence
        else:
            entity_id = domain_hint or entity_name
        
        # Step 1: Load config
        config = self.config_manager.get_active_config(coverage)
        
        # Initialize exposure components for this coverage
        exposure_config = self._parse_exposure_config(config)
        if exposure_config and exposure_config.enabled:
            self._init_exposure_components(exposure_config)
        
        # Step 2: Create model data file
        model_id = self.data_manager.create_model(entity_id, config)
        
        # Step 3: Verify minimum viable inputs
        valid, missing = self.verify_inputs(submission_data, config)
        if not valid:
            return self._missing_inputs_result(model_id, missing)
        
        # Build inference context
        context = self._build_context(config, submission_data)
        
        # Step 4: Signal extraction (risk signals)
        # Step 5a: Risk composite score calculation
        scoring_result = self.scorer.score_entity(entity_id, config)
        
        # Step 5b: Exposure magnitude score calculation (NEW)
        exposure_result = None
        if self._exposure_scorer:
            exposure_result = self._exposure_scorer.score(entity_id, context)
        
        # Step 5c: Exposure complexity score calculation (NEW)
        complexity_result = None
        if self._complexity_scorer:
            complexity_result = self._complexity_scorer.score(entity_id, context)
        
        # Step 6: Signal conditions evaluation (risk signals)
        # Step 7: Direct query response evaluation
        query_result = self.query_evaluator.evaluate_queries(
            direct_query_responses, config
        )
        
        # Evaluate exposure rules (NEW)
        exposure_rules_result = None
        if self._exposure_rules_engine and exposure_result:
            exposure_rules_result = self._exposure_rules_engine.evaluate(
                exposure_result=exposure_result,
                complexity_result=complexity_result,
                tier=self._score_to_tier(scoring_result.pure_composite_score, config),
                config=exposure_config
            )
        
        # Step 8: Maximum tier override application
        all_tier_overrides = (
            scoring_result.tier_overrides_from_signals +
            query_result.tier_overrides
        )
        
        # Add exposure tier overrides
        if exposure_rules_result:
            if exposure_rules_result.tier_floor:
                all_tier_overrides.append(exposure_rules_result.tier_floor)
        
        # Step 9: Final tier capture
        score_tier = self._score_to_tier(scoring_result.pure_composite_score, config)
        final_tier = self._apply_tier_overrides(score_tier, all_tier_overrides)
        
        # Step 9b: Final exposure band capture (NEW)
        final_exposure_band = exposure_result.band if exposure_result else None
        
        # Step 9c: Final complexity category capture (NEW)
        final_complexity_category = complexity_result.category if complexity_result else None
        
        # Combine exposure assessment
        combined_exposure = None
        if exposure_result and complexity_result:
            combined_exposure = self._combine_exposure_assessment(
                exposure_result,
                complexity_result,
                exposure_rules_result,
                exposure_config
            )
        
        # Step 10: Base premium generation
        # Step 11: Modifier application
        # Step 12: Limit band scaling
        pricing_result = self.pricer.price_submission(
            pure_composite_score=scoring_result.pure_composite_score,
            signal_tier_overrides=scoring_result.tier_overrides_from_signals,
            query_tier_overrides=query_result.tier_overrides,
            query_modifiers=query_result.modifiers,
            categorical_selections=categorical_selections,
            submission_data=submission_data,
            config=config,
            # NEW: Exposure pricing inputs
            exposure_assessment=combined_exposure,
        )
        
        # Step 13: Output decision
        # Combine referral reasons
        all_referral_reasons = (
            list(scoring_result.referrals_from_signals) +
            list(query_result.referrals)
        )
        if exposure_rules_result and exposure_rules_result.referral_required:
            all_referral_reasons.extend(exposure_rules_result.referral_reasons)
        
        decision, auto_approve = self.determine_decision(
            final_tier, all_referral_reasons, config
        )
        
        # Create model version with exposure data
        model_version = self._create_model_version(
            model_id=model_id,
            entity_id=entity_id,
            config=config,
            scoring_result=scoring_result,
            query_result=query_result,
            pricing_result=pricing_result,
            exposure_result=exposure_result,
            complexity_result=complexity_result,
            combined_exposure=combined_exposure,
            final_tier=final_tier,
            decision=decision,
            auto_approve=auto_approve,
            referral_reasons=all_referral_reasons,
            user=user,
        )
        
        return WorkflowResult(
            model_version=model_version,
            decision=decision,
            auto_approve=auto_approve,
            referral_reasons=tuple(all_referral_reasons),
            notes=tuple(query_result.notes),
            premium_options=pricing_result.limit_premiums,
            recommended_limit=self._get_recommended_limit(pricing_result),
            recommended_premium=self._get_recommended_premium(pricing_result),
            # NEW: Exposure outputs
            exposure_assessment=combined_exposure,
        )
    
    def _init_exposure_components(self, exposure_config: ExposureConfig) -> None:
        """Initialize exposure scoring components for the coverage."""
        band_mapper = BandMapper(exposure_config)
        cohort_manager = CohortManager()
        
        self._exposure_scorer = ExposureScorer(exposure_config, band_mapper)
        self._complexity_scorer = ComplexityScorer(exposure_config)
        self._exposure_rules_engine = ExposureRulesEngine(exposure_config)
    
    def _parse_exposure_config(self, config: CoverageConfig) -> Optional[ExposureConfig]:
        """Parse exposure configuration from coverage config."""
        # Implementation: parse YAML exposure section into ExposureConfig
        pass
    
    def _combine_exposure_assessment(
        self,
        exposure_result: ExposureResult,
        complexity_result: ComplexityResult,
        rules_result: Optional[RulesEvaluationResult],
        config: ExposureConfig
    ) -> CombinedExposureAssessment:
        """Combine magnitude and complexity into final assessment."""
        # Calculate combined modifier
        exposure_modifier = config.exposure_modifiers.get(
            exposure_result.band.value, 1.0
        )
        complexity_modifier = config.complexity_modifiers.get(
            complexity_result.category.value, 1.0
        )
        combined_modifier = exposure_modifier * complexity_modifier
        
        # Determine referral
        referral_required = False
        referral_reasons = []
        if rules_result:
            referral_required = rules_result.referral_required
            referral_reasons = list(rules_result.referral_reasons)
        
        # Create pricing band string
        pricing_band = f"{exposure_result.band.value}_{complexity_result.category.value}"
        
        return CombinedExposureAssessment(
            magnitude=exposure_result,
            complexity=complexity_result,
            pricing_band=pricing_band,
            premium_modifier=combined_modifier,
            referral_required=referral_required,
            referral_reasons=tuple(referral_reasons),
            notes=tuple(rules_result.notes if rules_result else [])
        )
```

---

## 15. Phase 15.11: Pricing Integration

### 15.1 Purpose

Extend the pricer to support three pricing integration patterns: parallel, embedded, and grid.

### 15.2 Modifications to `model/pricer.py`

```python
# Add to existing ModelPricer class

def price_submission(
    self,
    pure_composite_score: float,
    signal_tier_overrides: list[int],
    query_tier_overrides: list[int],
    query_modifiers: list[dict],
    categorical_selections: dict[str, str],
    submission_data: dict,
    config: CoverageConfig,
    # NEW: Exposure inputs
    exposure_assessment: Optional[CombinedExposureAssessment] = None,
) -> PricingResult:
    """
    Execute Steps 8-12 with exposure integration.
    """
    # Step 8: Tier override resolution
    score_tier = self._score_to_tier(pure_composite_score, config)
    final_tier = self.resolve_tier_overrides(
        score_tier,
        signal_tier_overrides + query_tier_overrides
    )
    
    # Step 10: Base premium generation
    base_premium, method = self.calculate_base_premium(
        tier=final_tier,
        submission_data=submission_data,
        config=config,
        exposure_assessment=exposure_assessment,  # NEW
    )
    
    # Step 11: Modifier application
    premium_after_modifiers, modifiers_applied = self.apply_modifiers(
        base_premium=base_premium,
        categorical_selections=categorical_selections,
        query_modifiers=query_modifiers,
        config=config,
        exposure_assessment=exposure_assessment,  # NEW
    )
    
    # Step 12: Limit band scaling
    limit_premiums = self.scale_to_limits(premium_after_modifiers, config)
    
    return PricingResult(
        tier_overrides_considered=signal_tier_overrides + query_tier_overrides,
        max_tier_override=max(signal_tier_overrides + query_tier_overrides) if signal_tier_overrides + query_tier_overrides else None,
        score_based_tier=score_tier,
        final_tier=final_tier,
        base_premium=base_premium,
        base_premium_method=method,
        modifiers_applied=modifiers_applied,
        premium_after_modifiers=premium_after_modifiers,
        limit_premiums=limit_premiums,
    )

def calculate_base_premium(
    self,
    tier: int,
    submission_data: dict,
    config: CoverageConfig,
    exposure_assessment: Optional[CombinedExposureAssessment] = None,
) -> Tuple[float, str]:
    """
    Calculate base premium using configured method.
    
    Methods:
    - Pure premium: Fixed amount per tier
    - Rate-based: Rate × exposure basis
    - Grid: Tier × Exposure Band × Complexity lookup
    """
    pricing_config = config.pricing
    integration = pricing_config.get("exposure_integration", "parallel")
    
    if integration == "grid" and exposure_assessment:
        return self._calculate_grid_premium(
            tier, exposure_assessment, submission_data, config
        )
    else:
        return self._calculate_tier_premium(tier, submission_data, config)

def _calculate_grid_premium(
    self,
    tier: int,
    exposure_assessment: CombinedExposureAssessment,
    submission_data: dict,
    config: CoverageConfig,
) -> Tuple[float, str]:
    """
    Calculate premium using three-dimensional grid.
    
    Grid: tier × exposure_band × complexity_category → rate
    """
    grid = config.pricing.get("pricing_grid", {})
    tier_key = f"tier{tier}"
    band = exposure_assessment.magnitude.band.value
    complexity = exposure_assessment.complexity.category.value
    
    try:
        rate = grid[tier_key][band][complexity]
    except KeyError:
        # Fall back to tier-only pricing
        return self._calculate_tier_premium(tier, submission_data, config)
    
    # Apply rate to exposure basis
    basis = self._get_rate_basis(submission_data, config)
    premium = rate * basis
    
    return (premium, "grid_3d")

def apply_modifiers(
    self,
    base_premium: float,
    categorical_selections: dict[str, str],
    query_modifiers: list[dict],
    config: CoverageConfig,
    exposure_assessment: Optional[CombinedExposureAssessment] = None,
) -> Tuple[float, list[dict]]:
    """
    Apply all modifiers including exposure modifiers.
    """
    premium = base_premium
    modifiers_applied = []
    
    # Apply categorical modifiers
    for group, category in categorical_selections.items():
        modifier = config.categorical_features.get(group, {}).get(category, 1.0)
        if modifier != 1.0:
            modifiers_applied.append({
                "name": f"categorical_{group}",
                "factor": modifier,
                "premium_before": premium,
                "premium_after": premium * modifier,
            })
            premium *= modifier
    
    # Apply query modifiers
    for mod in query_modifiers:
        factor = mod.get("factor", 1.0)
        modifiers_applied.append({
            "name": mod.get("name", "query_modifier"),
            "factor": factor,
            "premium_before": premium,
            "premium_after": premium * factor,
        })
        premium *= factor
    
    # Apply exposure modifiers (for parallel integration only)
    pricing_config = config.pricing
    if pricing_config.get("exposure_integration") == "parallel" and exposure_assessment:
        # Exposure modifier
        exposure_modifier = exposure_assessment.premium_modifier
        if exposure_modifier != 1.0:
            modifiers_applied.append({
                "name": "exposure_combined",
                "factor": exposure_modifier,
                "premium_before": premium,
                "premium_after": premium * exposure_modifier,
                "components": {
                    "exposure_band": exposure_assessment.magnitude.band.value,
                    "complexity_category": exposure_assessment.complexity.category.value,
                }
            })
            premium *= exposure_modifier
    
    return (premium, modifiers_applied)
```

---

## 16. Phase 15.12: Auto-Apply Rules Engine

### 16.1 Purpose

Implement the rules engine that evaluates exposure-based auto-apply rules.

### 16.2 File: `exposure/rules_engine.py`

```python
"""
Exposure Rules Engine

Evaluates auto-apply rules based on exposure assessment results.
"""

from typing import Any, Dict, List, Optional
import re

from exposure.types import (
    ComplexityCategory,
    ComplexityResult,
    ExposureBand,
    ExposureConfig,
    ExposureResult,
    ExposureRuleAction,
    ExposureRuleConfig,
    ProxyTier,
    RuleOutcome,
    RulesEvaluationResult,
)


class ExposureRulesEngine:
    """
    Evaluate exposure auto-apply rules.
    
    Rules are defined in YAML and evaluated against exposure results.
    Supports Python-like condition expressions.
    
    Usage:
        engine = ExposureRulesEngine(config)
        result = engine.evaluate(exposure_result, complexity_result, tier, config)
    """
    
    def __init__(self, config: ExposureConfig):
        """Initialize with exposure configuration."""
        self.config = config
        self._rules = config.auto_apply_rules
    
    def evaluate(
        self,
        exposure_result: ExposureResult,
        complexity_result: Optional[ComplexityResult],
        tier: int,
        config: ExposureConfig
    ) -> RulesEvaluationResult:
        """
        Evaluate all rules against exposure results.
        
        Args:
            exposure_result: Exposure magnitude result
            complexity_result: Complexity result (optional)
            tier: Current risk tier
            config: Exposure configuration
        
        Returns:
            RulesEvaluationResult with all triggered outcomes
        """
        # Build evaluation context
        context = self._build_context(exposure_result, complexity_result, tier)
        
        # Evaluate each rule
        outcomes: List[RuleOutcome] = []
        for rule in self._rules:
            if self._evaluate_condition(rule.condition, context):
                outcomes.append(RuleOutcome(
                    rule_id=rule.id,
                    action=rule.action,
                    value=rule.value,
                    reason=rule.reason
                ))
        
        # Aggregate outcomes
        return self._aggregate_outcomes(outcomes)
    
    def _build_context(
        self,
        exposure_result: ExposureResult,
        complexity_result: Optional[ComplexityResult],
        tier: int
    ) -> Dict[str, Any]:
        """Build evaluation context from results."""
        context = {
            # Exposure magnitude
            "exposure_score": exposure_result.score,
            "exposure_band": exposure_result.band.value,
            "exposure_confidence": exposure_result.confidence,
            "proxy_tier": exposure_result.proxy_tier.value,
            "range_low": exposure_result.range_low,
            "range_high": exposure_result.range_high,
            
            # Cohort
            "cohort_percentile": exposure_result.cohort_percentile,
            
            # Risk tier
            "tier": tier,
        }
        
        # Complexity (if available)
        if complexity_result:
            context.update({
                "complexity_score": complexity_result.score,
                "complexity_category": complexity_result.category.value,
                "complexity_confidence": complexity_result.confidence,
                "geographic_complexity": complexity_result.geographic_score,
                "structural_complexity": complexity_result.structural_score,
                "technical_complexity": complexity_result.technical_score,
                "regulatory_complexity": complexity_result.regulatory_score,
            })
        
        return context
    
    def _evaluate_condition(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a condition expression.
        
        Supports Python-like expressions:
        - Comparisons: ==, !=, <, >, <=, >=
        - Logical: and, or, not
        - Membership: in, not in
        - Literals: strings, numbers, lists
        
        Example conditions:
        - "exposure_band in ['large', 'very_large'] and exposure_confidence < 0.6"
        - "proxy_tier == 'unknown'"
        - "complexity_category == 'extremely_complex'"
        """
        try:
            # Use restricted eval with only context variables
            # In production, use a proper expression parser for safety
            result = eval(condition, {"__builtins__": {}}, context)
            return bool(result)
        except Exception:
            # If evaluation fails, rule doesn't trigger
            return False
    
    def _aggregate_outcomes(
        self,
        outcomes: List[RuleOutcome]
    ) -> RulesEvaluationResult:
        """Aggregate individual outcomes into combined result."""
        tier_floors: List[int] = []
        tier_ceilings: List[int] = []
        modifiers: List[Dict[str, Any]] = []
        referral_reasons: List[str] = []
        notes: List[str] = []
        decline_reason: Optional[str] = None
        
        for outcome in outcomes:
            if outcome.action == ExposureRuleAction.TIER_FLOOR:
                tier_floors.append(outcome.value)
            elif outcome.action == ExposureRuleAction.TIER_CEILING:
                tier_ceilings.append(outcome.value)
            elif outcome.action == ExposureRuleAction.MODIFIER:
                modifiers.append({
                    "name": outcome.rule_id,
                    "factor": outcome.value,
                    "reason": outcome.reason
                })
            elif outcome.action == ExposureRuleAction.REFER:
                referral_reasons.append(outcome.reason)
            elif outcome.action == ExposureRuleAction.NOTE:
                notes.append(outcome.reason)
            elif outcome.action == ExposureRuleAction.DECLINE:
                decline_reason = outcome.reason
        
        return RulesEvaluationResult(
            outcomes=tuple(outcomes),
            tier_floor=max(tier_floors) if tier_floors else None,
            tier_ceiling=min(tier_ceilings) if tier_ceilings else None,
            modifiers=tuple(modifiers),
            referral_required=len(referral_reasons) > 0,
            referral_reasons=tuple(referral_reasons),
            notes=tuple(notes),
            decline_required=decline_reason is not None,
            decline_reason=decline_reason,
        )
```

---

## 17. Phase 15.13: Model Version Extensions

### 17.1 Purpose

Extend ModelVersion to store exposure assessment data for audit trail.

### 17.2 Modifications to `model/types.py`

```python
# Add to existing ModelVersion dataclass

@dataclass
class ModelVersion:
    """A complete model execution snapshot."""
    
    # Existing fields...
    version_id: str
    model_id: str
    version_number: int
    version_type: str
    entity_id: str
    submission_data: dict
    direct_query_responses: dict[str, bool]
    categorical_selections: dict[str, str]
    signal_outputs: list[SignalOutput]
    group_scores: dict[str, float]
    pure_composite_score: float
    signal_conditions: list[dict]
    query_conditions: list[dict]
    tier_overrides: list[int]
    final_tier: int
    base_premium: float
    modifiers_applied: list[dict]
    limit_premiums: dict[float, float]
    final_premium: float
    decision: str
    auto_approve: bool
    referral_reasons: list[str]
    notes: list[str]
    config_hash: str
    created_at: datetime
    created_by: str
    
    # NEW: Exposure fields
    exposure_score: Optional[float] = None
    exposure_score_range: Optional[Tuple[float, float]] = None
    exposure_band: Optional[str] = None
    exposure_confidence: Optional[float] = None
    exposure_proxy_tier: Optional[str] = None
    exposure_group_scores: Optional[Dict[str, float]] = None
    exposure_group_confidences: Optional[Dict[str, float]] = None
    exposure_cohort_id: Optional[str] = None
    exposure_cohort_percentile: Optional[float] = None
    exposure_implied_tiv_range: Optional[Tuple[float, float]] = None
    
    complexity_score: Optional[float] = None
    complexity_category: Optional[str] = None
    complexity_confidence: Optional[float] = None
    complexity_components: Optional[Dict[str, float]] = None
    
    exposure_modifiers_applied: Optional[List[Dict[str, Any]]] = None
    exposure_rules_triggered: Optional[List[str]] = None
    pricing_method: Optional[str] = None  # 'parallel', 'embedded', 'grid'
```

---

## 18-21: Remaining Phases

Due to length constraints, the remaining phases are summarized:

### Phase 15.14: Testing Framework
- Unit tests for all new modules
- Integration tests for workflow
- Validation tests against known TIVs
- Performance benchmarks

### Phase 15.15: Monitoring and Calibration
- Signal availability metrics
- Confidence distribution tracking
- Calibration drift detection
- Cohort stability monitoring

### Cross-Cutting Concerns
- Error handling patterns
- Logging standards
- Performance optimization
- Documentation requirements

### Integration Checklist
- [ ] All types defined in `exposure/types.py`
- [ ] All extractors implemented and registered
- [ ] All aggregators implemented
- [ ] All inference functions registered
- [ ] ExposureScorer complete
- [ ] ComplexityScorer complete
- [ ] BandMapper complete
- [ ] CohortManager complete
- [ ] RulesEngine complete
- [ ] Workflow integration complete
- [ ] Pricer integration complete
- [ ] All YAML configs updated
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Documentation complete

---

## Document End

**This document should be read in conjunction with Part 1.**

When implementing, always:
1. Read the complete development plan first
2. Follow the phase order
3. Test each phase before proceeding
4. Update SKILL.md with new components
5. Never hardcode values that belong in YAML
