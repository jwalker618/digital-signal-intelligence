# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## Data Processing Framework: Signals

| Item | Value |
|-|-|
|Version|1.0|
|Date|November 2025|
|Classification|Technical Specification|

---

### Introduction

This framework provides a clean, scalable way to:
1. Extract data from multiple sources
2. Analyse it consistently
3. Classify/score based on business rules
4. Process multiple entities in parallel

The three-stage architecture (Extract → Aggregate → Categorise) makes it easy to understand, extend, and maintain.

### Key Features
|*|Component|Description|
|-|-|-|
|✅|**Modular Architecture**|Easy to add new components|
|✅|**Clear Seperation of Concerns**|Each component has a single, well-defined responsibility|
|✅|**Parallel Execution**|Fast processing with ThreadPoolExecutor|  
|✅|**Type Safety**|Abstract base classes enforce contracts|  
|✅|**Error Handling**|Automatic exception catching and logging|  
|✅|**Timing Metrics**|Track performance of each component|  
|✅|**Registry System**|Automatic component discovery|  
|✅|**Batch Processing**|Handle multiple sources efficiently|  
|✅|**Flexible Configuration**|Parameterizable thresholds and rules|  
|✅|**Comprehensive Logging**|Track pipeline execution|  

### Architecture

The framework follows a clear three-stage architecture:

```
┌─────────────┐
│  EXTRACTOR  │  Stage 1: Extract raw data from source
└──────┬──────┘
       │ Raw Data
       ▼
┌─────────────┐
│ AGGREGATORS │  Stage 2: Transform & analyzs raw data (parallel)
└──────┬──────┘
       │ Aggregated / Analysed Data
       ▼
┌─────────────┐
│CATEGORISERS │  Stage 3: Classify & score (parallel)
└──────┬──────┘
       │
       ▼
   [Results]
```

#### Stage 1: Extractors (Data Sources)

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

#### Stage 2: Aggregators (Data Transformation & Analysis)

**Purpose**: Transform raw extracted data into standardised, analysed output

**Base Class**: `DataAggregator`

**Key Method**: `aggregate(raw_data: Dict[str, Any]) -> Dict[str, Any]`

**Key Characteristics**:
- Multiple aggregators can run in parallel
- Each aggregator focuses on a specific aspect of analysis
- Outputs are merged for use by categorisers

**Example Use Cases**:
- Statistical calculations (averages, totals, distributions)
- Data normalisation and standardisation
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

#### Stage 3: Categorisers (Classification & Scoring)

**Purpose**: Take aggregated data and produce classifications, scores, or categories

**Base Class**: `DataCategorizer`

**Key Method**: `categorize(aggregated_data: Dict[str, Any]) -> Dict[str, Any]`

**Key Characteristics**:
- Multiple categorisers can run in parallel
- Each categoriser performs independent classification/scoring
- Can be parameterised for different thresholds/rules

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

### Pipeline Classes

#### AnalysisPipeline

Single extractor with multiple aggregators and categorisers.

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

#### BatchPipeline

Multiple extractors through the same aggregation/categorisation pipeline.

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

### Registry System

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

### Detailed Architecture Diagram

