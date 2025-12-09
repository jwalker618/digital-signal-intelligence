from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Type, Optional

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ----------------------------
# Registries
# ----------------------------
EXTRACTOR_REGISTRY: Dict[str, Type["DataExtractor"]] = {}
AGGREGATOR_REGISTRY: Dict[str, Type["DataAggregator"]] = {}
CATEGORIZER_REGISTRY: Dict[str, Type["DataCategorizer"]] = {}

def register_extractor(cls: Type["DataExtractor"]) -> Type["DataExtractor"]:
    """Register a data extractor (source) class."""
    EXTRACTOR_REGISTRY[cls.__name__] = cls
    return cls

def register_aggregator(cls: Type["DataAggregator"]) -> Type["DataAggregator"]:
    """Register a data aggregator/analyzer class."""
    AGGREGATOR_REGISTRY[cls.__name__] = cls
    return cls

def register_categorizer(cls: Type["DataCategorizer"]) -> Type["DataCategorizer"]:
    """Register a data categorizer/scorer class."""
    CATEGORIZER_REGISTRY[cls.__name__] = cls
    return cls


# ----------------------------
# Base Classes
# ----------------------------
class DataExtractor(ABC):
    """
    Base class for data extractors (sources).
    Extracts raw data from various sources (API, database, file, etc.)
    """
    @abstractmethod
    def extract(self) -> Dict[str, Any]:
        """Extract raw data from the source."""
        raise NotImplementedError
    
    def get_source_metadata(self) -> Dict[str, str]:
        """Optional: Return metadata about the data source."""
        return {
            "extractor_type": self.__class__.__name__,
            "source": "unknown"
        }


class DataAggregator(ABC):
    """
    Base class for data aggregators/analyzers.
    Transforms raw extracted data into standardized, analyzed output.
    """
    @abstractmethod
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform and analyze raw data.
        
        Args:
            raw_data: Raw data from an extractor
            
        Returns:
            Standardized, aggregated/analyzed data
        """
        raise NotImplementedError
    
    def get_aggregator_metadata(self) -> Dict[str, str]:
        """Optional: Return metadata about the aggregator."""
        return {
            "aggregator_type": self.__class__.__name__,
            "version": "1.0"
        }


class DataCategorizer(ABC):
    """
    Base class for data categorizers/scorers.
    Takes aggregated data and produces classifications, scores, or categories.
    """
    @abstractmethod
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize or score the aggregated data.
        
        Args:
            aggregated_data: Standardized data from an aggregator
            
        Returns:
            Category, score, or classification result
        """
        raise NotImplementedError
    
    def get_categorizer_metadata(self) -> Dict[str, str]:
        """Optional: Return metadata about the categorizer."""
        return {
            "categorizer_type": self.__class__.__name__,
            "version": "1.0"
        }



# ----------------------------
# Example Implementations: Maritime Domain
# ----------------------------

# EXTRACTORS
@register_extractor
class EquasisAPIExtractor(DataExtractor):
    """
    Simulates extracting vessel data from Equasis API for a marine operator.
    Returns raw API-style payload.
    """

    def __init__(self, company_name: str, offers_liner_service: bool, fleet_spec: Dict[str, int]):
        self.company_name = company_name
        self.offers_liner_service = offers_liner_service
        self.fleet_spec = fleet_spec  # e.g., {"container": 60, "bulk": 10}

    def extract(self) -> Dict[str, Any]:
        """Simulate API call returning raw vessel data."""
        vessels: List[Dict[str, Any]] = []
        imo_seed = abs(hash(self.company_name)) % 1000000
        
        for cat, count in self.fleet_spec.items():
            for i in range(count):
                vessels.append({
                    "imo": imo_seed + i,
                    "category": cat,
                    "dwt": 50000 + (i * 1000),  # Example: deadweight tonnage
                    "year_built": 2010 + (i % 15)
                })
        
        return {
            "company_name": self.company_name,
            "offers_liner_service": self.offers_liner_service,
            "vessels": vessels,
            "data_source": "equasis_api"
        }
    
    def get_source_metadata(self) -> Dict[str, str]:
        return {
            "extractor_type": self.__class__.__name__,
            "source": "Equasis API",
            "company": self.company_name
        }


