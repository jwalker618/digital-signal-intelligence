"""
DSI Signal Architecture - Categorizer Base

This module provides the base class and utilities for Categorizers.
Categorizers apply scoring/categorization logic to produce final values.

Implementation Status: PRODUCTION READY
    Categorizer TYPES are reusable across many signals. Logic is
    parameterized, not signal-specific. Must be deterministic.

Key principles:
    - Categorizers are generic and reusable
    - All configuration comes through params dict
    - Return either score (0-100) OR category string
    - Deterministic: same inputs always produce same outputs
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Callable

from ..base import BaseCategorizer
from ..types import CategorizerResult


class ProductionCategorizer(BaseCategorizer):
    """
    Extended base class for production-ready categorizers with utilities.
    
    Provides helper methods for common scoring patterns, threshold
    evaluation, and parameterized logic.
    """
    
    def _get_param(
        self,
        params: Dict[str, Any],
        key: str,
        default: Any = None,
        required: bool = False
    ) -> Any:
        """
        Safely get a parameter with optional requirement enforcement.
        
        Args:
            params: Parameters dictionary
            key: Parameter key to retrieve
            default: Default value if not found
            required: If True, raise error when missing
        
        Returns:
            Parameter value or default
        
        Raises:
            ValueError if required parameter is missing
        """
        value = params.get(key, default)
        if required and value is None:
            raise ValueError(f"Required parameter '{key}' not provided")
        return value
    
    def _get_value(
        self,
        data: Dict[str, Any],
        field: str,
        default: Any = None
    ) -> Any:
        """
        Get a value from aggregated data, supporting nested paths.
        
        Args:
            data: Aggregated data dictionary
            field: Field name or dot-separated path (e.g., "metrics.score")
            default: Default if not found
        
        Returns:
            Field value or default
        """
        if "." not in field:
            return data.get(field, default)
        
        # Handle nested path
        current = data
        for part in field.split("."):
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return default
            else:
                return default
        
        return current
    
    def _linear_scale(
        self,
        value: float,
        min_input: float,
        max_input: float,
        min_output: float = 0,
        max_output: float = 100,
        clamp: bool = True
    ) -> float:
        """
        Linearly scale a value from one range to another.
        
        Args:
            value: Input value
            min_input: Minimum of input range
            max_input: Maximum of input range
            min_output: Minimum of output range (default 0)
            max_output: Maximum of output range (default 100)
            clamp: If True, clamp output to range
        
        Returns:
            Scaled value
        """
        if max_input == min_input:
            return (min_output + max_output) / 2
        
        # Scale
        ratio = (value - min_input) / (max_input - min_input)
        result = min_output + ratio * (max_output - min_output)
        
        if clamp:
            # Handle both normal and reversed output ranges
            low = min(min_output, max_output)
            high = max(min_output, max_output)
            result = max(low, min(high, result))
        
        return result
    
    def _inverse_scale(
        self,
        value: float,
        min_input: float,
        max_input: float,
        min_output: float = 0,
        max_output: float = 100,
        clamp: bool = True
    ) -> float:
        """
        Inversely scale a value (higher input = lower output).
        
        Useful for metrics where lower is better (e.g., incident count).
        """
        return self._linear_scale(
            value, min_input, max_input,
            max_output, min_output,  # Reversed
            clamp
        )
    
    def _threshold_score(
        self,
        value: float,
        thresholds: List[Dict[str, float]],
        default_score: float = 50
    ) -> float:
        """
        Assign score based on threshold buckets.
        
        Args:
            value: Input value to evaluate
            thresholds: List of {"max": x, "score": y} in ascending order
            default_score: Score if value exceeds all thresholds
        
        Returns:
            Score from matching bucket
        
        Example:
            thresholds = [
                {"max": 5, "score": 100},   # 0-5: excellent
                {"max": 10, "score": 75},   # 6-10: good
                {"max": 20, "score": 50},   # 11-20: average
            ]
            _threshold_score(3, thresholds)  # Returns 100
            _threshold_score(15, thresholds) # Returns 50
            _threshold_score(25, thresholds) # Returns 50 (default)
        """
        sorted_thresholds = sorted(thresholds, key=lambda x: x["max"])
        
        for threshold in sorted_thresholds:
            if value <= threshold["max"]:
                return threshold["score"]
        
        return default_score
    
    def _range_score(
        self,
        value: float,
        ranges: List[Dict[str, Any]],
        default_score: float = 50
    ) -> float:
        """
        Assign score based on explicit min/max ranges.
        
        Args:
            value: Input value to evaluate
            ranges: List of {"min": x, "max": y, "score": z}
            default_score: Score if no range matches
        
        Returns:
            Score from matching range
        """
        for r in ranges:
            min_val = r.get("min", float("-inf"))
            max_val = r.get("max", float("inf"))
            if min_val <= value <= max_val:
                return r["score"]
        
        return default_score
    
    def _boolean_score(
        self,
        value: bool,
        true_score: float = 100,
        false_score: float = 0
    ) -> float:
        """
        Convert boolean to score.
        
        Args:
            value: Boolean value
            true_score: Score when True
            false_score: Score when False
        
        Returns:
            Corresponding score
        """
        return true_score if value else false_score
    
    def _presence_score(
        self,
        value: Any,
        present_score: float = 100,
        absent_score: float = 0
    ) -> float:
        """
        Score based on presence/absence of value.
        
        None, empty string, empty list, 0 are considered absent.
        """
        if value is None:
            return absent_score
        if isinstance(value, (str, list, dict)) and len(value) == 0:
            return absent_score
        if value == 0:
            return absent_score
        return present_score
    
    def _count_score(
        self,
        count: int,
        thresholds: List[Dict[str, Any]],
        default_score: float = 50
    ) -> float:
        """
        Score based on count using thresholds.
        
        Convenience wrapper around _threshold_score for counts.
        """
        return self._threshold_score(count, thresholds, default_score)
    
    def _weighted_average(
        self,
        components: List[Dict[str, Any]],
        data: Dict[str, Any],
        null_handling: str = "skip"
    ) -> tuple[float, float]:
        """
        Calculate weighted average of multiple fields.
        
        Args:
            components: List of {"field": str, "weight": float}
            data: Data dictionary containing field values
            null_handling: "skip" (exclude nulls), "zero" (treat as 0), "neutral" (treat as 50)
        
        Returns:
            Tuple of (weighted_score, confidence)
            Confidence = proportion of weight that had valid data
        """
        total_score = 0.0
        total_weight = 0.0
        available_weight = 0.0
        max_weight = sum(c.get("weight", 0) for c in components)
        
        for component in components:
            field = component.get("field")
            weight = component.get("weight", 1.0)
            
            value = self._get_value(data, field)
            
            if value is None:
                if null_handling == "skip":
                    continue
                elif null_handling == "zero":
                    value = 0
                elif null_handling == "neutral":
                    value = 50
            
            try:
                score = float(value)
                total_score += score * weight
                total_weight += weight
                available_weight += weight
            except (TypeError, ValueError):
                continue
        
        if total_weight == 0:
            return 50.0, 0.0
        
        weighted_score = total_score / total_weight
        confidence = available_weight / max_weight if max_weight > 0 else 0.0
        
        return weighted_score, confidence
    
    def _category_match(
        self,
        value: Any,
        rules: List[Dict[str, Any]],
        default_category: str = "UNKNOWN"
    ) -> str:
        """
        Match value to category using rules.
        
        Args:
            value: Value to categorize
            rules: List of {"match": x, "category": y} or {"matches": [...], "category": y}
            default_category: Category if no rule matches
        
        Returns:
            Matched category string
        """
        for rule in rules:
            # Single match
            if "match" in rule:
                if value == rule["match"]:
                    return rule["category"]
            
            # Multiple matches
            if "matches" in rule:
                if value in rule["matches"]:
                    return rule["category"]
            
            # Range match (for numeric)
            if "min" in rule or "max" in rule:
                try:
                    num_val = float(value)
                    min_val = rule.get("min", float("-inf"))
                    max_val = rule.get("max", float("inf"))
                    if min_val <= num_val <= max_val:
                        return rule["category"]
                except (TypeError, ValueError):
                    continue
        
        return default_category
    
    def _condition_match(
        self,
        data: Dict[str, Any],
        conditions: Dict[str, Any]
    ) -> bool:
        """
        Check if data matches all conditions.
        
        Args:
            data: Data dictionary to check
            conditions: Dict of {field: expected_value} or {field: {"op": x, "value": y}}
        
        Returns:
            True if all conditions match
        
        Supported operators:
            eq, ne, gt, gte, lt, lte, in, not_in, contains
        """
        for field, expected in conditions.items():
            actual = self._get_value(data, field)
            
            # Simple equality check
            if not isinstance(expected, dict):
                if actual != expected:
                    return False
                continue
            
            # Operator-based check
            op = expected.get("op", "eq")
            value = expected.get("value")
            
            if op == "eq" and actual != value:
                return False
            elif op == "ne" and actual == value:
                return False
            elif op == "gt" and not (actual is not None and actual > value):
                return False
            elif op == "gte" and not (actual is not None and actual >= value):
                return False
            elif op == "lt" and not (actual is not None and actual < value):
                return False
            elif op == "lte" and not (actual is not None and actual <= value):
                return False
            elif op == "in" and actual not in value:
                return False
            elif op == "not_in" and actual in value:
                return False
            elif op == "contains" and value not in (actual or ""):
                return False
        
        return True
    
    def _calculate_confidence(
        self,
        data: Dict[str, Any],
        required_fields: List[str],
        optional_fields: List[str] = None
    ) -> float:
        """
        Calculate confidence based on field availability.
        
        Args:
            data: Data dictionary
            required_fields: Fields that must be present (weighted heavily)
            optional_fields: Fields that improve confidence (weighted lightly)
        
        Returns:
            Confidence score 0-1
        """
        if not required_fields:
            return 1.0
        
        optional_fields = optional_fields or []
        
        # Check required fields (80% weight)
        required_present = sum(
            1 for f in required_fields
            if self._get_value(data, f) is not None
        )
        required_ratio = required_present / len(required_fields)
        
        # Check optional fields (20% weight)
        if optional_fields:
            optional_present = sum(
                1 for f in optional_fields
                if self._get_value(data, f) is not None
            )
            optional_ratio = optional_present / len(optional_fields)
        else:
            optional_ratio = 1.0
        
        return (required_ratio * 0.8) + (optional_ratio * 0.2)