```
==============================================================================
                        DATA PROCESSING FRAMEWORK
                          ARCHITECTURE OVERVIEW
==============================================================================

┌────────────────────────────────────────────────────────────────────────────┐
│                            DATA SOURCES LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │   API    │  │ Database │  │   CSV    │  │   Web    │  │  Stream  │      │
│  │  (REST)  │  │  (SQL)   │  │  (File)  │  │ (Scrape) │  │ (Kafka)  │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼────────────┘
        │             │             │             │             │
        ▼             ▼             ▼             ▼             ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 1: EXTRACTION                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                  DataExtrctor (Abstract)                             │  │
│  │  • extract() → Dict[str, Any]                                        │  │
│  │  • get_source_metadata() → Dict[str, str]                            │  │
│  └─┬────────────────────────────────────────────────────────────────────┘  │
│    |                                                                       │
│    |─────────────┬─────────────┐                                           │
│    │             │             │                                           │
│    ▼             ▼             ▼                                           │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                                 │
│  │Extractor A│ │Extractor B│ │Other...   │                                 |
│  └─┬─────────┘ └─┬─────────┘ └─┬─────────┘                                 │
│    └─────────────┴─────────────|                                           │
│                                │                                           │
│                                [Raw Data Dict]                             │
│  eg.                                                                       │
│  {source, timestamp,                                                       │
│  items, ...}                                                               │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: AGGREGATION (Parallel)                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                  DataAggregator (Abstract)                           │  │
│  │  • aggregate(raw_data) → Dict[str, Any]                              │  │
│  │  • get_aggregator_metadata() → Dict[str, str]                        │  │
│  └─┬────────────────────────────────────────────────────────────────────┘  │
│    |                                                                       │
│    |─────────────┬─────────────┐                                           │
│    │             │             │                                           │
│    ▼             ▼             ▼                                           │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                                 │
│  │Aggregator │ │Analyser   │ │Other...   │                                 |
│  └─┬─────────┘ └─┬─────────┘ └─┬─────────┘                                 │
│    │             │             │                                           │
│    │  ThreadPoolExecutor (max_workers=N)                                   │
│    │             │             │                                           │
│    └─────────────┴─────────────|                                           │
│                                │                                           │
│                                [Merge All Outputs]                         │
│  eg.                           │                                           │
│  {total_vessels, dominant_category, revenue,                               │
│  inventory_health, service_capabilities, ...}                              │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 3: CATEGORISATION (Parallel)                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                  DataCategorizer (Abstract)                          │  │
│  │  • categorize(aggregated_data) → Dict[str, Any]                      │  │
│  │  • get_categorizer_metadata() → Dict[str, str]                       │  │
│  └─┬────────────────────────────────────────────────────────────────────┘  │
│    |                                                                       │
│    |─────────────┬─────────────┐                                           │
│    │             │             │                                           │
│    ▼             ▼             ▼                                           │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                                 │
│  │Categorizer│ │Score      │ │Other...   │                                 |
│  └─┬─────────┘ └─┬─────────┘ └─┬─────────┘                                 │
│    │             │             │                                           │
│    │  ThreadPoolExecutor (max_workers=N)                                   │
│    │             │             │                                           │
│    └─────────────┴─────────────|                                           │
│                                │                                           │
│                                [Individual Results]                        │
│  eg.                           │                                           │
│  {CompanySizeCategoriser: {}, OperatorTypeCategoriser: {},                 │
│  OtherCategoriser: {}, ...}                                                │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          FINAL OUTPUT                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ pipeline_metadata:                                                   │  │
│  │   - company_name                                                     │  │
│  │   - total_duration_sec                                               │  │
│  │   - extract_duration_sec                                             │  │
│  │   - timestamp                                                        │  │
│  │                                                                      │  │
│  │ raw_data: {...}                                                      │  │
│  │                                                                      │  │
│  │ aggregation_results:                                                 │  │
│  │   FleetAggregator: {output: {...}, duration_sec: 0.012}              │  │
│  │   ServiceCapabilityAggregator: {output: {...}, duration_sec: 0.008}  │  │
│  │   ...                                                                │  │
│  │                                                                      │  │
│  │ categorization_results:                                              │  │
│  │   CompanySizeCategorizer: {output: {...}, duration_sec: 0.005}       │  │
│  │   OperatorTypeCategorizer: {output: {...}, duration_sec: 0.007}      │  │
│  │   FleetModernityScorer: {output: {...}, duration_sec: 0.004}         │  │
│  │   RiskProfileCategorizer: {output: {...}, duration_sec: 0.006}       │  │
│  │   ...                                                                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘

==============================================================================
                          KEY DESIGN PRINCIPLES
==============================================================================

1. SINGLE RESPONSIBILITY
   • Extractors:   Only fetch data
   • Aggregators:  Only transform/analyse  
   • Categorisers: Only classify/score

2. COMPOSABILITY
   • Mix and match components
   • Reuse aggregators across domains
   • Add new categorisers without changing aggregators

3. PARALLELISM
   • Aggregators run in parallel (Stage 2)
   • Categorisers run in parallel (Stage 3)
   • ThreadPoolExecutor for I/O-bound operations

4. EXTENSIBILITY
   • Registry system for component discovery
   • Abstract base classes enforce contracts
   • Easy to add new components

5. OBSERVABILITY
   • Timing metrics for each component
   • Comprehensive logging
   • Metadata tracking

==============================================================================
                           EXAMPLE USE CASES
==============================================================================

MARITIME                    E-COMMERCE                  HEALTHCARE
---------                   ----------                  ----------
Fleet Analysis              Store Performance           Patient Risk
Vessel Classification       Inventory Management        Treatment Outcomes
Risk Assessment             Revenue Analysis            Resource Utilisation

FINANCIAL                   SUPPLY CHAIN                QUALITY CONTROL
---------                   ------------                ---------------
Credit Scoring              Supplier Analysis           Defect Detection
Portfolio Analysis          Lead Time Tracking          Process Monitoring
Risk Management             Cost Optimisation           Grade Assignment

==============================================================================
                          BATCH PROCESSING MODE
==============================================================================

Single Pipeline:                Batch Pipeline:
┌─────────────┐                ┌─────────────┐
│ Extractor 1 │                │ Extractor 1 │─┐
└──────┬──────┘                │ Extractor 2 │ ├─→ Same Analysis
       │                       │ Extractor 3 │─┘   Applied to All
       ▼                       └─────────────┘
  [Analysis]                         │
       │                             ▼
       ▼                        [Multiple Results]
   [Result]                          │
                                     ▼
                              [Comparative Summary]

```

