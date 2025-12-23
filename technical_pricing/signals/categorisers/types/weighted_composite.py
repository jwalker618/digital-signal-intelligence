"""
Weighted Composite Categorizer

Combines multiple sub-scores or fields into a single weighted score.
Core categorizer for complex signals that aggregate multiple factors.

Examples:
    - Alliance membership score from: alliance_tier * 0.5 + years * 0.3 + founding_member * 0.2
    - Safety score from: accident_score * 0.4 + incident_score * 0.3 + regulatory_score * 0.3
"""

from typing import Any, Dict, List, Optional, Tuple

from ..base import ProductionCategorizer
from ...types import CategorizerResult


class WeightedCompositeCategorizer(ProductionCategorizer):
    """
    Combines multiple fields into a weighted composite score.
    
    Params Schema:
        {
            "components": [
                {
                    "field": str,         # Field name in aggregated_data
                    "weight": float,      # Weight for this component (weights should sum to 1.0)
                    "scale": float,       # Optional: multiply field value by scale before using
                    "min": float,         # Optional: minimum value (clamp)
                    "max": float,         # Optional: maximum value (clamp)
                    "default": float      # Optional: default if field is missing
                },
                ...
            ],
            "null_handling": str,         # "skip", "zero", "neutral", "default" (default: "skip")
            "normalize_weights": bool,    # If True, normalize weights to sum to 1.0 (default: True)
            "min_components": int         # Minimum components needed for valid result (default: 1)
        }
    
    Example:
        params = {
            "components": [
                {"field": "alliance_tier", "weight": 0.5, "scale": 33.33},  # 0-3 -> 0-100
                {"field": "membership_years", "weight": 0.3, "scale": 10, "max": 100},
                {"field": "founding_member_score", "weight": 0.2}
            ],
            "null_handling": "skip"
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """
        Calculate weighted composite score from multiple fields.
        
        Args:
            aggregated_data: Data containing component fields
            params: Configuration with components and weights
        
        Returns:
            CategorizerResult with weighted composite score
        """
        components = self._get_param(params, "components", required=True)
        null_handling = self._get_param(params, "null_handling", default="skip")
        normalize_weights = self._get_param(params, "normalize_weights", default=True)
        min_components = self._get_param(params, "min_components", default=1)
        
        total_score = 0.0
        total_weight = 0.0
        max_possible_weight = sum(c.get("weight", 1.0) for c in components)
        valid_components = 0
        details = []
        
        for comp in components:
            field = comp.get("field")
            weight = comp.get("weight", 1.0)
            scale = comp.get("scale", 1.0)
            min_val = comp.get("min")
            max_val = comp.get("max")
            default = comp.get("default")
            
            value = self._get_value(aggregated_data, field)
            
            # Handle null values
            if value is None:
                if null_handling == "skip":
                    continue
                elif null_handling == "zero":
                    value = 0
                elif null_handling == "neutral":
                    value = 50
                elif null_handling == "default" and default is not None:
                    value = default
                else:
                    continue
            
            # Convert to numeric
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue
            
            # Apply scale
            scaled_value = numeric_value * scale
            
            # Apply bounds
            if min_val is not None:
                scaled_value = max(min_val, scaled_value)
            if max_val is not None:
                scaled_value = min(max_val, scaled_value)
            
            total_score += scaled_value * weight
            total_weight += weight
            valid_components += 1
            details.append(f"{field}={numeric_value}*{scale}={scaled_value:.1f}")
        
        # Check minimum components
        if valid_components < min_components:
            return self._create_score_result(
                score=50,
                confidence=0.0,
                reasoning=f"Insufficient components: {valid_components} < {min_components}"
            )
        
        # Calculate final score
        if total_weight == 0:
            return self._create_score_result(
                score=50,
                confidence=0.0,
                reasoning="No valid components with weight"
            )
        
        if normalize_weights:
            final_score = total_score / total_weight
        else:
            final_score = total_score
        
        # Clamp to 0-100
        final_score = max(0, min(100, final_score))
        
        # Calculate confidence
        confidence = total_weight / max_possible_weight if max_possible_weight > 0 else 0.0
        
        return self._create_score_result(
            score=final_score,
            confidence=confidence,
            reasoning=f"Weighted composite: {', '.join(details)}"
        )


class LinearScaleCategorizer(ProductionCategorizer):
    """
    Linearly scales a single value from an input range to a score range.
    
    Params Schema:
        {
            "value_field": str,           # Field to scale
            "input_min": float,           # Minimum of input range
            "input_max": float,           # Maximum of input range
            "output_min": float,          # Minimum score (default: 0)
            "output_max": float,          # Maximum score (default: 100)
            "clamp": bool,                # Clamp output to range (default: True)
            "invert": bool,               # If True, higher input = lower score (default: False)
            "null_score": float,          # Score when null (default: 50)
            "null_confidence": float      # Confidence when null (default: 0.0)
        }
    
    Example:
        # Scale fleet age 0-25 years to score 100-0 (younger = better)
        params = {
            "value_field": "average_age",
            "input_min": 0,
            "input_max": 25,
            "invert": True
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """Apply linear scaling to produce score."""
        value_field = self._get_param(params, "value_field", required=True)
        input_min = self._get_param(params, "input_min", required=True)
        input_max = self._get_param(params, "input_max", required=True)
        output_min = self._get_param(params, "output_min", default=0)
        output_max = self._get_param(params, "output_max", default=100)
        clamp = self._get_param(params, "clamp", default=True)
        invert = self._get_param(params, "invert", default=False)
        null_score = self._get_param(params, "null_score", default=50)
        null_confidence = self._get_param(params, "null_confidence", default=0.0)
        
        value = self._get_value(aggregated_data, value_field)
        
        if value is None:
            return self._create_score_result(
                score=null_score,
                confidence=null_confidence,
                reasoning=f"No value for {value_field}"
            )
        
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return self._create_error_result(f"Cannot convert {value_field} to numeric")
        
        # Apply scaling
        if invert:
            score = self._inverse_scale(
                numeric_value, input_min, input_max, output_min, output_max, clamp
            )
        else:
            score = self._linear_scale(
                numeric_value, input_min, input_max, output_min, output_max, clamp
            )
        
        return self._create_score_result(
            score=score,
            confidence=1.0,
            reasoning=f"{value_field}={numeric_value} scaled to {score:.1f}"
        )


class AverageScoreCategorizer(ProductionCategorizer):
    """
    Calculates simple or weighted average of multiple score fields.
    
    Simpler than WeightedCompositeCategorizer when all fields are already 0-100 scores.
    
    Params Schema:
        {
            "fields": [str, ...],         # List of field names to average
            "weights": [float, ...],      # Optional weights (default: equal weights)
            "null_handling": str,         # "skip", "zero", "neutral" (default: "skip")
            "min_fields": int             # Minimum fields needed (default: 1)
        }
    
    Example:
        params = {
            "fields": ["safety_score", "regulatory_score", "operational_score"],
            "weights": [0.4, 0.35, 0.25]
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """Calculate average of score fields."""
        fields = self._get_param(params, "fields", required=True)
        weights = self._get_param(params, "weights", default=None)
        null_handling = self._get_param(params, "null_handling", default="skip")
        min_fields = self._get_param(params, "min_fields", default=1)
        
        # Default to equal weights
        if weights is None:
            weights = [1.0] * len(fields)
        
        if len(weights) != len(fields):
            return self._create_error_result("Number of weights must match number of fields")
        
        scores = []
        used_weights = []
        
        for field, weight in zip(fields, weights):
            value = self._get_value(aggregated_data, field)
            
            if value is None:
                if null_handling == "skip":
                    continue
                elif null_handling == "zero":
                    value = 0
                elif null_handling == "neutral":
                    value = 50
            
            try:
                score = float(value)
                scores.append(score)
                used_weights.append(weight)
            except (TypeError, ValueError):
                continue
        
        if len(scores) < min_fields:
            return self._create_score_result(
                score=50,
                confidence=0.0,
                reasoning=f"Insufficient fields: {len(scores)} < {min_fields}"
            )
        
        # Calculate weighted average
        total_weight = sum(used_weights)
        if total_weight == 0:
            return self._create_score_result(score=50, confidence=0.0)
        
        weighted_sum = sum(s * w for s, w in zip(scores, used_weights))
        final_score = weighted_sum / total_weight
        
        confidence = len(scores) / len(fields)
        
        return self._create_score_result(
            score=final_score,
            confidence=confidence,
            reasoning=f"Average of {len(scores)} fields = {final_score:.1f}"
        )
