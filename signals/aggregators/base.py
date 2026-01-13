"""
DSI Signal Architecture - Aggregator Base

This module provides the base class and utilities for Aggregators.
Aggregators transform raw extractor data into normalized structures
optimized for scoring/categorization.

Implementation Status: PRODUCTION READY
    Aggregators must be production-ready and require no changes when
    extractors are upgraded from stubs to real data sources. They must
    handle missing/malformed data gracefully.

Key responsibilities:
    - Normalize varied input structures into consistent output
    - Handle missing fields with sensible defaults
    - Validate data quality and add warnings (not errors) for issues
    - Support multiple extractor inputs when needed
"""

from abc import abstractmethod
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union

from ..base import BaseAggregator
from ..types import AggregatorResult, ExtractorResult


def utcnow() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    from datetime import timezone
    return datetime.now(timezone.utc)


class ProductionAggregator(BaseAggregator):
    """
    Extended base class for production-ready aggregators with utilities.
    
    Provides helper methods for common normalization tasks, data validation,
    and defensive data access patterns.
    
    Example:
        class AllianceAggregator(ProductionAggregator):
            def aggregate(self, results: List[ExtractorResult]) -> AggregatorResult:
                raw = self._get_primary_data(results)
                
                has_alliance = self._normalize_bool(raw.get("membership_status") == "ACTIVE")
                years = self._calculate_years_since(raw.get("join_date"))
                
                return self._create_success_result({
                    "has_alliance": has_alliance,
                    "membership_years": years,
                }, results)
    """
    
    def _create_success_result(
        self,
        data: Dict[str, Any],
        extractor_results: List[ExtractorResult] = None,
        warnings: Optional[List[str]] = None
    ) -> AggregatorResult:
        """
        Helper to create a successful aggregation result.
        
        Args:
            data: The aggregated/normalized data
            extractor_results: Original extractor results (for tracking sources)
            warnings: Any warnings generated during aggregation
        """
        sources = []
        source_count = 0
        
        if extractor_results:
            source_count = len(extractor_results)
            sources = [r.source for r in extractor_results if r.success]
        
        return AggregatorResult(
            success=True,
            data=data,
            aggregated_at=utcnow(),
            source_extractions=source_count,
            sources=sources,
            warnings=warnings or []
        )
    
    def _create_error_result(self, error: str) -> AggregatorResult:
        """Helper to create a failed aggregation result."""
        return AggregatorResult(
            success=False,
            data={},
            aggregated_at=utcnow(),
            error=error
        )
    
    def _get_primary_data(
        self,
        extractor_results: List[ExtractorResult],
        data_key: str = "data"
    ) -> Dict[str, Any]:
        """
        Extract the primary data dictionary from extractor results.
        
        Args:
            extractor_results: List of ExtractorResult
            data_key: Key within the result data to extract (default "data")
        
        Returns:
            The data dictionary, or empty dict if not found
        """
        if not extractor_results:
            return {}
        
        result = extractor_results[0]
        if not result.success:
            return {}
        
        data = result.data
        if data_key and data_key in data:
            return data.get(data_key, {})
        return data
    
    def _merge_extractor_data(
        self,
        extractor_results: List[ExtractorResult]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Merge data from multiple extractors keyed by source.
        
        Returns:
            Dict mapping source name to data
        """
        merged = {}
        for result in extractor_results:
            if result.success:
                merged[result.source] = result.data
        return merged
    
    def _normalize_bool(
        self,
        value: Any,
        true_values: List[Any] = None,
        default: bool = False
    ) -> bool:
        """
        Normalize various representations to boolean.
        
        Args:
            value: Input value to normalize
            true_values: Values that should be considered True
            default: Default if value is None
        
        Returns:
            Normalized boolean
        """
        if value is None:
            return default
        
        if isinstance(value, bool):
            return value
        
        if true_values and value in true_values:
            return True
        
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "active", "valid", "y")
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        return default
    
    def _normalize_int(
        self,
        value: Any,
        default: int = 0,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None
    ) -> int:
        """
        Normalize to integer with optional bounds.
        
        Args:
            value: Input value to normalize
            default: Default if value cannot be converted
            min_val: Minimum allowed value (clamp)
            max_val: Maximum allowed value (clamp)
        
        Returns:
            Normalized integer
        """
        if value is None:
            return default
        
        try:
            result = int(value)
        except (ValueError, TypeError):
            return default
        
        if min_val is not None:
            result = max(min_val, result)
        if max_val is not None:
            result = min(max_val, result)
        
        return result
    
    def _normalize_float(
        self,
        value: Any,
        default: float = 0.0,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        decimals: Optional[int] = None
    ) -> float:
        """
        Normalize to float with optional bounds and precision.
        """
        if value is None:
            return default
        
        try:
            result = float(value)
        except (ValueError, TypeError):
            return default
        
        if min_val is not None:
            result = max(min_val, result)
        if max_val is not None:
            result = min(max_val, result)
        if decimals is not None:
            result = round(result, decimals)
        
        return result
    
    def _normalize_string(
        self,
        value: Any,
        default: str = "",
        uppercase: bool = False,
        strip: bool = True
    ) -> str:
        """
        Normalize to string with optional transformations.
        """
        if value is None:
            return default
        
        result = str(value)
        if strip:
            result = result.strip()
        if uppercase:
            result = result.upper()
        
        return result if result else default
    
    def _normalize_list(
        self,
        value: Any,
        default: List = None
    ) -> List:
        """
        Normalize to list.
        """
        if default is None:
            default = []
        
        if value is None:
            return default
        
        if isinstance(value, list):
            return value
        
        if isinstance(value, (tuple, set)):
            return list(value)
        
        # Single value becomes single-element list
        return [value]
    
    def _parse_date(
        self,
        value: Any,
        default: Optional[date] = None
    ) -> Optional[date]:
        """
        Parse various date formats to date object.
        
        Handles:
            - date objects
            - datetime objects  
            - ISO format strings (YYYY-MM-DD)
            - Common string formats
        
        Returns:
            Parsed date or default if parsing fails
        """
        if value is None:
            return default
        
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, date):
            return value
        
        if isinstance(value, str):
            # Try ISO format first
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00')).date()
            except ValueError:
                pass
            
            # Try date-only ISO
            try:
                return datetime.strptime(value[:10], "%Y-%m-%d").date()
            except ValueError:
                pass
        
        return default
    
    def _calculate_years_since(
        self,
        date_value: Any,
        reference_date: Optional[date] = None
    ) -> int:
        """
        Calculate years elapsed since a date.
        
        Args:
            date_value: The historical date (various formats accepted)
            reference_date: Reference date (default: today)
        
        Returns:
            Number of complete years, or 0 if date is invalid/future
        """
        parsed = self._parse_date(date_value)
        if parsed is None:
            return 0
        
        if reference_date is None:
            reference_date = date.today()
        
        if parsed > reference_date:
            return 0
        
        years = reference_date.year - parsed.year
        
        # Adjust if birthday hasn't occurred this year
        if (reference_date.month, reference_date.day) < (parsed.month, parsed.day):
            years -= 1
        
        return max(0, years)
    
    def _calculate_days_since(
        self,
        date_value: Any,
        reference_date: Optional[date] = None
    ) -> int:
        """Calculate days elapsed since a date."""
        parsed = self._parse_date(date_value)
        if parsed is None:
            return 0
        
        if reference_date is None:
            reference_date = date.today()
        
        delta = reference_date - parsed
        return max(0, delta.days)
    
    def _map_to_tier(
        self,
        value: Any,
        tiers: Dict[Any, int],
        default: int = 0
    ) -> int:
        """
        Map a value to a numeric tier using a mapping dict.
        
        Args:
            value: The value to map
            tiers: Dict mapping values to tier numbers
            default: Default tier if value not in mapping
        
        Returns:
            Tier number
        """
        if value is None:
            return default
        
        # Try exact match first
        if value in tiers:
            return tiers[value]
        
        # Try uppercase string match
        if isinstance(value, str):
            upper = value.upper()
            if upper in tiers:
                return tiers[upper]
        
        return default
    
    def _count_occurrences(
        self,
        items: List[Dict],
        field: str,
        value: Any
    ) -> int:
        """Count items in a list where field equals value."""
        if not items:
            return 0
        return sum(1 for item in items if item.get(field) == value)
    
    def _sum_field(
        self,
        items: List[Dict],
        field: str,
        default: float = 0.0
    ) -> float:
        """Sum a numeric field across a list of dicts."""
        if not items:
            return default
        
        total = 0.0
        for item in items:
            val = item.get(field)
            if val is not None:
                try:
                    total += float(val)
                except (ValueError, TypeError):
                    pass
        
        return total
    
    def _average_field(
        self,
        items: List[Dict],
        field: str,
        default: float = 0.0
    ) -> float:
        """Calculate average of a numeric field across a list of dicts."""
        if not items:
            return default
        
        values = []
        for item in items:
            val = item.get(field)
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
        
        if not values:
            return default
        
        return sum(values) / len(values)
    
    def _validate_required_fields(
        self,
        data: Dict[str, Any],
        required: List[str]
    ) -> List[str]:
        """
        Check for required fields and return list of missing ones.
        
        Returns:
            List of missing field names (empty if all present)
        """
        missing = []
        for field in required:
            if field not in data or data[field] is None:
                missing.append(field)
        return missing
    
    def _add_warning_if(
        self,
        condition: bool,
        message: str,
        warnings: List[str]
    ) -> None:
        """Add a warning message if condition is true."""
        if condition:
            warnings.append(message)
    
    def _safe_get(
        self,
        data: Dict[str, Any],
        *keys: str,
        default: Any = None
    ) -> Any:
        """
        Safely navigate nested dictionaries.
        
        Args:
            data: The dictionary to navigate
            *keys: Sequence of keys to traverse
            default: Value to return if path doesn't exist
        
        Returns:
            The value at the path, or default if not found
        
        Example:
            value = self._safe_get(data, "response", "items", 0, "name")
        """
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, default)
                if current is default:
                    return default
            elif isinstance(current, (list, tuple)) and isinstance(key, int):
                try:
                    current = current[key]
                except IndexError:
                    return default
            else:
                return default
        return current
