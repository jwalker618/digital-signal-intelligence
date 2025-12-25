"""
Aerospace Aggregators - Safety Record Signal Group

Aggregators for safety record signals that assess historical safety performance.

Signals:
- accident_history: Hull loss and major accidents
- incident_history: Serious incidents and near-misses
- accident_rate: Accidents per million departures vs industry
- fatality_history: Fatal accident history
- investigation_findings: Operator cited as causal factor
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


class AviationSafetyAggregator(ProductionAggregator):
    """
    Transforms aviation safety database data into multiple signal metrics.
    
    This aggregator produces data for multiple signals from a single
    extractor (AviationSafetyDatabaseExtractor), as all safety metrics
    come from the same data source.
    
    Expected input (from AviationSafetyDatabaseExtractor):
        {
            "data": {
                "total_accidents": int,
                "accidents": [{category, fatalities, hull_loss, operator_cited}, ...],
                "fatal_accidents": int,
                "total_fatalities": int,
                "hull_losses": int,
                "total_incidents": int,
                "incidents": [{severity, ...}, ...],
                "serious_incidents": int,
                "accident_rate_per_million_departures": float,
                "industry_average_rate": float,
                "rate_vs_industry": float,
                "operator_cited_count": int,
            }
        }
    
    Output:
        Full normalized safety data for all 5 safety signals.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No safety data available")
        
        # Extract raw values
        total_accidents = self._normalize_int(raw.get("total_accidents"), 0)
        fatal_accidents = self._normalize_int(raw.get("fatal_accidents"), 0)
        total_fatalities = self._normalize_int(raw.get("total_fatalities"), 0)
        hull_losses = self._normalize_int(raw.get("hull_losses"), 0)
        
        total_incidents = self._normalize_int(raw.get("total_incidents"), 0)
        serious_incidents = self._normalize_int(raw.get("serious_incidents"), 0)
        
        accident_rate = self._normalize_float(raw.get("accident_rate_per_million_departures"), 0)
        industry_rate = self._normalize_float(raw.get("industry_average_rate"), 0.18)
        rate_vs_industry = self._normalize_float(raw.get("rate_vs_industry"), 1.0)
        
        operator_cited = self._normalize_int(raw.get("operator_cited_count"), 0)
        
        # Calculate scores for each signal
        
        # 1. Accident History Score (0-100, higher = safer)
        accident_score = 100
        if hull_losses > 0:
            accident_score -= hull_losses * 25  # Major penalty for hull losses
        accident_score -= total_accidents * 10
        accident_score = max(0, accident_score)
        
        # 2. Incident History Score
        incident_score = 100
        incident_score -= serious_incidents * 8
        incident_score -= (total_incidents - serious_incidents) * 2
        incident_score = max(0, incident_score)
        
        # 3. Accident Rate Score (vs industry)
        if rate_vs_industry == 0 or accident_rate == 0:
            rate_score = 100  # No accidents
        elif rate_vs_industry <= 0.5:
            rate_score = 95  # Well below industry
        elif rate_vs_industry <= 0.8:
            rate_score = 85
        elif rate_vs_industry <= 1.0:
            rate_score = 75
        elif rate_vs_industry <= 1.5:
            rate_score = 55
        elif rate_vs_industry <= 2.0:
            rate_score = 40
        else:
            rate_score = 20  # Well above industry
        
        # 4. Fatality History Score
        if fatal_accidents == 0:
            fatality_score = 100
        elif fatal_accidents == 1 and total_fatalities <= 5:
            fatality_score = 50  # Single minor fatal
        elif fatal_accidents == 1:
            fatality_score = 35
        else:
            fatality_score = max(0, 50 - fatal_accidents * 20)
        
        # 5. Investigation Findings Score
        if total_accidents == 0:
            investigation_score = 100
        elif operator_cited == 0:
            investigation_score = 85  # Accidents but not at fault
        else:
            # Ratio of cited to total accidents
            cited_ratio = operator_cited / total_accidents
            investigation_score = max(0, 100 - cited_ratio * 60 - operator_cited * 10)
        
        return self._create_success_result({
            # Raw counts
            "total_accidents": total_accidents,
            "fatal_accidents": fatal_accidents,
            "total_fatalities": total_fatalities,
            "hull_losses": hull_losses,
            "total_incidents": total_incidents,
            "serious_incidents": serious_incidents,
            "operator_cited_count": operator_cited,
            
            # Rate metrics
            "accident_rate": round(accident_rate, 4),
            "industry_average_rate": industry_rate,
            "rate_vs_industry": round(rate_vs_industry, 2),
            
            # Signal scores (0-100)
            "accident_history_score": round(accident_score, 1),
            "incident_history_score": round(incident_score, 1),
            "accident_rate_score": round(rate_score, 1),
            "fatality_history_score": round(fatality_score, 1),
            "investigation_findings_score": round(investigation_score, 1),
            
            # Flags
            "has_hull_loss": hull_losses > 0,
            "has_fatalities": fatal_accidents > 0,
            "above_industry_rate": rate_vs_industry > 1.0,
            "clean_record": total_accidents == 0 and serious_incidents == 0,
        }, extractor_results, warnings)


