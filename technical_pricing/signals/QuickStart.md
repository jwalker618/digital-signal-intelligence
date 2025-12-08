# Quick Start Guide

This guide will help you get started with the data processing framework in 5 minutes.

## Step 1: Understand the Basics

The framework has three main components:

1. **Extractor** - Gets raw data from a source (API, database, file, etc.)
2. **Aggregator** - Transforms and analyzes the raw data
3. **Categorizer** - Classifies or scores the analyzed data

## Step 2: Create Your First Extractor

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

## Step 3: Create Your First Aggregator

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

## Step 4: Create Your First Categorizer

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

## Step 5: Run Your Pipeline

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

## Step 6: Process Multiple Sources

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

## Complete Example

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

## Next Steps

1. **Add Multiple Aggregators**: Create specialized aggregators for different aspects of your data
2. **Add Multiple Categorizers**: Score and classify your data in various ways
3. **Use BatchPipeline**: Process multiple data sources with the same analysis
4. **Add Error Handling**: The framework catches errors automatically, but you can add custom handling
5. **Customize Parameters**: Use `__init__` parameters to make your components configurable

## Common Patterns

### Pattern 1: Financial Analysis
- Extractor: Pull transaction data
- Aggregator: Calculate totals, averages, trends
- Categorizer: Assign risk levels, credit ratings

### Pattern 2: Inventory Management
- Extractor: Fetch stock levels
- Aggregator: Calculate turnover, reorder points
- Categorizer: Flag items needing restocking

### Pattern 3: Customer Segmentation
- Extractor: Get customer data
- Aggregator: Calculate lifetime value, engagement metrics
- Categorizer: Segment customers into tiers

### Pattern 4: Quality Control
- Extractor: Retrieve inspection data
- Aggregator: Calculate defect rates, trends
- Categorizer: Assign quality grades

## Tips

1. **Keep It Simple**: Start with one aggregator and one categorizer
2. **Use Descriptive Names**: Name your classes clearly (e.g., `InventoryAggregator`, not just `Aggregator1`)
3. **Return Consistent Structure**: Always return dictionaries with predictable keys
4. **Test Incrementally**: Test each component before building the full pipeline
5. **Use Parameters**: Make thresholds and rules configurable via `__init__`
6. **Document Your Logic**: Add docstrings explaining what each component does

## Troubleshooting

**Problem**: My extractor returns empty data
- Check your data source connection
- Add print statements to debug
- Return sample data first to verify the pipeline works

**Problem**: Aggregator crashes
- Check for empty lists before calculating averages/sums
- Add defensive checks for missing keys
- Use `.get()` with defaults instead of direct dictionary access

**Problem**: Categorizer gives unexpected results
- Print the aggregated_data to see what you're receiving
- Verify your threshold logic
- Check for edge cases (zero values, None, etc.)

## Getting Help

1. Check `FRAMEWORK_GUIDE.md` for detailed documentation
2. Look at `example_ecommerce.py` for a complete working example
3. Review the maritime examples in `utility.py`

## Summary

You now know how to:
- ✅ Create extractors to pull data
- ✅ Create aggregators to analyze data
- ✅ Create categorizers to classify data
- ✅ Run a pipeline to process everything
- ✅ Handle multiple data sources with BatchPipeline

Start building your own analysis pipeline!