### Quick Start Guide

This guide will help you get started with the data processing framework in 5 minutes.

#### Step 1: Understand the Basics

The framework has three main components:

1. **Extractor** - Gets raw data from a source (API, database, file, etc.)
2. **Aggregator** - Transforms and analyses the raw data
3. **Categoriser** - Classifies or scores the analyzed data

#### Step 2: Create Your First Extractor

```python
from utility import DataExtractor, register_extractor
from typing import Dict, Any

@register_extractor
class MyDataExtractor(DataExtractor):
    def __init__(self, data_source: str):
        self.data_source = data_source
    
    def extract(self) -> Dict[str, Any]:
        # Your code to fetch data goes here
        # For now, let's return sample data
        return {
            "source": self.data_source,
            "items": [
                {"id": 1, "value": 100, "category": "A"},
                {"id": 2, "value": 200, "category": "B"},
                {"id": 3, "value": 150, "category": "A"},
            ]
        }
```

#### Step 3: Create Your First Aggregator

```python
from utility import DataAggregator, register_aggregator

@register_aggregator
class BasicAggregator(DataAggregator):
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        items = raw_data.get("items", [])
        
        # Calculate some basic metrics
        total = sum(item["value"] for item in items)
        average = total / len(items) if items else 0
        
        # Count by category
        category_counts = {}
        for item in items:
            cat = item["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return {
            "total_items": len(items),
            "total_value": total,
            "average_value": average,
            "category_distribution": category_counts
        }
```

#### Step 4: Create Your First Categorizer

```python
from utility import DataCategorizer, register_categorizer

@register_categorizer
class SimpleCategorizer(DataCategorizer):
    def __init__(self, threshold: int = 150):
        self.threshold = threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        avg_value = aggregated_data.get("average_value", 0)
        
        if avg_value >= self.threshold:
            category = "high_value"
        else:
            category = "low_value"
        
        return {
            "category": category,
            "average_value": avg_value,
            "threshold_used": self.threshold
        }
```

#### Step 5: Run Your Pipeline

```python
from utility import AnalysisPipeline

# Create instances
extractor = MyDataExtractor(data_source="my_database")
aggregator = BasicAggregator()
categorizer = SimpleCategorizer(threshold=150)

# Build and run pipeline
pipeline = AnalysisPipeline(
    extractor=extractor,
    aggregators=[aggregator],
    categorizers=[categorizer]
)

results = pipeline.run()

# Access results
print("Aggregation Results:")
print(results["aggregation_results"]["BasicAggregator"]["output"])

print("\nCategorization Results:")
print(results["categorization_results"]["SimpleCategorizer"]["output"])
```

#### Step 6: Process Multiple Sources