# Individual aggregators that can use subsets of the data

class AccidentHistoryAggregator(ProductionAggregator):
    """
    Focused aggregator for accident_history signal only.
    Can use either AviationSafetyAggregator output or raw extractor data.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No accident data available")
        
        total_accidents = self._normalize_int(raw.get("total_accidents"), 0)
        hull_losses = self._normalize_int(raw.get("hull_losses"), 0)
        
        # Score calculation
        score = 100
        score -= hull_losses * 25
        score -= total_accidents * 10
        
        return self._create_success_result({
            "total_accidents": total_accidents,
            "hull_losses": hull_losses,
            "accident_history_score": max(0, round(score, 1)),
            "has_hull_loss": hull_losses > 0,
        }, extractor_results, warnings)


class IncidentHistoryAggregator(ProductionAggregator):
    """Focused aggregator for incident_history signal."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No incident data available")
        
        total_incidents = self._normalize_int(raw.get("total_incidents"), 0)
        serious_incidents = self._normalize_int(raw.get("serious_incidents"), 0)
        
        score = 100
        score -= serious_incidents * 8
        score -= (total_incidents - serious_incidents) * 2
        
        return self._create_success_result({
            "total_incidents": total_incidents,
            "serious_incidents": serious_incidents,
            "incident_history_score": max(0, round(score, 1)),
        }, extractor_results, warnings)


class AccidentRateAggregator(ProductionAggregator):
    """Focused aggregator for accident_rate signal."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No rate data available")
        
        accident_rate = self._normalize_float(raw.get("accident_rate_per_million_departures"), 0)
        industry_rate = self._normalize_float(raw.get("industry_average_rate"), 0.18)
        rate_vs_industry = self._normalize_float(raw.get("rate_vs_industry"), 1.0)
        
        if rate_vs_industry == 0 or accident_rate == 0:
            score = 100
        elif rate_vs_industry <= 0.5:
            score = 95
        elif rate_vs_industry <= 0.8:
            score = 85
        elif rate_vs_industry <= 1.0:
            score = 75
        elif rate_vs_industry <= 1.5:
            score = 55
        elif rate_vs_industry <= 2.0:
            score = 40
        else:
            score = 20
        
        return self._create_success_result({
            "accident_rate": round(accident_rate, 4),
            "industry_rate": industry_rate,
            "rate_vs_industry": round(rate_vs_industry, 2),
            "accident_rate_score": score,
            "above_industry": rate_vs_industry > 1.0,
        }, extractor_results, warnings)


class FatalityHistoryAggregator(ProductionAggregator):
    """Focused aggregator for fatality_history signal."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No fatality data available")
        
        fatal_accidents = self._normalize_int(raw.get("fatal_accidents"), 0)
        total_fatalities = self._normalize_int(raw.get("total_fatalities"), 0)
        
        if fatal_accidents == 0:
            score = 100
        elif fatal_accidents == 1 and total_fatalities <= 5:
            score = 50
        elif fatal_accidents == 1:
            score = 35
        else:
            score = max(0, 50 - fatal_accidents * 20)
        
        return self._create_success_result({
            "fatal_accidents": fatal_accidents,
            "total_fatalities": total_fatalities,
            "fatality_history_score": score,
            "has_fatalities": fatal_accidents > 0,
        }, extractor_results, warnings)


class InvestigationFindingsAggregator(ProductionAggregator):
    """Focused aggregator for investigation_findings signal."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No investigation data available")
        
        total_accidents = self._normalize_int(raw.get("total_accidents"), 0)
        operator_cited = self._normalize_int(raw.get("operator_cited_count"), 0)
        
        if total_accidents == 0:
            score = 100
        elif operator_cited == 0:
            score = 85
        else:
            cited_ratio = operator_cited / total_accidents
            score = max(0, 100 - cited_ratio * 60 - operator_cited * 10)
        
        return self._create_success_result({
            "total_accidents": total_accidents,
            "operator_cited": operator_cited,
            "cited_ratio": round(operator_cited / total_accidents, 2) if total_accidents > 0 else 0,
            "investigation_findings_score": round(score, 1),
        }, extractor_results, warnings)