# AGGREGATORS
@register_aggregator
class FleetAggregator(DataAggregator):
    """
    Aggregates raw vessel data into standardized fleet statistics.
    Calculates totals, dominant categories, age distribution, etc.
    """
    
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw vessel data into fleet statistics."""
        vessels = raw_data.get("vessels", [])
        
        # Calculate category distribution
        category_counts: Dict[str, int] = {}
        for vessel in vessels:
            cat = vessel.get("category")
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Determine dominant category
        if not category_counts:
            dominant_category = None
            dominance_ratio = 0.0
        else:
            max_count = max(category_counts.values())
            max_cats = [c for c, n in category_counts.items() if n == max_count]
            
            if len(max_cats) == 1:
                dominant_category = max_cats[0]
                dominance_ratio = max_count / len(vessels) if vessels else 0.0
            else:
                dominant_category = "mixed"
                dominance_ratio = max_count / len(vessels) if vessels else 0.0
        
        # Calculate fleet age
        current_year = 2024
        ages = [current_year - v.get("year_built", current_year) for v in vessels if "year_built" in v]
        avg_age = sum(ages) / len(ages) if ages else 0.0
        
        # Calculate total capacity (if available)
        total_dwt = sum(v.get("dwt", 0) for v in vessels)
        
        return {
            "company_name": raw_data.get("company_name"),
            "total_vessels": len(vessels),
            "category_distribution": category_counts,
            "dominant_category": dominant_category,
            "dominance_ratio": round(dominance_ratio, 2),
            "average_fleet_age": round(avg_age, 1),
            "total_dwt": total_dwt,
            "offers_liner_service": raw_data.get("offers_liner_service", False),
            "vessels": vessels,  # Pass through for downstream use
        }


@register_aggregator
class ServiceCapabilityAggregator(DataAggregator):
    """
    Analyzes service capabilities based on vessel types and operational flags.
    """
    
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze service capabilities."""
        vessels = raw_data.get("vessels", [])
        categories = set(v.get("category") for v in vessels if v.get("category"))
        
        # Determine service capabilities
        capabilities = {
            "liner_service": raw_data.get("offers_liner_service", False),
            "container_capable": "container" in categories,
            "bulk_capable": "bulk" in categories,
            "tanker_capable": "tanker" in categories,
            "multi_modal": len(categories) > 1,
        }
        
        return {
            "company_name": raw_data.get("company_name"),
            "service_capabilities": capabilities,
            "vessel_type_count": len(categories),
            "vessel_types": list(categories),
        }



