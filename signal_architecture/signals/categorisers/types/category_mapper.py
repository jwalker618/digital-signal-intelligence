"""
Category Mapper Categorizer

Maps aggregated data to categorical values (strings).
Used for categorical_groups like operator_type, fleet_size, regulatory_framework.

The output category maps to a modifier defined in the YAML config's categorical_features.

Examples:
    - Map fleet count to: SINGLE, MICRO, SMALL, MEDIUM, LARGE, MAJOR
    - Map regulatory body to: FAA, EASA, CAA_UK, etc.
    - Map alliance code to: STAR_ALLIANCE, ONEWORLD, SKYTEAM, NONE
"""

from typing import Any, Dict, List, Optional

from ..base import ProductionCategorizer
from ...types import CategorizerResult


class CategoryMapperCategorizer(ProductionCategorizer):
    """
    Maps aggregated data to a categorical value using rules.
    
    Params Schema:
        {
            "rules": [
                {
                    "conditions": {           # All conditions must match
                        "field1": value,      # Simple equality
                        "field2": {           # Operator-based
                            "op": "gte",      # eq, ne, gt, gte, lt, lte, in, not_in, contains
                            "value": 100
                        }
                    },
                    "category": "CATEGORY_NAME"
                },
                ...
            ],
            "default_category": str,          # Category if no rule matches (default: "UNKNOWN")
            "default_confidence": float       # Confidence for default (default: 0.5)
        }
    
    Example:
        # Map fleet size to categories
        params = {
            "rules": [
                {"conditions": {"fleet_count": {"op": "gte", "value": 150}}, "category": "MAJOR"},
                {"conditions": {"fleet_count": {"op": "gte", "value": 51}}, "category": "LARGE"},
                {"conditions": {"fleet_count": {"op": "gte", "value": 21}}, "category": "MEDIUM"},
                {"conditions": {"fleet_count": {"op": "gte", "value": 6}}, "category": "SMALL"},
                {"conditions": {"fleet_count": {"op": "gte", "value": 2}}, "category": "MICRO"},
                {"conditions": {"fleet_count": {"op": "eq", "value": 1}}, "category": "SINGLE"},
            ],
            "default_category": "UNKNOWN"
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """
        Map aggregated data to a category.
        
        Args:
            aggregated_data: Data to evaluate against rules
            params: Configuration with rules and default
        
        Returns:
            CategorizerResult with category string
        """
        rules = self._get_param(params, "rules", required=True)
        default_category = self._get_param(params, "default_category", default="UNKNOWN")
        default_confidence = self._get_param(params, "default_confidence", default=0.5)
        
        # Evaluate rules in order
        for rule in rules:
            conditions = rule.get("conditions", {})
            category = rule.get("category")
            
            if self._condition_match(aggregated_data, conditions):
                return self._create_category_result(
                    category=category,
                    confidence=1.0,
                    reasoning=f"Matched rule for {category}"
                )
        
        # No rule matched
        return self._create_category_result(
            category=default_category,
            confidence=default_confidence,
            reasoning=f"No rule matched, using default: {default_category}"
        )


class DirectMappingCategorizer(ProductionCategorizer):
    """
    Direct value-to-category mapping from a single field.
    
    Simpler than CategoryMapperCategorizer when mapping is straightforward.
    
    Params Schema:
        {
            "value_field": str,           # Field to map from
            "mapping": {                  # Direct value -> category mapping
                "value1": "CATEGORY_A",
                "value2": "CATEGORY_B",
                ...
            },
            "case_insensitive": bool,     # If True, match case-insensitively (default: True)
            "default_category": str,      # Default if no mapping matches (default: "UNKNOWN")
            "null_category": str          # Category for null values (default: uses default_category)
        }
    
    Example:
        # Map alliance code to category
        params = {
            "value_field": "alliance_code",
            "mapping": {
                "STAR": "STAR_ALLIANCE",
                "OW": "ONEWORLD", 
                "ST": "SKYTEAM"
            },
            "default_category": "NO_ALLIANCE"
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """Apply direct value-to-category mapping."""
        value_field = self._get_param(params, "value_field", required=True)
        mapping = self._get_param(params, "mapping", required=True)
        case_insensitive = self._get_param(params, "case_insensitive", default=True)
        default_category = self._get_param(params, "default_category", default="UNKNOWN")
        null_category = self._get_param(params, "null_category", default=None)
        
        value = self._get_value(aggregated_data, value_field)
        
        # Handle null
        if value is None:
            category = null_category or default_category
            return self._create_category_result(
                category=category,
                confidence=0.5 if category == default_category else 1.0,
                reasoning=f"{value_field} is null → {category}"
            )
        
        # Convert to string for matching
        str_value = str(value)
        
        # Try direct match
        if str_value in mapping:
            return self._create_category_result(
                category=mapping[str_value],
                confidence=1.0,
                reasoning=f"{value_field}='{str_value}' → {mapping[str_value]}"
            )
        
        # Try case-insensitive match
        if case_insensitive:
            upper_value = str_value.upper()
            for key, category in mapping.items():
                if key.upper() == upper_value:
                    return self._create_category_result(
                        category=category,
                        confidence=1.0,
                        reasoning=f"{value_field}='{str_value}' → {category}"
                    )
        
        # No match found
        return self._create_category_result(
            category=default_category,
            confidence=0.5,
            reasoning=f"{value_field}='{str_value}' not in mapping → {default_category}"
        )


class RangeCategorizer(ProductionCategorizer):
    """
    Maps a numeric value to categories based on ranges.
    
    Useful for size-based categories, age brackets, etc.
    
    Params Schema:
        {
            "value_field": str,           # Numeric field to evaluate
            "ranges": [
                {
                    "min": float,         # Minimum value (inclusive, optional)
                    "max": float,         # Maximum value (exclusive, optional)
                    "category": str       # Category for this range
                },
                ...
            ],
            "default_category": str,      # Default if no range matches
            "null_category": str          # Category for null values
        }
    
    Example:
        # Map fleet size to categories
        params = {
            "value_field": "fleet_count",
            "ranges": [
                {"min": 150, "category": "MAJOR"},
                {"min": 51, "max": 150, "category": "LARGE"},
                {"min": 21, "max": 51, "category": "MEDIUM"},
                {"min": 6, "max": 21, "category": "SMALL"},
                {"min": 2, "max": 6, "category": "MICRO"},
                {"max": 2, "category": "SINGLE"}
            ],
            "default_category": "UNKNOWN"
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """Map numeric value to category based on ranges."""
        value_field = self._get_param(params, "value_field", required=True)
        ranges = self._get_param(params, "ranges", required=True)
        default_category = self._get_param(params, "default_category", default="UNKNOWN")
        null_category = self._get_param(params, "null_category", default=None)
        
        value = self._get_value(aggregated_data, value_field)
        
        # Handle null
        if value is None:
            category = null_category or default_category
            return self._create_category_result(
                category=category,
                confidence=0.5,
                reasoning=f"{value_field} is null → {category}"
            )
        
        # Convert to numeric
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return self._create_category_result(
                category=default_category,
                confidence=0.0,
                reasoning=f"Cannot convert {value_field}='{value}' to numeric"
            )
        
        # Find matching range
        for range_def in ranges:
            min_val = range_def.get("min", float("-inf"))
            max_val = range_def.get("max", float("inf"))
            category = range_def.get("category")
            
            if min_val <= numeric_value < max_val:
                return self._create_category_result(
                    category=category,
                    confidence=1.0,
                    reasoning=f"{value_field}={numeric_value} in [{min_val}, {max_val}) → {category}"
                )
        
        # No range matched
        return self._create_category_result(
            category=default_category,
            confidence=0.5,
            reasoning=f"{value_field}={numeric_value} not in any range → {default_category}"
        )


class MultiFieldCategorizer(ProductionCategorizer):
    """
    Determines category based on multiple fields with priority rules.
    
    Useful when category depends on combination of factors.
    
    Params Schema:
        {
            "priority_rules": [           # Evaluated in order, first match wins
                {
                    "conditions": {...},  # Same as CategoryMapperCategorizer
                    "category": str
                },
                ...
            ],
            "fallback_field": str,        # Field to use if no rule matches
            "fallback_mapping": {...},    # Mapping for fallback field
            "default_category": str
        }
    
    Example:
        # Determine operator type from multiple signals
        params = {
            "priority_rules": [
                {
                    "conditions": {
                        "is_major_airline": True,
                        "fleet_count": {"op": "gte", "value": 100}
                    },
                    "category": "MAJOR_AIRLINE"
                },
                {
                    "conditions": {"is_cargo_only": True},
                    "category": "CARGO_AIRLINE"
                }
            ],
            "fallback_field": "operator_type_raw",
            "fallback_mapping": {"charter": "CHARTER_OPERATOR", ...},
            "default_category": "OTHER"
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """Determine category from multiple fields."""
        priority_rules = self._get_param(params, "priority_rules", default=[])
        fallback_field = self._get_param(params, "fallback_field", default=None)
        fallback_mapping = self._get_param(params, "fallback_mapping", default={})
        default_category = self._get_param(params, "default_category", default="UNKNOWN")
        
        # Try priority rules first
        for rule in priority_rules:
            conditions = rule.get("conditions", {})
            category = rule.get("category")
            
            if self._condition_match(aggregated_data, conditions):
                return self._create_category_result(
                    category=category,
                    confidence=1.0,
                    reasoning=f"Priority rule matched: {category}"
                )
        
        # Try fallback field
        if fallback_field:
            value = self._get_value(aggregated_data, fallback_field)
            if value is not None:
                str_value = str(value).upper()
                if str_value in fallback_mapping:
                    return self._create_category_result(
                        category=fallback_mapping[str_value],
                        confidence=0.8,
                        reasoning=f"Fallback mapping: {fallback_field}={value}"
                    )
                # Check case-insensitive
                for key, category in fallback_mapping.items():
                    if key.upper() == str_value:
                        return self._create_category_result(
                            category=category,
                            confidence=0.8,
                            reasoning=f"Fallback mapping: {fallback_field}={value}"
                        )
        
        # Default
        return self._create_category_result(
            category=default_category,
            confidence=0.3,
            reasoning=f"No rules matched, using default: {default_category}"
        )
