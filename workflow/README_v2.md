# Entity-to-Assessment Generator

## Overview

The **Entity-to-Assessment Generator** reduces the minimum viable interaction for DSI pricing from **4 data points to 1**:

### Traditional Approach (4 inputs required):
```python
- entity_id
- coverage_type
- limit
- deductible
```

### New Approach (1 input required):
```python
- entity_name (e.g., "Microsoft Corporation")
```

All other parameters are automatically derived from:
- **Configurable limit bandings** (`coverage_limit_bands.yaml`)
- **DSI signal extraction** (automated)
- **Model defaults** (from model registry)

---

## Quick Start

### Basic Usage

Generate assessments for all coverages with one command:

```bash
python workflow/entity_to_assessment.py "Microsoft Corporation"
```

This will:
1. Extract signals for Microsoft
2. Generate quotes for ALL enabled coverage types
3. Apply ALL limit bands for each coverage
4. Return comprehensive assessment results

### Example Output (Summary Format)

```json
{
  "entity": "Microsoft Corporation",
  "entity_id": "microsoft-corporation-20251202",
  "generated_at": "2025-12-02T14:30:00",
  "total_assessments": 35,
  "assessments": [
    {
      "coverage": "cyber",
      "limit": "$5,000,000",
      "limit_label": "Mid-Market SME",
      "deductible": "$50,000",
      "score": "742/1000",
      "tier": "STANDARD",
      "premium": "$11,250.00",
      "decision": "straight_through",
      "status": "quoted",
      "flags": {
        "green": 5,
        "amber": 2,
        "red": 0
      }
    },
    ...
  ]
}
```

---

## Advanced Usage

### Specific Coverage Types

```bash
# Only Cyber and Financial Institutions
python workflow/entity_to_assessment.py "JP Morgan Chase" --coverage-types cyber,fi

# Only D&O
python workflow/entity_to_assessment.py "Tesla Inc" --coverage-types do
```

### Custom Entity ID

```bash
python workflow/entity_to_assessment.py "Apple Inc" --entity-id aapl-001
```

### Output Formats

#### Summary Format (Default - Concise)
```bash
python workflow/entity_to_assessment.py "Google" --format summary --output google_summary.json
```

#### Full JSON (Complete Details)
```bash
python workflow/entity_to_assessment.py "Amazon" --format json --output amazon_full.json
```

#### CSV Export
```bash
python workflow/entity_to_assessment.py "Meta" --format csv --output meta_assessments.csv
```

### Custom Policy Parameters

```bash
python workflow/entity_to_assessment.py "Ford Motor Co" \
  --term-months 24 \
  --market uk \
  --entity-id ford-uk-001
```

### Verbose Logging

```bash
python workflow/entity_to_assessment.py "IBM" --verbose
```

---

## Configuration: Limit Bandings

Edit `workflow/coverage_limit_bands.yaml` to customize limit bands for each coverage type.

### Structure

```yaml
cyber:
  enabled: true
  currency: USD
  bands:
    - limit: 1000000
      label: "Small Tech Startup"
      standard_deductible: 25000
    - limit: 5000000
      label: "Mid-Market SME"
      standard_deductible: 50000
```

### Coverage Types

| Coverage | Bands | Range |
|----------|-------|-------|
| **Cyber** | 5 | $1M - $50M |
| **Financial Institutions** | 5 | $5M - $100M |
| **D&O** | 5 | $5M - $100M |
| **Energy** | 5 | $10M - $250M |
| **Marine** | 5 | $5M - $100M |
| **PI** | 5 | $1M - $25M |
| **Aerospace** | 5 | $10M - $250M |

### Enable/Disable Coverages

```yaml
cyber:
  enabled: true  # Active
  ...

pi:
  enabled: false  # Disabled
  ...
```

### Custom Bandings

Add custom banding sets for specific use cases:

```yaml
custom_bands:
  cyber_startup:
    parent: cyber
    enabled: true
    bands:
      - limit: 500000
        label: "Seed Stage"
        standard_deductible: 10000
```

