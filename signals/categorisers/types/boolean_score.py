"""
Boolean Score Categorizer

Maps boolean values to scores. Simple but common pattern for presence/absence signals.

Examples:
    - Has IOSA certification: True = 100, False = 0
    - Has alliance membership: True = 90, False = 30
    - Is on EU safety list: True = 0, False = 100 (inverted)
"""

from typing import Any, Dict, List, Optional

from ..base import ProductionCategorizer
from ...types import CategorizerResult


class BooleanScoreCategorizer(ProductionCategorizer):
    """
    Maps a boolean value to a score.
    
    Params Schema:
        {
            "value_field": str,           # Field in aggregated_data to evaluate
            "true_score": float,          # Score when value is True (default: 100)
            "false_score": float,         # Score when value is False (default: 0)
            "null_score": float,          # Score when value is None (default: 50)
            "null_confidence": float,     # Confidence when null (default: 0.0)
            "invert": bool                # If True, swap true/false scores (default: False)
        }
    
    Example:
        # Has IOSA registration (positive signal)
        params = {
            "value_field": "has_iosa",
            "true_score": 100,
            "false_score": 25
        }
        
        # Is on banned list (negative signal - invert)
        params = {
            "value_field": "on_eu_safety_list",
            "true_score": 0,
            "false_score": 100
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """
        Apply boolean scoring to aggregated data.
        
        Args:
            aggregated_data: Data containing the boolean field
            params: Configuration with scores for true/false
        
        Returns:
            CategorizerResult with score based on boolean value
        """
        value_field = self._get_param(params, "value_field", required=True)
        true_score = self._get_param(params, "true_score", default=100)
        false_score = self._get_param(params, "false_score", default=0)
        null_score = self._get_param(params, "null_score", default=50)
        null_confidence = self._get_param(params, "null_confidence", default=0.0)
        invert = self._get_param(params, "invert", default=False)
        
        if invert:
            true_score, false_score = false_score, true_score
        
        value = self._get_value(aggregated_data, value_field)
        
        # Handle null
        if value is None:
            return self._create_score_result(
                score=null_score,
                confidence=null_confidence,
                reasoning=f"No value for {value_field}"
            )
        
        # Normalize to boolean
        bool_value = self._normalize_to_bool(value)
        score = true_score if bool_value else false_score
        
        return self._create_score_result(
            score=score,
            confidence=1.0,
            reasoning=f"{value_field}={bool_value} → score={score}"
        )
    
    def _normalize_to_bool(self, value: Any) -> bool:
        """Convert various representations to boolean."""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "active", "valid", "y", "registered")
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        return bool(value)


class PresenceScoreCategorizer(ProductionCategorizer):
    """
    Scores based on presence (non-empty) vs absence (null/empty) of a value.
    
    More flexible than BooleanScoreCategorizer - considers empty strings,
    empty lists, zero values as "absent".
    
    Params Schema:
        {
            "value_field": str,           # Field to check
            "present_score": float,       # Score when value is present (default: 100)
            "absent_score": float,        # Score when value is absent (default: 0)
            "treat_zero_as_absent": bool, # If True, 0 counts as absent (default: True)
            "treat_empty_as_absent": bool # If True, "" and [] count as absent (default: True)
        }
    
    Example:
        # Has credit rating (presence is positive)
        params = {
            "value_field": "credit_rating",
            "present_score": 80,
            "absent_score": 40
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """Score based on presence/absence of value."""
        value_field = self._get_param(params, "value_field", required=True)
        present_score = self._get_param(params, "present_score", default=100)
        absent_score = self._get_param(params, "absent_score", default=0)
        treat_zero_as_absent = self._get_param(params, "treat_zero_as_absent", default=True)
        treat_empty_as_absent = self._get_param(params, "treat_empty_as_absent", default=True)
        
        value = self._get_value(aggregated_data, value_field)
        
        # Determine if present
        is_present = value is not None
        
        if is_present and treat_empty_as_absent:
            if isinstance(value, (str, list, dict)) and len(value) == 0:
                is_present = False
        
        if is_present and treat_zero_as_absent:
            if value == 0:
                is_present = False
        
        score = present_score if is_present else absent_score
        status = "present" if is_present else "absent"
        
        return self._create_score_result(
            score=score,
            confidence=1.0,
            reasoning=f"{value_field} is {status} → score={score}"
        )


class MultiBooleanScoreCategorizer(ProductionCategorizer):
    """
    Scores based on multiple boolean fields with individual weights.
    
    Useful for composite presence checks (e.g., security controls checklist).
    
    Params Schema:
        {
            "fields": [
                {
                    "field": str,         # Field name
                    "weight": float,      # Weight for this field (default: 1.0)
                    "true_score": float,  # Score when true (default: 100)
                    "false_score": float  # Score when false (default: 0)
                },
                ...
            ],
            "null_handling": str          # "skip", "false", or "neutral" (default: "skip")
        }
    
    Example:
        params = {
            "fields": [
                {"field": "has_mfa", "weight": 2.0},
                {"field": "has_edr", "weight": 1.5},
                {"field": "has_backup", "weight": 1.0},
                {"field": "has_training", "weight": 0.5}
            ]
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """Score based on multiple boolean fields."""
        fields = self._get_param(params, "fields", required=True)
        null_handling = self._get_param(params, "null_handling", default="skip")
        
        total_score = 0.0
        total_weight = 0.0
        max_weight = 0.0
        details = []
        
        for field_config in fields:
            field_name = field_config.get("field")
            weight = field_config.get("weight", 1.0)
            true_score = field_config.get("true_score", 100)
            false_score = field_config.get("false_score", 0)
            
            max_weight += weight
            value = self._get_value(aggregated_data, field_name)
            
            if value is None:
                if null_handling == "skip":
                    continue
                elif null_handling == "false":
                    value = False
                elif null_handling == "neutral":
                    total_score += 50 * weight
                    total_weight += weight
                    continue
            
            # Normalize to bool
            bool_value = bool(value) if not isinstance(value, bool) else value
            field_score = true_score if bool_value else false_score
            
            total_score += field_score * weight
            total_weight += weight
            details.append(f"{field_name}={bool_value}")
        
        if total_weight == 0:
            return self._create_score_result(
                score=50,
                confidence=0.0,
                reasoning="No valid boolean fields found"
            )
        
        final_score = total_score / total_weight
        confidence = total_weight / max_weight if max_weight > 0 else 0.0
        
        return self._create_score_result(
            score=final_score,
            confidence=confidence,
            reasoning=f"Multi-boolean: {', '.join(details)}"
        )