```python
from utility import BatchPipeline

# Create multiple extractors for different data sources
extractors = [
    MyDataExtractor(data_source="database_1"),
    MyDataExtractor(data_source="database_2"),
    MyDataExtractor(data_source="database_3"),
]

# Use the same analysis for all
batch = BatchPipeline(
    extractors=extractors,
    aggregators=[BasicAggregator()],
    categorizers=[SimpleCategorizer(threshold=150)]
)

all_results = batch.run()

# Print summary
for result in all_results:
    source = result["raw_data"]["source"]
    category = result["categorization_results"]["SimpleCategorizer"]["output"]["category"]
    print(f"{source}: {category}")
```

#### Complete Example

Here's a complete working example you can copy and paste:

```python
from utility import (
    DataExtractor, DataAggregator, DataCategorizer,
    register_extractor, register_aggregator, register_categorizer,
    AnalysisPipeline
)
from typing import Dict, Any

# 1. Define Extractor
@register_extractor
class SalesDataExtractor(DataExtractor):
    def __init__(self, region: str):
        self.region = region
    
    def extract(self) -> Dict[str, Any]:
        # Simulate sales data
        return {
            "region": self.region,
            "sales": [
                {"product": "Widget A", "revenue": 1000, "units": 50},
                {"product": "Widget B", "revenue": 2000, "units": 100},
                {"product": "Widget C", "revenue": 1500, "units": 75},
            ]
        }

# 2. Define Aggregator
@register_aggregator
class SalesAggregator(DataAggregator):
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        sales = raw_data.get("sales", [])
        
        total_revenue = sum(s["revenue"] for s in sales)
        total_units = sum(s["units"] for s in sales)
        
        return {
            "region": raw_data.get("region"),
            "total_revenue": total_revenue,
            "total_units": total_units,
            "num_products": len(sales)
        }

# 3. Define Categorizer
@register_categorizer
class PerformanceCategorizer(DataCategorizer):
    def __init__(self, excellent_threshold: int = 4000):
        self.excellent_threshold = excellent_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        revenue = aggregated_data.get("total_revenue", 0)
        
        if revenue >= self.excellent_threshold:
            performance = "excellent"
        elif revenue >= self.excellent_threshold * 0.7:
            performance = "good"
        else:
            performance = "needs_improvement"
        
        return {
            "region": aggregated_data.get("region"),
            "performance": performance,
            "revenue": revenue
        }

# 4. Run Pipeline
if __name__ == "__main__":
    pipeline = AnalysisPipeline(
        extractor=SalesDataExtractor(region="North America"),
        aggregators=[SalesAggregator()],
        categorizers=[PerformanceCategorizer(excellent_threshold=4000)]
    )
    
    results = pipeline.run()
    
    # Display results
    perf = results["categorization_results"]["PerformanceCategorizer"]["output"]
    print(f"Region: {perf['region']}")
    print(f"Performance: {perf['performance']}")
    print(f"Revenue: ${perf['revenue']:,}")
```

#### Common Patterns

##### Pattern 1: Financial Analysis
- Extractor: Pull transaction data
- Aggregator: Calculate totals, averages, trends
- Categoriser: Assign risk levels, credit ratings

##### Pattern 2: Inventory Management
- Extractor: Fetch stock levels
- Aggregator: Calculate turnover, reorder points
- Categorizer: Flag items needing restocking

##### Pattern 3: Customer Segmentation
- Extractor: Get customer data
- Aggregator: Calculate lifetime value, engagement metrics
- Categorizer: Segment customers into tiers

##### Pattern 4: Quality Control
- Extractor: Retrieve inspection data
- Aggregator: Calculate defect rates, trends
- Categorizer: Assign quality grades

#### Tips

1. **Keep It Simple**: Start with one aggregator and one categoriser
2. **Use Descriptive Names**: Name your classes clearly (e.g., `InventoryAggregator`, not just `Aggregator1`)
3. **Return Consistent Structure**: Always return dictionaries with predictable keys
4. **Test Incrementally**: Test each component before building the full pipeline
5. **Use Parameters**: Make thresholds and rules configurable via `__init__`
6. **Document Your Logic**: Add docstrings explaining what each component does