---

## Use Cases

### 1. Portfolio Screening

Generate quick assessments for a list of entities:

```bash
#!/bin/bash
# screen_portfolio.sh

for entity in "Microsoft" "Apple" "Google" "Amazon" "Meta"; do
  python workflow/entity_to_assessment.py "$entity" \
    --format summary \
    --output "assessments/${entity}_assessment.json"
done
```

### 2. Broker Submissions

Accept broker submissions with minimal information:

```python
from workflow.entity_to_assessment import EntityAssessmentGenerator

generator = EntityAssessmentGenerator()

# Broker provides just company name
results = generator.generate_for_entity(
    entity_name="Acme Technology Corp"
)

# Instantly get quotes for all coverages and limits
for result in results:
    print(f"{result.coverage_name}: ${result.gross_premium:,.2f}")
```

### 3. API Integration

Build a REST API endpoint that accepts just entity name:

```python
from flask import Flask, jsonify, request
from workflow.entity_to_assessment import EntityAssessmentGenerator

app = Flask(__name__)
generator = EntityAssessmentGenerator(storage_type="redis")

@app.route("/api/v1/assess", methods=["POST"])
def assess_entity():
    data = request.json
    entity_name = data.get("entity_name")

    results = generator.generate_for_entity(entity_name)

    return jsonify({
        "entity": entity_name,
        "assessments": [r.to_summary() for r in results]
    })
```

### 4. Bulk Processing

Process multiple entities in batch:

```python
from workflow.entity_to_assessment import EntityAssessmentGenerator

generator = EntityAssessmentGenerator()

entities = [
    "Microsoft Corporation",
    "Apple Inc",
    "Amazon.com Inc",
    "Alphabet Inc",
    "Meta Platforms Inc",
]

all_results = []

for entity in entities:
    results = generator.generate_for_entity(entity)
    all_results.extend(results)

# Export combined results
output = generator.export_results(all_results, output_format="csv", output_file="bulk_assessments.csv")
```

---

## Architecture

### How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                  ENTITY-TO-ASSESSMENT FLOW                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. INPUT: Entity Name ("Microsoft")                            │
│                   │                                              │
│                   ▼                                              │
│  2. Load Limit Bandings Config                                  │
│     ├─ Cyber: 5 limit bands                                     │
│     ├─ FI: 5 limit bands                                        │
│     ├─ D&O: 5 limit bands                                       │
│     └─ ... (all enabled coverages)                              │
│                   │                                              │
│                   ▼                                              │
│  3. For Each Coverage Type:                                     │
│     For Each Limit Band:                                        │
│                   │                                              │
│                   ▼                                              │
│     ┌──────────────────────────────────┐                        │
│     │    DSI Workflow Processing       │                        │
│     ├──────────────────────────────────┤                        │
│     │ • Extract signals (cached)       │                        │
│     │ • Run pricing model              │                        │
│     │ • Calculate score/tier           │                        │
│     │ • Determine decision path        │                        │
│     │ • Generate quote                 │                        │
│     └──────────────────────────────────┘                        │
│                   │                                              │
│                   ▼                                              │
│  4. OUTPUT: Comprehensive Assessment Results                    │
│     ├─ 35 quotes generated (7 coverages × 5 bands)              │
│     ├─ Average score: 742/1000                                  │
│     ├─ Total premium: $X,XXX,XXX                                │
│     └─ Decision breakdown: 80% straight-through, 20% referred   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Signal Extraction (Automatic)

Signals are extracted automatically for the entity and cached:

| Signal Category | TTL | Examples |
|-----------------|-----|----------|
| **STATIC** | 90 days | Company registration, industry |
| **SEMI_STATIC** | 7 days | Financial ratings, certifications |
| **DYNAMIC** | 4 hours | Security scores, vulnerabilities |
| **REAL_TIME** | No cache | Active incidents, stock price |

On subsequent assessments (e.g., requotes), signals are reused from cache, making processing nearly instant.

