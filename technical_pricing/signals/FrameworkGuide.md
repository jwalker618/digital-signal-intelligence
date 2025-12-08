# Data Processing Framework Guide

## Overview

This framework provides a flexible, three-stage pipeline for extracting, analyzing, and categorizing data from various sources. It's designed to be extensible and parallelizable, making it suitable for processing data from multiple sources with consistent analysis methodologies.

## Architecture

The framework follows a clear three-stage architecture:

```
┌─────────────┐
│  EXTRACTOR  │  Stage 1: Extract raw data from source
└──────┬──────┘
       │ Raw Data
       ▼
┌─────────────┐
│ AGGREGATORS │  Stage 2: Transform & analyze raw data (parallel)
└──────┬──────┘
       │ Aggregated Data
       ▼
┌─────────────┐
│CATEGORIZERS │  Stage 3: Classify & score (parallel)
└──────┬──────┘
       │
       ▼
   [Results]
```

### Stage 1: Extractors (Data Sources)

**Purpose**: Pull raw data from various sources (APIs, databases, files, etc.)

**Base Class**: `DataExtractor`

**Key Method**: `extract() -> Dict[str, Any]`

**Example Use Cases**:
- API calls (REST, GraphQL, SOAP)
- Database queries
- File reading (CSV, JSON, XML)
- Web scraping
- Real-time data streams

**Implementation Pattern**:
```python
@register_extractor
class MyAPIExtractor(DataExtractor):
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint
    
    def extract(self) -> Dict[str, Any]:
        # Make API call, fetch data
        raw_data = self._call_api()
        return {
            "source": "my_api",
            "timestamp": datetime.now(),
            "data": raw_data
        }
    
    def get_source_metadata(self) -> Dict[str, str]:
        return {
            "extractor_type": self.__class__.__name__,
            "source": self.endpoint
        }
```

### Stage 2: Aggregators (Data Transformation & Analysis)

**Purpose**: Transform raw extracted data into standardized, analyzed output

**Base Class**: `DataAggregator`

**Key Method**: `aggregate(raw_data: Dict[str, Any]) -> Dict[str, Any]`

**Key Characteristics**:
- Multiple aggregators can run in parallel
- Each aggregator focuses on a specific aspect of analysis
- Outputs are merged for use by categorizers

**Example Use Cases**:
- Statistical calculations (averages, totals, distributions)
- Data normalization and standardization
- Derived metric calculation
- Time series analysis
- Pattern detection

**Implementation Pattern**:
```python
@register_aggregator
class StatisticalAggregator(DataAggregator):
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        items = raw_data.get("items", [])
        
        return {
            "total_count": len(items),
            "average_value": sum(i["value"] for i in items) / len(items),
            "distribution": self._calculate_distribution(items),
            "trends": self._analyze_trends(items)
        }
```

### Stage 3: Categorizers (Classification & Scoring)

**Purpose**: Take aggregated data and produce classifications, scores, or categories

**Base Class**: `DataCategorizer`

**Key Method**: `categorize(aggregated_data: Dict[str, Any]) -> Dict[str, Any]`

**Key Characteristics**:
- Multiple categorizers can run in parallel
- Each categorizer performs independent classification/scoring
- Can be parameterized for different thresholds/rules

**Example Use Cases**:
- Business rule classification
- Risk scoring
- Quality assessment
- Tier/level assignment
- ML model predictions

**Implementation Pattern**:
```python
@register_categorizer
class RiskScorer(DataCategorizer):
    def __init__(self, high_risk_threshold: int = 70):
        self.high_risk_threshold = high_risk_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        risk_score = self._calculate_risk(aggregated_data)
        
        if risk_score >= self.high_risk_threshold:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "factors": self._get_risk_factors(aggregated_data)
        }
```

## Pipeline Classes

### AnalysisPipeline

Single extractor with multiple aggregators and categorizers.

```python
pipeline = AnalysisPipeline(
    extractor=my_extractor,
    aggregators=[agg1, agg2, agg3],
    categorizers=[cat1, cat2, cat3],
    max_workers=4
)

results = pipeline.run()
```

**Output Structure**:
```python
{
    "pipeline_metadata": {
        "company_name": "...",
        "total_duration_sec": 0.123,
        "extract_duration_sec": 0.045,
        "extractor": "MyExtractor",
        "timestamp": "2024-12-08 10:30:00"
    },
    "raw_data": {...},  # Original extracted data
    "aggregation_results": {
        "Aggregator1Name": {
            "aggregator": "Aggregator1Name",
            "duration_sec": 0.012,
            "output": {...}
        },
        ...
    },
    "categorization_results": {
        "Categorizer1Name": {
            "categorizer": "Categorizer1Name",
            "params": {...},
            "duration_sec": 0.008,
            "output": {...}
        },
        ...
    }
}
```

### BatchPipeline

Multiple extractors through the same aggregation/categorization pipeline.

```python
batch = BatchPipeline(
    extractors=[extractor1, extractor2, extractor3],
    aggregators=[agg1, agg2],
    categorizers=[cat1, cat2],
    max_workers=4
)

all_results = batch.run()
summary = batch.get_summary(all_results, categorizer_name="PrimaryCategorizerName")
```

## Registry System

The framework includes a registry system for easy component discovery and dynamic loading:

```python
# Registration happens automatically with decorators
@register_extractor
class MyExtractor(DataExtractor):
    pass

# Access registered components
all_extractors = EXTRACTOR_REGISTRY
all_aggregators = AGGREGATOR_REGISTRY
all_categorizers = CATEGORIZER_REGISTRY
```

