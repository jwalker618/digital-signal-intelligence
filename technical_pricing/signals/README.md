# Data Processing Framework - Refined Version

## What's Included

This package contains a refined, production-ready data processing framework with clear separation of concerns and extensibility.

### Core Files

1. **utility.py** - The main framework with:
   - Base classes for Extractors, Aggregators, and Categorizers
   - Pipeline orchestration (single and batch)
   - Registry system for component discovery
   - Parallel execution support
   - Maritime domain examples

2. **QUICK_START.md** - Get started in 5 minutes
   - Step-by-step guide
   - Copy-paste examples
   - Common patterns
   - Troubleshooting tips

3. **FRAMEWORK_GUIDE.md** - Comprehensive documentation
   - Architecture overview
   - Detailed component descriptions
   - Implementation patterns
   - Best practices
   - Extension points

4. **example_ecommerce.py** - Complete working example
   - E-commerce store analysis
   - Shows how to adapt framework to new domains
   - Multiple extractors, aggregators, and categorizers
   - Demonstrates batch processing

## Key Improvements from Original

### 1. Clear Three-Stage Architecture

**Before**: Single "Scorer" concept that mixed concerns

**After**: Three distinct stages
- **Extractors**: Pure data retrieval from sources
- **Aggregators**: Data transformation and analysis
- **Categorizers**: Classification and scoring

### 2. Better Separation of Concerns

Each component has a single, well-defined responsibility:
- Extractors don't analyze
- Aggregators don't classify
- Categorizers work with pre-analyzed data

### 3. More Flexible Pipeline

- Multiple aggregators can run in parallel
- Multiple categorizers can run in parallel
- Aggregated data is merged for categorizers
- Easy to add new analysis dimensions

### 4. Improved Naming and Structure

- Descriptive class names (`FleetAggregator` vs `FleetSizeScorer`)
- Clear method names (`aggregate()`, `categorize()` vs `score()`)
- Consistent return structures
- Better documentation

### 5. Enhanced Examples

**Maritime Domain** (in utility.py):
- EquasisAPIExtractor
- FleetAggregator
- ServiceCapabilityAggregator  
- CompanySizeCategorizer
- OperatorTypeCategorizer
- FleetModernityScorer
- RiskProfileCategorizer

**E-Commerce Domain** (in example_ecommerce.py):
- ShopifyAPIExtractor
- InventoryAggregator
- RevenueAggregator
- CustomerSatisfactionAggregator
- StoreSizeCategorizer
- InventoryHealthScorer
- RevenuePerformanceCategorizer
- CustomerExperienceScorer

### 6. Better Extensibility

- Registry system for component discovery
- Abstract base classes with clear interfaces
- Configurable thresholds via `__init__` parameters
- Metadata methods for introspection
- Easy to plug in new components

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                     DATA SOURCES                          │
│  (APIs, Databases, Files, Streams, Scrapers, etc.)       │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                   STAGE 1: EXTRACTION                     │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Extractor 1 │  │  Extractor 2 │  │  Extractor N │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│         └──────────────────┴──────────────────┘          │
│                            │                              │
│                      [Raw Data]                           │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│              STAGE 2: AGGREGATION (Parallel)              │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Aggregator 1 │  │ Aggregator 2 │  │ Aggregator N │  │
│  │   (Stats)    │  │ (Trends)     │  │  (Patterns)  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│         └──────────────────┴──────────────────┘          │
│                            │                              │
│                  [Aggregated Data Merged]                 │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│            STAGE 3: CATEGORIZATION (Parallel)             │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Categorizer 1 │  │Categorizer 2 │  │Categorizer N │  │
│  │   (Tier)     │  │  (Risk)      │  │   (Score)    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│         └──────────────────┴──────────────────┘          │
│                            │                              │
│                       [Results]                           │
└────────────────────────────┴─────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Final Output   │
                    │  • Raw Data     │
                    │  • Aggregations │
                    │  • Categories   │
                    │  • Metadata     │
                    └─────────────────┘
```

## Usage Example

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

## Testing the Framework

### Run Maritime Example
```bash
python utility.py
```

### Run E-Commerce Example
```bash
python example_ecommerce.py
```

Both examples demonstrate:
- Multiple extractors (different companies/stores)
- Parallel aggregation (different analytical dimensions)
- Parallel categorization (multiple classification schemes)
- Summary report generation

## Key Features

✅ **Modular Architecture** - Easy to add new components  
✅ **Parallel Execution** - Fast processing with ThreadPoolExecutor  
✅ **Type Safety** - Abstract base classes enforce contracts  
✅ **Error Handling** - Automatic exception catching and logging  
✅ **Timing Metrics** - Track performance of each component  
✅ **Registry System** - Automatic component discovery  
✅ **Batch Processing** - Handle multiple sources efficiently  
✅ **Flexible Configuration** - Parameterizable thresholds and rules  
✅ **Comprehensive Logging** - Track pipeline execution  
✅ **Production Ready** - Tested and documented  

## When to Use This Framework

### Perfect For:
- Analyzing data from multiple similar sources
- Applying consistent analysis across datasets
- Building classification/scoring systems
- Processing batch data with standardized logic
- Creating reusable analysis components

### Not Ideal For:
- One-off data processing scripts
- Simple single-source analysis
- Real-time streaming (though adaptable)
- When sources require completely different analysis

## Extending the Framework

### Add a New Domain (e.g., Healthcare)

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

## Performance Characteristics

- **Extraction**: Sequential (one extractor per pipeline)
- **Aggregation**: Parallel (all aggregators run simultaneously)
- **Categorization**: Parallel (all categorizers run simultaneously)
- **Bottleneck**: Usually the extraction phase (I/O bound)
- **Optimization**: Use BatchPipeline for multiple sources

## File Structure

```
.
├── utility.py                  # Core framework + maritime examples
├── example_ecommerce.py        # E-commerce domain example
├── QUICK_START.md             # 5-minute getting started guide
├── FRAMEWORK_GUIDE.md         # Comprehensive documentation
└── README.md                  # This file
```

## Requirements

- Python 3.9+
- No external dependencies (uses only standard library)
- Easily adaptable to use with pandas, numpy, etc.

## Next Steps

1. **Start Here**: Read `QUICK_START.md` for a 5-minute introduction
2. **Go Deeper**: Read `FRAMEWORK_GUIDE.md` for comprehensive docs
3. **See Examples**: Run `utility.py` and `example_ecommerce.py`
4. **Build Your Own**: Create extractors/aggregators/categorizers for your domain

## Questions?

Check the documentation files for:
- Detailed architecture explanation
- Best practices
- Common patterns
- Troubleshooting tips
- Extension points

## Summary

This framework provides a clean, scalable way to:
1. Extract data from multiple sources
2. Analyze it consistently
3. Classify/score based on business rules
4. Process multiple entities in parallel

The three-stage architecture (Extract → Aggregate → Categorize) makes it easy to understand, extend, and maintain.
