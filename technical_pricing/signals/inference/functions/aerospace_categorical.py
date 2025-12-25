"""
Aerospace Inference Functions - Categorical Groups

These inference functions determine categorical classifications for aerospace operators.
Each function orchestrates: Extractor → Aggregator → Categorizer → Category Result

Categorical Groups:
- operator_type: Type of aviation operator (MAJOR_AIRLINE, REGIONAL, etc.)
- fleet_category: Primary aircraft category (WIDEBODY, NARROWBODY, etc.)
- fleet_size: Fleet size category (SINGLE, MICRO, SMALL, MEDIUM, LARGE, MAJOR)
- regulatory_framework: Primary regulatory authority (FAA, EASA, etc.)
- iosa_status: IOSA registration status (REGISTERED, EXPIRED, NEVER_REGISTERED, NOT_APPLICABLE)
"""

import time
from typing import Dict, Any, Optional

from ...types import SignalResult, InferenceContext
from ...inference.registry import register_inference_function
from ...extractors.stubs.aerospace import (
    FleetRegistryExtractor,
    OperatingCertificateExtractor,
    IOSARegistryExtractor,
    AirlineAllianceExtractor,
)
from ...aggregators.implementations.aerospace import (
    FleetQualityAggregator,
    CertificateStatusAggregator,
    IOSAAuditAggregator,
    AllianceMembershipAggregator,
)
from ...categorizers.types.category_mapper import (
    RangeCategorizer,
    DirectMappingCategorizer,
    CategoryMapperCategorizer,
)


