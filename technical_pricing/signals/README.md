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

#### Core Files

1. **utility.py** - The main framework with:
   - Base classes for Extractors, Aggregators, and Categorisers
   - Pipeline orchestration (single and batch)
   - Registry system for component discovery
   - Parallel execution support
   - Maritime domain examples

2. **example_ecommerce.py** - Complete working example
   - E-commerce store analysis
   - Shows how to adapt framework to new domains
   - Multiple extractors, aggregators, and categorisers
   - Demonstrates batch processing

### Key Features

✅ **Modular Architecture** - Easy to add new components  
✅ **Clear Seperation of Concerns** - Each component has a single, well-defined responsibility. 
✅ **Parallel Execution** - Fast processing with ThreadPoolExecutor  
✅ **Type Safety** - Abstract base classes enforce contracts  
✅ **Error Handling** - Automatic exception catching and logging  
✅ **Timing Metrics** - Track performance of each component  
✅ **Registry System** - Automatic component discovery  
✅ **Batch Processing** - Handle multiple sources efficiently  
✅ **Flexible Configuration** - Parameterizable thresholds and rules  
✅ **Comprehensive Logging** - Track pipeline execution  

### Architecture Diagram

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

### Usage Example

```python
from utility import AnalysisPipeline, BatchPipeline

# Single source analysis
pipeline = AnalysisPipeline(
    extractor=MyExtractor(),
    aggregators=[Aggregator1(), Aggregator2()],
    categorizers=[Categorizer1(), Categorizer2(), Categorizer3()]
)
results = pipeline.run()

# Multiple sources, same analysis
batch = BatchPipeline(
    extractors=[Extractor1(), Extractor2(), Extractor3()],
    aggregators=[Aggregator1(), Aggregator2()],
    categorizers=[Categorizer1(), Categorizer2()]
)
all_results = batch.run()
```

### Testing the Framework

#### Run Maritime Example
```bash
python utility.py
```

#### Run E-Commerce Example
```bash
python example_ecommerce.py
```

Both examples demonstrate:
- Multiple extractors (different companies/stores)
- Parallel aggregation (different analytical dimensions)
- Parallel categorization (multiple classification schemes)
- Summary report generation

### When to Use This Framework

#### Perfect For:
- Analysing data from multiple similar sources
- Applying consistent analysis across datasets
- Building classification/scoring systems
- Processing batch data with standardized logic
- Creating reusable analysis components

#### Not Ideal For:
- One-off data processing scripts
- Simple single-source analysis
- Real-time streaming (though adaptable)
- When sources require completely different analysis

### Extending the Framework

#### Add a New Domain (e.g., Healthcare)

1. **Create Extractors** for your data sources:
   - EHRExtractor (Electronic Health Records)
   - LabResultsExtractor
   - PatientSurveyExtractor

2. **Create Aggregators** for analysis:
   - ClinicalMetricsAggregator
   - TreatmentOutcomesAggregator
   - CostAnalysisAggregator

3. **Create Categorizers** for classification:
   - RiskStratificationCategorizer
   - TreatmentSuccessScorer
   - ResourceUtilizationCategorizer

4. **Run the Pipeline**:
```python
pipeline = AnalysisPipeline(
    extractor=EHRExtractor(patient_id="12345"),
    aggregators=[ClinicalMetricsAggregator(), TreatmentOutcomesAggregator()],
    categorizers=[RiskStratificationCategorizer(), TreatmentSuccessScorer()]
)
```
