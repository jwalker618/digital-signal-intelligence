# DSI Portfolio Management Module

## Overview

The `portfolio_management` module is the **primary human interface** for the DSI system. It consolidates all underlying functionality into a unified platform for managing insurance portfolios across multiple coverage lines.

## Key Capabilities

### 1. Multi-Line Portfolio Management
- Manage risks across Cyber, FI, Energy, Marine, D&O, and more
- Extensible architecture for new coverage lines (Casualty, Property, etc.)
- Unified scoring and tiering across all lines

### 2. Real-Time Monitoring
- Automatic alert generation for threshold breaches
- Concentration monitoring (sector, geography, vendor, single risk)
- Score deterioration tracking
- Tier migration detection

### 3. Deep Analysis
- Individual risk drill-down with full signal detail
- Peer comparison and benchmarking
- Historical trend analysis
- Variance detection and explanation

### 4. Portfolio Intelligence
- Natural language queries ("show me tier 4 cyber risks")
- Outlier detection
- Stale assessment identification
- Scenario analysis ("what-if" modeling)

### 5. Dashboard & Reporting
- Executive summary with portfolio health score
- Distribution analysis (score, tier, coverage, geography)
- Alert management interface
- Export to JSON, CSV, or dict formats

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DSIPortfolioManager                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐   │
│  │ Risk Manager  │  │Alert Manager  │  │  Analysis Engine      │   │
│  │ • add_risk    │  │ • check       │  │  • analyse_risk       │   │
│  │ • update_risk │  │ • acknowledge │  │  • analyse_portfolio  │   │
│  │ • get_risks   │  │ • resolve     │  │  • compare_risks      │   │
│  └───────────────┘  └───────────────┘  └───────────────────────┘   │
│                                                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐   │
│  │ Query Engine  │  │ Dashboard Gen │  │  Export Manager       │   │
│  │ • query       │  │ • generate    │  │  • export_portfolio   │   │
│  │ • find_outliers│ │ • health_score│  │  • export_alerts      │   │
│  │ • find_stale  │  │ • metrics     │  │  • to_csv/json        │   │
│  └───────────────┘  └───────────────┘  └───────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                Coverage Line Registry                        │   │
│  │  Cyber | FI | Energy | Marine | D&O | Casualty | Property   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Initialize Portfolio Manager
```python
from portfolio_management import DSIPortfolioManager, CoverageType, RiskMetadata, DSIAssessment

manager = DSIPortfolioManager()
```

### Add a Risk
```python
risk = manager.add_risk(
    entity_name="Acme Technology Corp",
    coverage_type=CoverageType.CYBER,
    metadata=RiskMetadata(
        sector='technology',
        geography='US',
        premium=500000,
        limit=10000000
    ),
    assessment=DSIAssessment(
        overall_score=720,
        tier=2,
        data_quality_score=85
    )
)
```

### Get Portfolio Metrics
```python
metrics = manager.calculate_metrics()
print(f"Total Risks: {metrics.total_risks}")
print(f"Average Score: {metrics.average_score:.0f}")
print(f"By Tier: {metrics.risks_by_tier}")
```

### Check Alerts
```python
alerts = manager.get_active_alerts(severity=AlertSeverity.HIGH)
for alert in alerts:
    print(f"[{alert.severity.value}] {alert.title}")
```

### Query Portfolio
```python
# Natural language query
result = manager.query("show me tier 4 cyber risks")
print(f"Found {result.result_count} risks")

# Programmatic query
risks = manager.get_risks(
    coverage_type=CoverageType.CYBER,
    tier=4,
    min_score=350,
    max_score=499
)
```

### Analyse a Risk
```python
analysis = manager.analyze_risk(risk.identifier.risk_id, depth=AnalysisDepth.DETAILED)
print(f"Score: {analysis['assessment']['overall_score']}")
print(f"Peer Percentile: {analysis['peer_comparison']['percentile_rank']}")
```