@register_inference_function("operatortype_basefunction")
def operatortype_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for operator_type categorical group.
    
    Determines operator classification based on:
    - Fleet size and composition
    - Alliance membership
    - Operating certificate type
    
    Categories: MAJOR_AIRLINE, REGIONAL_AIRLINE, LOW_COST_CARRIER, CARGO_AIRLINE,
                CHARTER_OPERATOR, CORPORATE_FLIGHT, HELICOPTER_OPERATOR, 
                FLIGHT_SCHOOL, PRIVATE_OWNER
    """
    start_time = time.time()
    
    try:
        # Extract fleet data
        fleet_ext = FleetRegistryExtractor()
        fleet_result = fleet_ext.extract(entity_id, context=context)
        
        # Extract alliance data  
        alliance_ext = AirlineAllianceExtractor()
        alliance_result = alliance_ext.extract(entity_id, context=context)
        
        # Extract certificate data
        cert_ext = OperatingCertificateExtractor()
        cert_result = cert_ext.extract(entity_id, context=context)
        
        if not fleet_result.success:
            return SignalResult(
                signal_id="operator_type",
                category="CHARTER_OPERATOR",  # Default fallback
                confidence=0.3,
                error="Fleet data unavailable"
            )
        
        # Aggregate
        fleet_agg = FleetQualityAggregator()
        fleet_data = fleet_agg.aggregate([fleet_result])
        
        alliance_data = None
        if alliance_result.success:
            alliance_agg = AllianceMembershipAggregator()
            alliance_data = alliance_agg.aggregate([alliance_result])
        
        # Build classification input
        fleet_size = fleet_data.data.get("fleet_size", 1)
        primary_category = fleet_result.data.get("data", {}).get("primary_category", "NARROWBODY")
        has_alliance = alliance_data.data.get("has_alliance", False) if alliance_data else False
        
        # Classification logic
        if primary_category == "HELICOPTER":
            category = "HELICOPTER_OPERATOR"
        elif primary_category == "PISTON":
            if fleet_size <= 5:
                category = "FLIGHT_SCHOOL"
            else:
                category = "PRIVATE_OWNER"
        elif primary_category == "BUSINESS_JET":
            category = "CORPORATE_FLIGHT"
        elif fleet_size >= 100 and has_alliance:
            category = "MAJOR_AIRLINE"
        elif fleet_size >= 50:
            if has_alliance:
                category = "MAJOR_AIRLINE"
            else:
                category = "LOW_COST_CARRIER"
        elif fleet_size >= 20:
            category = "REGIONAL_AIRLINE"
        elif fleet_size >= 5:
            category = "CHARTER_OPERATOR"
        else:
            category = "PRIVATE_OWNER"
        
        execution_time = (time.time() - start_time) * 1000
        
        return SignalResult(
            signal_id="operator_type",
            category=category,
            confidence=0.85,
            execution_time_ms=execution_time,
            raw_data={
                "fleet_size": fleet_size,
                "primary_category": primary_category,
                "has_alliance": has_alliance,
            },
            aggregated_data=fleet_data.data,
            metadata={
                "categorizer": "rule_based",
                "extractors": ["FleetRegistryExtractor", "AirlineAllianceExtractor"],
            }
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="operator_type",
            category="CHARTER_OPERATOR",
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("fleetcategory_basefunction")
def fleetcategory_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for fleet_category categorical group.
    
    Categories: WIDEBODY, NARROWBODY, REGIONAL_JET, TURBOPROP, 
                BUSINESS_JET, HELICOPTER, PISTON
    """
    start_time = time.time()
    
    try:
        # Extract
        extractor = FleetRegistryExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="fleet_category",
                category="NARROWBODY",
                confidence=0.3,
                error="Fleet data unavailable"
            )
        
        # Get primary category directly from extractor
        primary_category = extract_result.data.get("data", {}).get("primary_category", "NARROWBODY")
        
        # Direct mapping - category names match
        categorizer = DirectMappingCategorizer()
        cat_result = categorizer.categorize(
            {"primary_category": primary_category},
            params={
                "value_field": "primary_category",
                "mapping": {
                    "WIDEBODY": "WIDEBODY",
                    "NARROWBODY": "NARROWBODY",
                    "REGIONAL_JET": "REGIONAL_JET",
                    "TURBOPROP": "TURBOPROP",
                    "BUSINESS_JET": "BUSINESS_JET",
                    "HELICOPTER": "HELICOPTER",
                    "PISTON": "PISTON",
                },
                "default_category": "NARROWBODY"
            }
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        return SignalResult(
            signal_id="fleet_category",
            category=cat_result.category,
            confidence=cat_result.confidence or 1.0,
            execution_time_ms=execution_time,
            raw_data=extract_result.data,
            metadata={
                "categorizer": "DirectMappingCategorizer",
                "from_cache": extract_result.from_cache,
            }
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="fleet_category",
            category="NARROWBODY",
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("fleetsize_basefunction")
def fleetsize_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for fleet_size categorical group.
    
    Categories: SINGLE (1), MICRO (2-5), SMALL (6-20), MEDIUM (21-50), 
                LARGE (51-150), MAJOR (150+)
    """
    start_time = time.time()
    
    try:
        # Extract
        extractor = FleetRegistryExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="fleet_size",
                category="SMALL",
                confidence=0.3,
                error="Fleet data unavailable"
            )
        
        fleet_size = extract_result.data.get("data", {}).get("fleet_size", 1)
        
        # Range-based categorization
        categorizer = RangeCategorizer()
        cat_result = categorizer.categorize(
            {"fleet_size": fleet_size},
            params={
                "value_field": "fleet_size",
                "ranges": [
                    {"min": 150, "category": "MAJOR"},
                    {"min": 51, "max": 150, "category": "LARGE"},
                    {"min": 21, "max": 51, "category": "MEDIUM"},
                    {"min": 6, "max": 21, "category": "SMALL"},
                    {"min": 2, "max": 6, "category": "MICRO"},
                ],
                "default_category": "SINGLE"
            }
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        return SignalResult(
            signal_id="fleet_size",
            category=cat_result.category,
            confidence=cat_result.confidence or 1.0,
            execution_time_ms=execution_time,
            raw_data={"fleet_size": fleet_size},
            metadata={
                "categorizer": "RangeCategorizer",
                "from_cache": extract_result.from_cache,
            }
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="fleet_size",
            category="SMALL",
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("regulatoryframework_basefunction")
def regulatoryframework_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for regulatory_framework categorical group.
    
    Categories: FAA, EASA, CAA_UK, TCCA, CASA, CAAC, DGCA_INDIA, OTHER_ICAO, NON_ICAO
    """
    start_time = time.time()
    
    try:
        # Extract
        extractor = OperatingCertificateExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="regulatory_framework",
                category="OTHER_ICAO",
                confidence=0.3,
                error="Certificate data unavailable"
            )
        
        regulator = extract_result.data.get("data", {}).get("primary_regulator", "OTHER_ICAO")
        
        # Map regulator codes to categories
        categorizer = DirectMappingCategorizer()
        cat_result = categorizer.categorize(
            {"regulator": regulator},
            params={
                "value_field": "regulator",
                "mapping": {
                    "FAA": "FAA",
                    "EASA": "EASA",
                    "CAA_UK": "CAA_UK",
                    "TCCA": "TCCA",
                    "CASA": "CASA",
                    "CAAC": "CAAC",
                    "DGCA_IN": "DGCA_INDIA",
                    "ANAC": "OTHER_ICAO",
                    "OTHER_ICAO": "OTHER_ICAO",
                },
                "default_category": "OTHER_ICAO"
            }
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        return SignalResult(
            signal_id="regulatory_framework",
            category=cat_result.category,
            confidence=cat_result.confidence or 1.0,
            execution_time_ms=execution_time,
            raw_data={"regulator": regulator},
            metadata={
                "categorizer": "DirectMappingCategorizer",
                "from_cache": extract_result.from_cache,
            }
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="regulatory_framework",
            category="OTHER_ICAO",
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("iosastatus_basefunction")
def iosastatus_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for iosa_status categorical group.
    
    Categories: REGISTERED, EXPIRED, NEVER_REGISTERED, NOT_APPLICABLE
    """
    start_time = time.time()
    
    try:
        # Extract
        extractor = IOSARegistryExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="iosa_status",
                category="NEVER_REGISTERED",
                confidence=0.3,
                error="IOSA data unavailable"
            )
        
        status = extract_result.data.get("data", {}).get("registration_status", "NEVER_REGISTERED")
        applicable = extract_result.data.get("data", {}).get("applicable", True)
        
        # Determine category
        if status == "REGISTERED":
            category = "REGISTERED"
        elif status == "EXPIRED":
            category = "EXPIRED"
        elif not applicable:
            category = "NOT_APPLICABLE"
        else:
            category = "NEVER_REGISTERED"
        
        execution_time = (time.time() - start_time) * 1000
        
        return SignalResult(
            signal_id="iosa_status",
            category=category,
            confidence=1.0,
            execution_time_ms=execution_time,
            raw_data={"status": status, "applicable": applicable},
            metadata={
                "categorizer": "rule_based",
                "from_cache": extract_result.from_cache,
            }
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="iosa_status",
            category="NEVER_REGISTERED",
            confidence=0.0,
            error=str(e)
        )
