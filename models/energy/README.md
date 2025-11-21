# DSI Energy Sector Pricing Models
Python implementation of Digital Signal Intelligence pricing models for upstream, midstream, and downstream energy coverages.

## Overview
These models implement automated insurance pricing based on digital footprint analysis for energy sector companies. The models support six coverage types across three energy segments.

### Installation

``` bash
# Clone repository
git clone https://github.com/jwalker618/digital-signal-intelligence.git
cd digital-signal-intelligence/models/energy
 
# Install dependencies
pip install -r requirements.txt
```

### Quick Start
```python

from dsi_energy_pricing import (
    CompanyProfile, DigitalSignals, EnergySegment,
    create_pricing_models
)

# Create company profile
company = CompanyProfile(
    company_name="Example Energy Corp",
    segment=EnergySegment.UPSTREAM,
    country="United States",
    annual_revenue=5_000_000_000,
    employees=12000,
    years_operating=25,
    public_traded=True,
    state_owned=False,
    signals=DigitalSignals(
        ssl_score=85,
        transparency_score=78,
        domain_authority=82,
        # ... other signals
    )
)

# Create pricing models
models = create_pricing_models(EnergySegment.UPSTREAM)

# Price all coverages
for coverage_name, model in models.items():
    result = model.price(company)
    print(f"{coverage_name}: ${result.annual_premium:,.0f}")
```

## Model Architecture
### Three Energy Segments
#### Upstream (Exploration & Production)

* Operators Extra Expense (OEE)
* Control of Well (COW)
* Pollution Liability (POLL)
* Property Damage (PD)
* Business Interruption (BI)
* General Liability (GL)

#### Midstream (Transportation & Storage)

* Operators Extra Expense (OEE)
* Pollution Liability (POLL)
* Property Damage (PD)
* Business Interruption (BI)
* General Liability (GL)

#### Downstream (Refining & Distribution)

* Operators Extra Expense (OEE)
* Pollution Liability (POLL)
* Property Damage (PD)
* Business Interruption (BI)
* General Liability (GL)

#### Four Signal Categories
Each with 6 individual metrics (24 total signals):

1/. Infrastructure Signals (20-30% weight)
* SSL certificate status
* Security headers implementation
* Domain age
* Technology stack modernity
* Uptime reliability
* Mobile optimization

2/. Content Signals (22-32% weight)
* Update frequency
* Transparency score
* Governance disclosure
* Multilingual presence
* Certification visibility
* Incident response protocols

3/. Network Signals (25-35% weight)
* Backlink quality
* Domain authority
* Industry citations
* Partnership quality
* Social engagement
* Supplier diversity

4/. Behavioral Signals (25-30% weight)
* Digital transformation
* Innovation signals
* Operational consistency
* Compliance history
* Investor relations sophistication
* Sustainability commitment

## Pricing Formula
```
Technical Rate = Base Rate × DSI Modifier × Size Modifier × 
                 Territory Modifier × Loss History Modifier

Annual Premium = Technical Rate × Exposure Base
```

### DSI Modifier Calculation
Composite Score (0-1000) = Weighted average of four signal categories

#### Score-Based Modifiers:
* 750-1000: 0.70-0.85x (Preferred)
* 650-750: 0.85-1.00x (Standard)
* 500-650: 1.00-1.25x (Elevated)
* 0-500: 1.25-1.75x (High Risk)

#### Exposure Base Calculation
* Upstream: Revenue / $1M (or production volume proxy)
* Midstream: Pipeline miles × $100K (or revenue / $1M)
* Downstream: Refining capacity × $50K (or revenue / $1M)

## Risk Tiers
| Tier | Score Range | Description | Recommendation|
|------|-------------|-------------|---------------|
|Tier 1|750-1000|Preferred|Auto-Approve - Preferred Pricing|
|Tier 2|650-750|Standard|Auto-Approve - Standard Pricing|
|Tier 3|500-650|Elevated|Manual Review Required|
|Tier 4|0-500|High Risk|Decline or Heavy Manual Review|

### Example Output
```
DSI PRICING ANALYSIS: Petróleo Brasileiro S.A.
================================================================================
Segment: UPSTREAM
Composite DSI Score: 742/1000

OEE Coverage:
  Base Rate: $1,250.00 per $1M
  DSI Modifier: 0.748x
  Technical Rate: $845.32 per $1M
  Exposure Base: $102,000M
  Annual Premium: $86,222,640
  Risk Tier: Tier 1 - Preferred
  Confidence: 95%
  Expected LR: 48.3%
  Recommendation: Auto-Approve - Preferred Pricing
  Reasoning: Exceptional digital maturity (score: 742). Strong signals across 
             all categories indicate robust operational discipline and risk 
             management. Expected LR: 48.3%.
```

#### Usage Examples
##### Example 1: Price Single Coverage
``` python
from dsi_energy_pricing import UpstreamPricingModel, CoverageType

# Create model for Control of Well coverage
model = UpstreamPricingModel(CoverageType.CONTROL_OF_WELL)

# Price the company
result = model.price(company)

print(f"Premium: ${result.annual_premium:,.0f}")
print(f"Recommendation: {result.recommendation}")
```