## Example: Maritime Domain Implementation

The included example demonstrates analyzing shipping companies:

### Extractors
- **EquasisAPIExtractor**: Simulates vessel data from maritime API

### Aggregators
- **FleetAggregator**: Calculates fleet statistics (size, category distribution, dominant type)
- **ServiceCapabilityAggregator**: Analyzes operational capabilities

### Categorizers
- **CompanySizeCategorizer**: Classifies by fleet size (small/medium/large/major)
- **OperatorTypeCategorizer**: Determines operator type (liner/tanker/specialized/diversified)
- **FleetModernityScorer**: Scores fleet based on average age
- **RiskProfileCategorizer**: Assesses risk based on multiple factors

## Adding New Components

### 1. Create a New Extractor

```python
@register_extractor
class DatabaseExtractor(DataExtractor):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def extract(self) -> Dict[str, Any]:
        # Connect to database and query
        conn = self._connect()
        data = conn.query("SELECT * FROM my_table")
        return {
            "source": "database",
            "records": data
        }
```

### 2. Create a New Aggregator

```python
@register_aggregator
class TimeSeriesAggregator(DataAggregator):
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        records = raw_data.get("records", [])
        
        return {
            "time_series_data": self._process_time_series(records),
            "moving_average": self._calculate_moving_average(records),
            "trend_direction": self._detect_trend(records)
        }
```

### 3. Create a New Categorizer

```python
@register_categorizer
class PerformanceTierCategorizer(DataCategorizer):
    def __init__(self, gold_threshold: int = 90, silver_threshold: int = 70):
        self.gold_threshold = gold_threshold
        self.silver_threshold = silver_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        score = aggregated_data.get("performance_score", 0)
        
        if score >= self.gold_threshold:
            tier = "gold"
        elif score >= self.silver_threshold:
            tier = "silver"
        else:
            tier = "bronze"
        
        return {
            "tier": tier,
            "score": score,
            "next_tier_gap": self._calculate_gap(score)
        }
```

## Best Practices

### 1. Single Responsibility
- Each aggregator should focus on one aspect of analysis
- Each categorizer should perform one type of classification/scoring

### 2. Data Flow
- Extractors return raw, unprocessed data
- Aggregators standardize and analyze
- Categorizers make decisions based on aggregated data

### 3. Parameterization
- Use `__init__` parameters for configurable thresholds and rules
- Makes components reusable across different contexts

### 4. Error Handling
- The pipeline automatically catches and logs exceptions
- Failed components won't crash the entire pipeline

### 5. Parallel Execution
- Aggregators run in parallel (independent of each other)
- Categorizers run in parallel (all use same merged aggregated data)
- Use `max_workers` parameter to control parallelism

### 6. Metadata
- Implement `get_source_metadata()`, `get_aggregator_metadata()`, `get_categorizer_metadata()`
- Helps with debugging and understanding data provenance

## Performance Considerations

1. **Parallelization**: Stages 2 and 3 run in parallel within their stage
2. **Timing**: Each component's execution time is tracked
3. **Thread Pool**: Configurable worker count for I/O-bound operations
4. **Memory**: Raw data and all intermediate results are kept in memory

## Extension Points

### Custom Pipeline Logic
Extend `AnalysisPipeline` to add custom behavior:

```python
class CustomPipeline(AnalysisPipeline):
    def run(self) -> Dict[str, Any]:
        results = super().run()
        
        # Add custom post-processing
        results["custom_metric"] = self._calculate_custom_metric(results)
        
        return results
```

### Dynamic Component Loading
Use the registries to load components dynamically:

```python
def create_pipeline_from_config(config: Dict) -> AnalysisPipeline:
    extractor_cls = EXTRACTOR_REGISTRY[config["extractor"]["type"]]
    extractor = extractor_cls(**config["extractor"]["params"])
    
    aggregators = [
        AGGREGATOR_REGISTRY[agg["type"]](**agg.get("params", {}))
        for agg in config["aggregators"]
    ]
    
    categorizers = [
        CATEGORIZER_REGISTRY[cat["type"]](**cat.get("params", {}))
        for cat in config["categorizers"]
    ]
    
    return AnalysisPipeline(extractor, aggregators, categorizers)
```

## Common Use Cases

### 1. Financial Analysis
- **Extractors**: Market data APIs, financial statements
- **Aggregators**: Financial ratio calculations, trend analysis
- **Categorizers**: Credit rating, investment grade classification

### 2. Supply Chain
- **Extractors**: Inventory systems, supplier databases
- **Aggregators**: Lead time analysis, cost aggregation
- **Categorizers**: Supplier tier classification, risk assessment

### 3. Customer Analytics
- **Extractors**: CRM systems, transaction logs
- **Aggregators**: Behavior analysis, lifetime value calculation
- **Categorizers**: Customer segmentation, churn prediction

### 4. Quality Control
- **Extractors**: IoT sensors, inspection logs
- **Aggregators**: Statistical process control metrics
- **Categorizers**: Quality grade assignment, defect classification

## Summary

This framework provides:
- ✅ Clear separation of concerns (extract, analyze, classify)
- ✅ Parallel execution for performance
- ✅ Easy extensibility through base classes and registries
- ✅ Comprehensive result tracking and timing
- ✅ Type-safe interfaces with abstract base classes
- ✅ Batch processing capabilities
- ✅ Flexible parameterization

The architecture scales from simple single-source analysis to complex multi-source, multi-dimensional classification systems.