# CATEGORIZERS
@register_categorizer
class CompanySizeCategorizer(DataCategorizer):
    """
    Categorizes companies by fleet size.
    """
    
    def __init__(self, small_threshold: int = 10, medium_threshold: int = 30, large_threshold: int = 50):
        self.small_threshold = small_threshold
        self.medium_threshold = medium_threshold
        self.large_threshold = large_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize by fleet size."""
        fleet_size = aggregated_data.get("total_vessels", 0)
        
        if fleet_size < self.small_threshold:
            category = "small"
        elif fleet_size < self.medium_threshold:
            category = "medium"
        elif fleet_size < self.large_threshold:
            category = "large"
        else:
            category = "major"
        
        return {
            "company_name": aggregated_data.get("company_name"),
            "size_category": category,
            "fleet_size": fleet_size,
            "thresholds": {
                "small": f"< {self.small_threshold}",
                "medium": f"{self.small_threshold}-{self.medium_threshold-1}",
                "large": f"{self.medium_threshold}-{self.large_threshold-1}",
                "major": f">= {self.large_threshold}"
            }
        }


@register_categorizer
class OperatorTypeCategorizer(DataCategorizer):
    """
    Categorizes shipping companies by operational type:
    - Major Liner: Container-focused, large fleet, offers liner service
    - Major Tanker: Tanker-focused, medium+ fleet
    - Specialized: Single vessel type dominance
    - Diversified: Multiple vessel types with no clear dominance
    """
    
    def __init__(self, liner_fleet_threshold: int = 50, tanker_fleet_threshold: int = 30, 
                 dominance_threshold: float = 0.6):
        self.liner_fleet_threshold = liner_fleet_threshold
        self.tanker_fleet_threshold = tanker_fleet_threshold
        self.dominance_threshold = dominance_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize by operator type."""
        fleet_size = aggregated_data.get("total_vessels", 0)
        dominant_cat = aggregated_data.get("dominant_category")
        dominance_ratio = aggregated_data.get("dominance_ratio", 0.0)
        offers_liner = aggregated_data.get("offers_liner_service", False)
        
        category = "uncategorized"
        reasons: List[str] = []
        confidence = 0.0
        
        # Major Liner classification
        if (dominant_cat == "container" and 
            fleet_size >= self.liner_fleet_threshold and 
            offers_liner):
            category = "major_liner"
            confidence = min(0.9, dominance_ratio + 0.2)
            reasons = [
                f"Container dominance ({dominance_ratio:.0%})",
                f"Fleet size >= {self.liner_fleet_threshold}",
                "Offers liner service"
            ]
        
        # Major Tanker classification
        elif dominant_cat == "tanker" and fleet_size >= self.tanker_fleet_threshold:
            category = "major_tanker"
            confidence = min(0.9, dominance_ratio + 0.1)
            reasons = [
                f"Tanker dominance ({dominance_ratio:.0%})",
                f"Fleet size >= {self.tanker_fleet_threshold}"
            ]
        
        # Specialized operator
        elif dominance_ratio >= self.dominance_threshold and fleet_size >= 5:
            category = "specialized"
            confidence = dominance_ratio
            reasons = [
                f"{dominant_cat.title()} dominance ({dominance_ratio:.0%})",
                f"Above dominance threshold ({self.dominance_threshold:.0%})"
            ]
        
        # Diversified operator
        elif dominant_cat == "mixed" or dominance_ratio < self.dominance_threshold:
            category = "diversified"
            confidence = 1.0 - dominance_ratio
            reasons = [
                f"No clear vessel type dominance ({dominance_ratio:.0%})",
                "Multi-vessel portfolio"
            ]
        
        else:
            reasons = [
                f"Dominant category: {dominant_cat}",
                f"Fleet size: {fleet_size}",
                f"Liner service: {offers_liner}",
                f"Dominance ratio: {dominance_ratio:.0%}"
            ]
        
        return {
            "company_name": aggregated_data.get("company_name"),
            "operator_type": category,
            "confidence": round(confidence, 2),
            "classification_reasons": reasons,
            "supporting_data": {
                "dominant_category": dominant_cat,
                "fleet_size": fleet_size,
                "dominance_ratio": dominance_ratio,
                "offers_liner_service": offers_liner
            }
        }