### Generate Dashboard
```python
dashboard = manager.generate_dashboard()
print(f"Portfolio Health: {dashboard['executive_summary']['portfolio_health']['score']}")
```

## Alert Types

| Alert Type | Severity | Description |
|------------|----------|-------------|
| CONCENTRATION_SECTOR | HIGH | Sector exposure exceeds limit |
| CONCENTRATION_GEOGRAPHY | HIGH | Geographic concentration breach |
| CONCENTRATION_SINGLE_RISK | CRITICAL | Single risk too large |
| SCORE_DETERIORATION | HIGH | Score dropped significantly |
| TIER_MIGRATION | MEDIUM | Risk moved to worse tier |
| DATA_QUALITY_LOW | LOW | Assessment quality concerns |
| SIGNAL_MISSING | LOW | Expected signals not collected |
| MANUAL_REVIEW_REQUIRED | MEDIUM | Human review needed |

## Concentration Limits (Defaults)

| Dimension | Default Limit |
|-----------|---------------|
| Single Risk | 5% of portfolio |
| Sector | 25% of portfolio |
| Geography | 30% of portfolio |
| Vendor | 10% of portfolio |
| Tier 4 | 15% of portfolio |
| Tier 5 | 5% of portfolio |

## Adding New Coverage Lines

```python
from portfolio_management import CoverageLineRegistry, CoverageType

# Register a new coverage type
CoverageLineRegistry.register(
    coverage_type=CoverageType.PROFESSIONAL_INDEMNITY,
    name="Professional Indemnity",
    signal_weights={
        'network_authority': 0.20,
        'technical_infrastructure': 0.10,
        'asset_telemetry': 0.15,
        'structured_data': 0.20,
        'corporate_footprint': 0.20,
        'public_records': 0.15,
    },
    sector_adjustments={
        'legal': -0.10,
        'accounting': -0.05,
        'consulting': 0.0,
    }
)
```

## Scenario Analysis

```python
# What if all scores dropped by 100 points?
scenario = manager.run_scenario(
    "Market Stress Test",
    {'score_adjustment': -100}
)

print(f"Current avg: {scenario['current_state']['average_score']:.0f}")
print(f"Scenario avg: {scenario['scenario_state']['average_score']:.0f}")
print(f"Tier shift: {scenario['current_state']['tier_distribution']} → {scenario['scenario_state']['tier_distribution']}")
```

## Export Options

```python
# JSON export
json_data = manager.export_portfolio(format='json', include_history=True)

# CSV export
csv_data = manager.export_portfolio(format='csv')

# Dict for further processing
data = manager.export_portfolio(format='dict')

# Export alerts
alerts_json = manager.export_alerts(format='json')
```

## Portfolio Health Score

The portfolio health score (0-100) is calculated based on:
- Tier distribution (high-risk tier concentration)
- Concentration limit breaches
- Data quality metrics
- Review backlog
- Active critical alerts

| Score | Status | Color |
|-------|--------|-------|
| 80-100 | Healthy | Green |
| 60-79 | Attention Needed | Amber |
| 0-59 | Action Required | Red |

## Integration with Signal Collection

```python
from portfolio_management import DSIPortfolioManager
from signal_collection import create_signal_engine, ModelType

manager = DSIPortfolioManager()

# Refresh all assessments using signal engine
signal_engine = create_signal_engine(ModelType.CYBER)
results = manager.refresh_all_assessments(
    signal_engine=signal_engine,
    coverage_types=[CoverageType.CYBER]
)

print(f"Refreshed: {results['refreshed']}/{results['total_risks']}")
print(f"Score changes: {results['score_changes']}")
```

## Best Practices

1. **Regular Monitoring**: Check alerts daily, especially CRITICAL and HIGH severity
2. **Data Quality**: Address low data quality scores to improve assessment accuracy
3. **Concentration Management**: Monitor approaching limits, not just breaches
4. **Historical Tracking**: Review score trends to catch gradual deterioration
5. **Scenario Planning**: Run stress tests quarterly to understand portfolio resilience