#### Example 2: Batch Pricing Multiple Companies
``` python
import pandas as pd

companies = [company1, company2, company3]
models = create_pricing_models(EnergySegment.UPSTREAM)

results = []
for company in companies:
    for cov_name, model in models.items():
        result = model.price(company)
        results.append({
            'Company': result.company_name,
            'Coverage': result.coverage,
            'Premium': result.annual_premium,
            'Score': result.composite_score,
            'Recommendation': result.recommendation
        })

df = pd.DataFrame(results)
df.to_csv('pricing_results.csv', index=False)
```

#### Example 3: Signal Sensitivity Analysis
```  python
# Test impact of different signal levels
base_signals = company.signals

for transparency in [30, 50, 70, 90]:
    test_signals = DigitalSignals(**base_signals.__dict__)
    test_signals.transparency_score = transparency
    
    test_company = CompanyProfile(**company.__dict__)
    test_company.signals = test_signals
    
    result = model.price(test_company)
    print(f"Transparency {transparency}: Premium ${result.annual_premium:,.0f}")
```

## Data Integration
### Input Data Sources
Models expect digital signals to be populated from:

1/. Infrastructure Signals: SSL Labs API, SecurityHeaders.com, Shodan
2/. Content Signals: Web scraping, NLP analysis, manual review
3/. Network Signals: Ahrefs API, Moz API, Common Crawl
4/. Behavioral Signals: Historical snapshots, news analysis, SEC filings


### Sample Data Pipeline
``` py
# Pseudocode for data pipeline
def collect_digital_signals(company_domain):
    signals = DigitalSignals()
    
    # Infrastructure
    signals.ssl_score = check_ssl_certificate(company_domain)
    signals.security_headers = analyze_security_headers(company_domain)
    
    # Content
    signals.transparency_score = analyze_content_transparency(company_domain)
    signals.update_frequency = calculate_update_frequency(company_domain)
    
    # Network
    signals.domain_authority = get_moz_domain_authority(company_domain)
    signals.backlink_quality = analyze_backlink_profile(company_domain)
    
    # Behavioral
    signals.compliance_history = check_regulatory_filings(company_name)
    signals.operational_consistency = analyze_historical_snapshots(company_domain)
    
    return signals
```

## Model Validation
### Backtesting Approach
```  py
from dsi_energy_pricing import validate_model

# Load historical data
historical_data = pd.read_csv('historical_losses_2019_2024.csv')

# Backtest model
validation_results = validate_model(
    model=UpstreamPricingModel(CoverageType.CONTROL_OF_WELL),
    historical_data=historical_data,
    test_period='2022-2024'
)

print(f"Gini Coefficient: {validation_results.gini:.3f}")
print(f"Top Quintile LR: {validation_results.top_quintile_lr:.2%}")
print(f"Bottom Quintile LR: {validation_results.bottom_quintile_lr:.2%}")
```

### Expected Performance Metrics
* Gini Coefficient: Target > 0.35
* C-Statistic: Target > 0.65
* Top vs Bottom Quintile: 40%+ LR differential
* Calibration: Predicted vs actual LR within 5 points

## Customization
### Adjusting Base Rates
``` py
# Modify base rates
model.base_rates[("upstream", "COW")] = 4000.0  # Increase COW base rate

# Or load from external file
import json
with open('custom_rates.json', 'r') as f:
    model.base_rates = json.load(f)
```

### Adjusting Signal Weights
``` py
# Emphasize behavioral signals for upstream
model.weights["upstream"]["behavioral"] = 0.35
model.weights["upstream"]["network"] = 0.30
Custom Signal Calculations
pythonclass CustomUpstreamModel(UpstreamPricingModel):
    def calculate_dsi_modifier(self, signals):
        # Add custom logic
        modifier, score = super().calculate_dsi_modifier(signals)
        
        # Penalize low compliance scores more heavily
        if signals.compliance_history < 50:
            modifier *= 1.20
        
        return modifier, score
```

## API Integration
Models can be wrapped in REST API for integration:
``` py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/price', methods=['POST'])
def price_coverage():
    data = request.json
    
    # Parse input
    company = CompanyProfile(**data['company'])
    segment = EnergySegment(data['segment'])
    coverage = CoverageType(data['coverage'])
    
    # Create model and price
    if segment == EnergySegment.UPSTREAM:
        model = UpstreamPricingModel(coverage)
    elif segment == EnergySegment.MIDSTREAM:
        model = MidstreamPricingModel(coverage)
    else:
        model = DownstreamPricingModel(coverage)
    
    result = model.price(company)
    
    return jsonify({
        'premium': result.annual_premium,
        'recommendation': result.recommendation,
        'score': result.composite_score,
        'confidence': result.confidence_level
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Testing
``` bash
# Run unit tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=dsi_energy_pricing --cov-report=html
```

## Performance Considerations
* Signal Collection: Cache results for 7 days to reduce API calls
* Batch Processing: Use multiprocessing for large portfolios
* Memory: Models use ~50MB RAM per instance
* Speed: ~50ms per pricing calculation on standard hardware

## Limitations
* Data Coverage: Requires sufficient digital footprint (60%+ signals populated)
* Emerging Markets: Limited effectiveness for companies with minimal web presence
* Private Companies: May have less public digital information
* Real-Time: Signals updated on schedule (weekly/monthly), not real-time