@register_categorizer
class FleetModernityScorer(DataCategorizer):
    """
    Scores fleet modernity based on average age.
    """
    
    def __init__(self, modern_threshold: float = 5.0, aging_threshold: float = 15.0):
        self.modern_threshold = modern_threshold
        self.aging_threshold = aging_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score fleet modernity."""
        avg_age = aggregated_data.get("average_fleet_age", 0.0)
        
        if avg_age <= self.modern_threshold:
            rating = "modern"
            score = 100
        elif avg_age <= self.aging_threshold:
            rating = "moderate"
            # Linear interpolation
            score = int(100 - ((avg_age - self.modern_threshold) / 
                              (self.aging_threshold - self.modern_threshold)) * 50)
        else:
            rating = "aging"
            score = max(0, int(50 - (avg_age - self.aging_threshold) * 2))
        
        return {
            "company_name": aggregated_data.get("company_name"),
            "modernity_rating": rating,
            "modernity_score": score,
            "average_fleet_age": avg_age,
            "assessment": f"{rating.title()} fleet ({avg_age:.1f} years avg)"
        }


@register_categorizer
class RiskProfileCategorizer(DataCategorizer):
    """
    Assesses operational risk profile based on multiple factors.
    """
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk profile."""
        fleet_size = aggregated_data.get("total_vessels", 0)
        avg_age = aggregated_data.get("average_fleet_age", 0.0)
        dominant_cat = aggregated_data.get("dominant_category")
        dominance_ratio = aggregated_data.get("dominance_ratio", 0.0)
        
        risk_score = 0
        risk_factors: List[str] = []
        
        # Fleet size risk (smaller = higher risk)
        if fleet_size < 5:
            risk_score += 30
            risk_factors.append("Very small fleet (<5 vessels)")
        elif fleet_size < 15:
            risk_score += 15
            risk_factors.append("Small fleet (<15 vessels)")
        
        # Age risk
        if avg_age > 20:
            risk_score += 30
            risk_factors.append(f"Aging fleet ({avg_age:.1f} years)")
        elif avg_age > 15:
            risk_score += 15
            risk_factors.append(f"Moderately old fleet ({avg_age:.1f} years)")
        
        # Diversification risk
        if dominance_ratio > 0.9:
            risk_score += 20
            risk_factors.append("Highly concentrated fleet")
        elif dominance_ratio < 0.4:
            risk_score += 10
            risk_factors.append("Highly diversified (may lack focus)")
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        return {
            "company_name": aggregated_data.get("company_name"),
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors if risk_factors else ["No significant risk factors identified"],
            "recommendation": self._get_recommendation(risk_level)
        }
    
    def _get_recommendation(self, risk_level: str) -> str:
        recommendations = {
            "high": "Requires detailed due diligence and enhanced monitoring",
            "moderate": "Standard due diligence recommended",
            "low": "Suitable for streamlined review process"
        }
        return recommendations.get(risk_level, "Review required")
      