### Model Selection (Automatic)

For each coverage type, the active model version is automatically selected:

```python
# Automatic model selection
model = model_registry.get_active_model(coverage_type="cyber")

# Uses:
# - Model version: e.g., "2.0.0"
# - Signal requirements: e.g., ["security_rating", "breach_history", ...]
# - Thresholds: e.g., {"tier_1": 800, "tier_2": 650, ...}
# - Base rates: e.g., {"base_rate": 2500, "min_premium": 5000}
```

---

## Performance

### First Assessment (Cold Cache)
- **Signals Extracted**: 8-15 per coverage (varies by model)
- **Processing Time**: ~3-5 seconds per coverage
- **Total Time for All Coverages**: ~25-40 seconds

### Subsequent Assessments (Warm Cache)
- **Signals Extracted**: 0 (all from cache)
- **Processing Time**: ~50-100ms per quote
- **Total Time for All Coverages**: ~2-3 seconds

### Cache Efficiency

| Scenario | Cache Hit Rate | Processing Time |
|----------|----------------|-----------------|
| First quote | 0% | 3000ms |
| Requote (same day) | 100% | 50ms |
| Requote (next week) | ~60% | 800ms |
| Different coverage (same entity) | 70-90% | 500ms |

---

## Error Handling

### Invalid Entity

```bash
$ python workflow/entity_to_assessment.py "NonexistentCompany123"

Warning: No signals found for entity
Processing with default/minimal signal set...
```

### Coverage Not Enabled

```bash
$ python workflow/entity_to_assessment.py "Apple" --coverage-types pi

Warning: Coverage pi not enabled or not found
Skipping...
```

### Signal Extraction Failure

Partial failures are handled gracefully:

```
Processing Cyber Insurance...
  ✓ Small Tech Startup: Score 720, Premium $2,250
  ✓ Mid-Market SME: Score 720, Premium $11,250
  ✗ Error processing Large Enterprise: Signal extraction timeout
  ✓ Fortune 500: Score 720, Premium $56,250
```

---

## Integration Examples

### Python Script

```python
from workflow.entity_to_assessment import EntityAssessmentGenerator

# Initialize generator
generator = EntityAssessmentGenerator()

# Generate assessments
results = generator.generate_for_entity("Microsoft Corporation")

# Process results
for result in results:
    if result.decision_path == "straight_through":
        print(f"Auto-approved: {result.coverage_name} @ ${result.gross_premium:,.2f}")
    elif result.decision_path == "referred":
        print(f"Refer to underwriter: {result.coverage_name}")
        print(f"  Reasons: {', '.join(result.decision_reasons)}")
```

### REST API

```python
# See full API example in Use Cases section above
```

### Command-Line Automation

```bash
#!/bin/bash
# Daily portfolio screening

date=$(date +%Y%m%d)
output_dir="assessments/$date"
mkdir -p "$output_dir"

# Read entities from file
while read entity; do
  echo "Assessing: $entity"
  python workflow/entity_to_assessment.py "$entity" \
    --format json \
    --output "$output_dir/${entity// /_}.json"
done < entities.txt

# Aggregate results
python scripts/aggregate_assessments.py "$output_dir"
```

---

## Comparison: Old vs New

### Old Minimum Viable Interaction (4 inputs)

```python
quote = dsi_api.get_quote(
    entity_id="msft-001",          # Required
    coverage_type="cyber",         # Required
    limit=5000000,                 # Required
    deductible=50000               # Required
)
```

**Result**: 1 quote

### New Minimum Viable Interaction (1 input)

```python
results = entity_assessment_generator.generate_for_entity(
    entity_name="Microsoft Corporation"  # Only required input
)
```

**Result**: 35 quotes (7 coverages × 5 limit bands each)

---

## Customization

### Add New Coverage Type

1. Edit `coverage_limit_bands.yaml`:

```yaml
property:
  enabled: true
  currency: USD
  name: "Property Insurance"
  bands:
    - limit: 10000000
      label: "Small Property"
      standard_deductible: 100000
    - limit: 50000000
      label: "Large Property"
      standard_deductible: 500000
```

2. Ensure model is registered in workflow:

```python
# In dsi_workflow.py initialize_models()
coverage_configs["property"] = {
    "name": "DSI Property Model",
    "base_rate": 1500,
    "min_premium": 10000,
    "signal_requirements": [
        "property_age", "construction_type", "fire_protection",
        "natural_hazard_exposure", "security_systems"
    ],
}
```

### Modify Limit Bands

Edit `coverage_limit_bands.yaml` to add, remove, or modify bands:

```yaml
cyber:
  bands:
    - limit: 500000        # Add new band
      label: "Micro SME"
      standard_deductible: 10000
    - limit: 1000000
      label: "Small Tech Startup"
      standard_deductible: 25000
    # ... existing bands
    - limit: 100000000     # Add new band
      label: "Tech Giant"
      standard_deductible: 1000000
```

---

## Troubleshooting

### Issue: "Config file not found"

**Solution**: Ensure `coverage_limit_bands.yaml` is in the `workflow/` directory, or specify path:

```bash
python workflow/entity_to_assessment.py "Apple" --config /path/to/config.yaml
```

### Issue: "No active model for coverage type: X"

**Solution**: Ensure models are initialized:

```python
from workflow.dsi_workflow import initialize_models

workflow = create_workflow()
initialize_models(workflow)  # This registers all models
```

### Issue: Slow performance

**Solution**: Use Redis for caching:

```bash
python workflow/entity_to_assessment.py "Microsoft" --storage redis
```

Configure Redis connection in storage config.

---

## Files

| File | Purpose |
|------|---------|
| `entity_to_assessment.py` | Main script |
| `coverage_limit_bands.yaml` | Limit bandings configuration |
| `dsi_workflow.py` | Workflow orchestration |
| `dsi_persistence.py` | Persistence layer |

---

## Command-Line Reference

```
usage: entity_to_assessment.py [-h] [--entity-id ENTITY_ID]
                               [--coverage-types COVERAGE_TYPES]
                               [--config CONFIG]
                               [--format {json,summary,csv}]
                               [--output OUTPUT]
                               [--market MARKET]
                               [--term-months TERM_MONTHS]
                               [--storage {memory,redis,postgres}]
                               [--verbose]
                               entity_name

Generate comprehensive DSI assessments from just an entity identifier

positional arguments:
  entity_name           Company/entity name to assess

optional arguments:
  -h, --help            show this help message and exit
  --entity-id ENTITY_ID
                        Optional entity ID (generated from name if not provided)
  --coverage-types COVERAGE_TYPES
                        Comma-separated list of coverage types (e.g., 'cyber,fi,do').
                        Defaults to all enabled.
  --config CONFIG       Path to limit banding config YAML file (uses default if not
                        specified)
  --format {json,summary,csv}
                        Output format (default: summary)
  --output OUTPUT       Output file path (prints to stdout if not specified)
  --market MARKET       Market code (default: us)
  --term-months TERM_MONTHS
                        Policy term in months (default: 12)
  --storage {memory,redis,postgres}
                        Storage backend (default: memory)
  --verbose             Enable verbose logging
```

---

## Summary

The Entity-to-Assessment Generator transforms DSI from a **4-input pricing system** to a **1-input comprehensive assessment platform**.

**Key Benefits**:
- ✅ **Reduced Friction**: One input generates 30-40 quotes
- ✅ **Consistency**: All limit bands assessed with same methodology
- ✅ **Speed**: Caching makes subsequent assessments nearly instant
- ✅ **Flexibility**: Configurable bands without code changes
- ✅ **Automation**: Perfect for batch processing and API integration

**Perfect For**:
- Broker portals (minimal input required)
- Portfolio screening (bulk assessments)
- API integrations (simple endpoints)
- Underwriting assistants (comprehensive view)