# ----------------------------
# Pipeline Architecture
# ----------------------------
class AnalysisPipeline:
    """
    Three-stage pipeline: Extract -> Aggregate -> Categorize
    
    1. Extractor: Pulls raw data from source
    2. Aggregators: Transform/analyze raw data (can run multiple in parallel)
    3. Categorizers: Classify/score aggregated data (can run multiple in parallel)
    """
    
    def __init__(
        self,
        extractor: DataExtractor,
        aggregators: List[DataAggregator],
        categorizers: List[DataCategorizer],
        max_workers: Optional[int] = None
    ):
        self.extractor = extractor
        self.aggregators = aggregators
        self.categorizers = categorizers
        self.max_workers = max_workers
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the full pipeline and return comprehensive results.
        """
        start_time = time.perf_counter()
        
        # Stage 1: Extract raw data
        logging.info(f"Stage 1: Extracting data from {self.extractor.__class__.__name__}")
        extract_start = time.perf_counter()
        raw_data = self.extractor.extract()
        extract_duration = time.perf_counter() - extract_start
        
        # Stage 2: Aggregate data (parallel)
        logging.info(f"Stage 2: Running {len(self.aggregators)} aggregator(s)")
        aggregation_results = self._run_aggregators_parallel(raw_data)
        
        # Merge aggregated data for categorizers
        merged_aggregated_data = self._merge_aggregated_data(raw_data, aggregation_results)
        
        # Stage 3: Categorize (parallel)
        logging.info(f"Stage 3: Running {len(self.categorizers)} categorizer(s)")
        categorization_results = self._run_categorizers_parallel(merged_aggregated_data)
        
        total_duration = time.perf_counter() - start_time
        
        return {
            "pipeline_metadata": {
                "company_name": raw_data.get("company_name", "unknown"),
                "total_duration_sec": round(total_duration, 3),
                "extract_duration_sec": round(extract_duration, 3),
                "extractor": self.extractor.__class__.__name__,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            },
            "raw_data": raw_data,
            "aggregation_results": aggregation_results,
            "categorization_results": categorization_results,
        }
    
    def _run_aggregators_parallel(self, raw_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Run all aggregators in parallel."""
        results: Dict[str, Dict[str, Any]] = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_aggregator = {
                executor.submit(self._run_single_aggregator, agg, raw_data): agg.__class__.__name__
                for agg in self.aggregators
            }
            
            for future in as_completed(future_to_aggregator.keys()):
                agg_name = future_to_aggregator[future]
                try:
                    results[agg_name] = future.result()
                except Exception as e:
                    logging.exception(f"Aggregator {agg_name} failed: {e}")
                    results[agg_name] = {"error": str(e)}
        
        return results
    
    def _run_categorizers_parallel(self, aggregated_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Run all categorizers in parallel."""
        results: Dict[str, Dict[str, Any]] = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_categorizer = {
                executor.submit(self._run_single_categorizer, cat, aggregated_data): cat.__class__.__name__
                for cat in self.categorizers
            }
            
            for future in as_completed(future_to_categorizer.keys()):
                cat_name = future_to_categorizer[future]
                try:
                    results[cat_name] = future.result()
                except Exception as e:
                    logging.exception(f"Categorizer {cat_name} failed: {e}")
                    results[cat_name] = {"error": str(e)}
        
        return results
    
    def _run_single_aggregator(self, aggregator: DataAggregator, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single aggregator with timing."""
        agg_name = aggregator.__class__.__name__
        start = time.perf_counter()
        logging.info(f"  Running aggregator: {agg_name}")
        
        output = aggregator.aggregate(raw_data)
        duration = time.perf_counter() - start
        
        logging.info(f"  Completed aggregator: {agg_name} in {duration:.3f}s")
        
        return {
            "aggregator": agg_name,
            "duration_sec": round(duration, 3),
            "output": output,
        }
    
    def _run_single_categorizer(self, categorizer: DataCategorizer, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single categorizer with timing."""
        cat_name = categorizer.__class__.__name__
        start = time.perf_counter()
        logging.info(f"  Running categorizer: {cat_name}")
        
        output = categorizer.categorize(aggregated_data)
        duration = time.perf_counter() - start
        
        logging.info(f"  Completed categorizer: {cat_name} in {duration:.3f}s")
        
        return {
            "categorizer": cat_name,
            "params": vars(categorizer),
            "duration_sec": round(duration, 3),
            "output": output,
        }
    
    def _merge_aggregated_data(self, raw_data: Dict[str, Any], aggregation_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge outputs from all aggregators into a single dict for categorizers.
        Includes original raw data plus all aggregated metrics.
        """
        merged = {"_raw": raw_data}
        
        for agg_name, result in aggregation_results.items():
            if "output" in result:
                merged.update(result["output"])
        
        return merged


# ----------------------------
# Convenience: Run multiple companies through the same pipeline
# ----------------------------
class BatchPipeline:
    """
    Run multiple extractors through the same aggregation/categorization pipeline.
    Useful for analyzing multiple companies with consistent methodology.
    """
    
    def __init__(
        self,
        extractors: List[DataExtractor],
        aggregators: List[DataAggregator],
        categorizers: List[DataCategorizer],
        max_workers: Optional[int] = None
    ):
        self.extractors = extractors
        self.aggregators = aggregators
        self.categorizers = categorizers
        self.max_workers = max_workers
    
    def run(self) -> List[Dict[str, Any]]:
        """Run the pipeline for each extractor and return all results."""
        all_results = []
        
        for extractor in self.extractors:
            logging.info(f"\n{'='*60}")
            logging.info(f"Processing: {extractor.get_source_metadata().get('company', 'unknown')}")
            logging.info(f"{'='*60}")
            
            pipeline = AnalysisPipeline(
                extractor=extractor,
                aggregators=self.aggregators,
                categorizers=self.categorizers,
                max_workers=self.max_workers
            )
            
            result = pipeline.run()
            all_results.append(result)
        
        return all_results
    
    def get_summary(self, results: List[Dict[str, Any]], categorizer_name: str = "OperatorTypeCategorizer") -> List[Dict[str, Any]]:
        """
        Extract a human-readable summary from batch results.
        
        Args:
            results: Output from run()
            categorizer_name: Which categorizer to use for primary classification
        """
        summary = []
        
        for result in results:
            metadata = result.get("pipeline_metadata", {})
            cat_results = result.get("categorization_results", {})
            
            primary_cat = cat_results.get(categorizer_name, {}).get("output", {})
            
            summary.append({
                "company": metadata.get("company_name"),
                "operator_type": primary_cat.get("operator_type", "unknown"),
                "confidence": primary_cat.get("confidence", 0.0),
                "all_categories": {
                    name: cat_result.get("output", {})
                    for name, cat_result in cat_results.items()
                }
            })
        
        return summary




# ----------------------------
# Demo: Maritime Company Analysis
# ----------------------------
if __name__ == "__main__":
    # Define test companies
    companies = [
        EquasisAPIExtractor(
            company_name="Atlas Container Lines",
            offers_liner_service=True,
            fleet_spec={"container": 60, "bulk": 10},
        ),
        EquasisAPIExtractor(
            company_name="Marina Tankers Ltd",
            offers_liner_service=False,
            fleet_spec={"tanker": 35, "container": 2},
        ),
        EquasisAPIExtractor(
            company_name="Ocean Mix Shipping",
            offers_liner_service=False,
            fleet_spec={"container": 20, "tanker": 25, "bulk": 5},
        ),
        EquasisAPIExtractor(
            company_name="Coastal Bulk Carriers",
            offers_liner_service=False,
            fleet_spec={"bulk": 8},
        ),
    ]
    
    # Define aggregators (data transformation/analysis)
    aggregators = [
        FleetAggregator(),
        ServiceCapabilityAggregator(),
    ]
    
    # Define categorizers (classification/scoring)
    categorizers = [
        CompanySizeCategorizer(small_threshold=10, medium_threshold=30, large_threshold=50),
        OperatorTypeCategorizer(liner_fleet_threshold=50, tanker_fleet_threshold=30),
        FleetModernityScorer(modern_threshold=5.0, aging_threshold=15.0),
        RiskProfileCategorizer(),
    ]
    
    # Run batch pipeline
    print("\n" + "="*80)
    print("MARITIME COMPANY ANALYSIS PIPELINE")
    print("="*80)
    
    batch = BatchPipeline(
        extractors=companies,
        aggregators=aggregators,
        categorizers=categorizers,
        max_workers=4
    )
    
    results = batch.run()
    
    # Generate summary
    print("\n" + "="*80)
    print("CLASSIFICATION SUMMARY")
    print("="*80)
    
    summary = batch.get_summary(results, categorizer_name="OperatorTypeCategorizer")
    
    for item in summary:
        print(f"\n{item['company']}")
        print(f"  Operator Type: {item['operator_type']} (confidence: {item['confidence']})")
        
        # Show other categories
        all_cats = item['all_categories']
        
        if 'CompanySizeCategorizer' in all_cats:
            size_data = all_cats['CompanySizeCategorizer']
            print(f"  Size Category: {size_data.get('size_category')} ({size_data.get('fleet_size')} vessels)")
        
        if 'FleetModernityScorer' in all_cats:
            mod_data = all_cats['FleetModernityScorer']
            print(f"  Fleet Modernity: {mod_data.get('modernity_rating')} (score: {mod_data.get('modernity_score')}/100)")
        
        if 'RiskProfileCategorizer' in all_cats:
            risk_data = all_cats['RiskProfileCategorizer']
            print(f"  Risk Profile: {risk_data.get('risk_level').upper()} (score: {risk_data.get('risk_score')})")
            print(f"    Recommendation: {risk_data.get('recommendation')}")
    
    # Detailed view of one company
    print("\n" + "="*80)
    print("DETAILED ANALYSIS: " + results[0]['pipeline_metadata']['company_name'])
    print("="*80)
    
    first_result = results[0]
    
    print("\n[AGGREGATION RESULTS]")
    for agg_name, agg_data in first_result['aggregation_results'].items():
        print(f"\n  {agg_name}:")
        output = agg_data.get('output', {})
        for key, value in output.items():
            if key not in ['vessels', 'company_name']:  # Skip large/duplicate data
                print(f"    {key}: {value}")
    
    print("\n[CATEGORIZATION RESULTS]")
    for cat_name, cat_data in first_result['categorization_results'].items():
        print(f"\n  {cat_name}:")
        output = cat_data.get('output', {})
        for key, value in output.items():
            if key != 'company_name':
                print(f"    {key}: {value}")
    
    print("\n" + "="*80)
    print(f"Pipeline completed in {first_result['pipeline_metadata']['total_duration_sec']}s")
    print("="*80)
