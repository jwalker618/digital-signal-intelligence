# DSI Cyber Insurance Pricing Model
Comprehensive cyber insurance pricing based on digital security posture analysis and vulnerability assessment.

## Overview
This model implements automated cyber insurance pricing using Digital Signal Intelligence (DSI) with particular emphasis on vulnerability indicators, security maturity, and breach probability estimation. Unlike traditional cyber underwriting that relies heavily on questionnaires, this model automatically extracts security signals from the digital footprint.

## Installation
```bash
cd digital-signal-intelligence/models/cyber
pip install -r requirements.txt
```

## Quick Start
```python
from dsi_cyber_pricing import (
    CyberCompanyProfile, CyberSecuritySignals,
    IndustryVertical, CompanySize, CyberCoverageType,
    CyberInsurancePricingModel
)

# Create company profile
company = CyberCompanyProfile(
    company_name="Example Corp",
    industry=IndustryVertical.TECHNOLOGY,
    country="United States",
    annual_revenue=50_000_000,
    employees=200,
    size_category=CompanySize.SMALL,
    records_stored=500_000,
    pii_volume="medium",
    signals=CyberSecuritySignals(
        ssl_certificate=90,
        known_vulnerabilities=85,
        security_certifications=80,
        # ... other signals
    )
)

# Create pricing model
model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

# Get pricing
result = model.price(company)
print(f"Premium: ${result.annual_premium:,.0f}")
print(f"Breach Probability: {result.breach_probability:.1%}")
print(f"Recommendation: {result.recommendation}")
```

## Model Architecture
### Coverage Types

1/. First-Party Coverage
* Data breach response costs
* Forensic investigation
* Legal consultation
* Notification costs
* Credit monitoring
* Business interruption
* Cyber extortion/ransomware

2/. Third-Party Coverage
* Privacy liability
* Network security liability
* Media liability
* Regulatory defense and penalties
* PCI-DSS fines
* Class action defense

3/. Comprehensive (Both First and Third Party)

### Five Signal Categories
1/. Infrastructure Security (20% weight)
* SSL certificate status and strength
* TLS version (1.3 = optimal)
* Security headers (HSTS, CSP, X-Frame-Options)
* DNSSEC implementation
* Email authentication (SPF, DMARC, DKIM)
* Web Application Firewall presence

2/. Vulnerability Indicators (30% weight) - CRITICAL
* Open ports exposure
* Outdated software detection
* Known CVEs (Common Vulnerabilities)
* Exposed databases
* Leaked credentials in breaches
* Historical breach incidents

3/. Organizational Maturity (20% weight)
* Security certifications (ISO 27001, SOC 2, etc.)
* Privacy policy quality and GDPR compliance
* Incident response plan visibility
* Bug bounty program participation
* Security team visibility (CISO, security engineers)
* Security awareness content

4/. Third-Party Risk (15% weight)
* Vendor security standards
* Supply chain transparency
* Cloud provider quality (AWS/Azure/GCP preferred)
* Third-party integration management
* Data processing agreements

5/. Behavioral Security (15% weight)
* Patch discipline and update frequency
* Security investment signals
* Employee training programs
* MFA adoption
* Backup and disaster recovery procedures
* Monitoring capabilities (SOC/SIEM)

### Industry Risk Multipliers
|Industry|Multiplier|Rationale|
|-|-|-
|Healthcare|1.50x|PHI sensitivity, HIPAA penalties|
|Financial Services|1.40x|High-value target, regulatory risk|
|Retail|1.25x|PCI compliance, customer data|
|Energy|1.20x|Critical infrastructure|
|Technology|1.15x|High-value intellectual property|
|Professional Services|1.10x|Client confidential data|
|Education|1.05x|Student data, lower maturity|
|Other|1.00x|Baseline|
|Manufacturing|0.95x|Lower data exposure|
|Government|0.90x|Security focus (but catastrophic if breached)|

### Pricing Formula
```
Technical Rate = Base Rate × Cyber Maturity Modifier × Vulnerability Modifier ×
                 Industry Modifier × Size Modifier × Data Sensitivity Modifier ×
                 IT Environment Modifier × Prior Incidents Modifier

Annual Premium = Technical Rate × Revenue ($M)
```

### Cyber Maturity Modifiers
|Composite Score|Modifier Range|Risk Profile|
|-|-|-|
|800-1000|0.60x|Exceptional security|
|700-800|0.70-0.80x|Strong security|
|600-700|0.80-0.95x|Good security|
|500-600|0.95-1.20x|Adequate security|
|400-500|1.20-1.60x|Weak security|
|0-400|1.60-2.50x|Poor security|

### Vulnerability Modifiers (Critical)
|Vulnerability Score|Modifier|Risk Level|
|-|-|-|
|90-100|0.70x|Very Low|
|80-90|0.80x|Low|
|70-80|0.95x|Moderate|
|60-70|1.10x|Elevated|
|50-60|1.30x|High|
|40-50|1.60x|Very High|
|0-40|2.00x|Critical|

### Risk Tiers
|Tier|Composite Score|Vulnerability Score|Decision|
|-|-|-|-|
|Tier 1|800+|85+|Auto-Approve - Preferred|
|Tier 2|700-800|75+|Auto-Approve - Standard|
|Tier 3|600-700|65+|Manual Review - Elevated|
|Tier 4|500-600|55+|Manual Review - High Risk|
|Tier 5|<500 or <50 vuln|<50|Decline or Critical Risk|

### Breach Probability Estimation
The model estimates annual breach probability based on:

```python
Base Probability = f(Composite Score)
  • 800+: 2%
  • 700-800: 5%
  • 600-700: 10%
  • 500-600: 18%
  • 400-500: 30%
  • <400: 45%

Adjusted = Base × Industry Multiplier × (1 + Prior Incidents × 0.40)
```

### Expected Loss Calculation
```
Breach Cost = (Records × $175/record × 10% exposure) +
              (Daily Revenue × 15 days downtime) +
              (Regulatory/Legal × 2.5x if third-party coverage)

Expected Loss = Breach Cost × Breach Probability
```

## Usage Examples
### Example 1: Technology Company with Strong Security
```python
strong_signals = CyberSecuritySignals(
    ssl_certificate=95, tls_version=100, security_headers=90,
    known_vulnerabilities=92, exposed_databases=100,
    security_certifications=90, mfa_adoption=95,
    # ... all other signals
)

tech_company = CyberCompanyProfile(
    company_name="SecureTech Inc",
    industry=IndustryVertical.TECHNOLOGY,
    annual_revenue=5_000_000_000,
    employees=1500,
    size_category=CompanySize.LARGE,
    records_stored=2_000_000,
    pii_volume="high",
    cloud_percentage=85,
    prior_incidents=0,
    signals=strong_signals
)

model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)
result = model.price(tech_company)

# Expected output:
# Premium: ~$450,000
# Breach Probability: 2-4%
# Recommendation: Auto-Approve - Preferred Pricing
```

### Example 2: Healthcare with Vulnerabilities
```python
vulnerable_signals = CyberSecuritySignals(
    ssl_certificate=75, tls_version=80,
    known_vulnerabilities=45,  # CRITICAL LOW SCORE
    exposed_databases=50,       # CRITICAL LOW SCORE
    leaked_credentials=40,      # CRITICAL LOW SCORE
    security_certifications=70,
    # ... other signals
)

healthcare = CyberCompanyProfile(
    company_name="Regional Hospital",
    industry=IndustryVertical.HEALTHCARE,
    annual_revenue=500_000_000,
    size_category=CompanySize.MEDIUM,
    phi_handler=True,  # HIPAA sensitive
    prior_incidents=1,
    signals=vulnerable_signals
)

result = model.price(healthcare)

# Expected output:
# Premium: $800,000+ (high due to vulnerabilities)
# Breach Probability: 35-45%
# Recommendation: Manual Review or Decline
# Conditions: Mandatory remediation of vulnerabilities
```

### Example 3: Batch Pricing Portfolio
```python
import pandas as pd

companies = [company1, company2, company3, ...]
model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

results = []
for company in companies:
    result = model.price(company)
    results.append({
        'Company': result.company_name,
        'Premium': result.annual_premium,
        'Score': result.composite_score,
        'Vulnerability': result.vulnerability_score,
        'Breach_Prob': result.breach_probability,
        'Recommendation': result.recommendation
    })

df = pd.DataFrame(results)
df.to_csv('cyber_pricing_results.csv', index=False)

# Portfolio analytics
print(f"Total Premium: ${df['Premium'].sum():,.0f}")
print(f"Avg Breach Prob: {df['Breach_Prob'].mean():.1%}")
print(f"Auto-Approve Rate: {(df['Recommendation'].str.contains('Auto-Approve').sum() / len(df)):.0%}")
```

### Example 4: Vulnerability Remediation Analysis
```python
# Show impact of fixing vulnerabilities
baseline_company = healthcare_company  # From Example 2

# Scenario: Fix critical vulnerabilities
improved_signals = CyberSecuritySignals(**baseline_company.signals.__dict__)
improved_signals.known_vulnerabilities = 85  # Patched
improved_signals.exposed_databases = 95      # Secured
improved_signals.leaked_credentials = 90     # Rotated

improved_company = CyberCompanyProfile(**baseline_company.__dict__)
improved_company.signals = improved_signals

baseline_result = model.price(baseline_company)
improved_result = model.price(improved_company)

savings = baseline_result.annual_premium - improved_result.annual_premium
print(f"Baseline Premium: ${baseline_result.annual_premium:,.0f}")
print(f"Improved Premium: ${improved_result.annual_premium:,.0f}")
print(f"Annual Savings: ${savings:,.0f}")
print(f"ROI on Security Investment: {(savings / 100_000):.1f}x")  # Assume $100k remediation cost
```

## Data Collection
### Automated Signal Collection
The model expects signals to be populated from various sources:
```python
def collect_cyber_signals(domain: str, company_name: str) -> CyberSecuritySignals:
    """
    Automated signal collection pipeline
    """
    signals = CyberSecuritySignals()
    
    # Infrastructure (automated tools)
    ssl_result = check_ssl_labs(domain)
    signals.ssl_certificate = ssl_result['score']
    signals.tls_version = ssl_result['protocol_score']
    
    headers = check_security_headers(domain)
    signals.security_headers = calculate_header_score(headers)
    
    # Vulnerabilities (critical - multiple sources)
    shodan = query_shodan(domain)
    signals.open_ports_score = 100 - (len(shodan['open_ports']) * 5)
    
    nvd = check_nvd_vulnerabilities(domain, company_name)
    signals.known_vulnerabilities = 100 - (nvd['critical_count'] * 10)
    
    # Check breach databases
    breach_check = query_haveibeenpwned_domain(domain)
    signals.leaked_credentials = 100 if not breach_check else 50
    
    # Organizational (web scraping + APIs)
    certifications = extract_certifications(domain)
    signals.security_certifications = score_certifications(certifications)
    
    # Third-party (vendor analysis)
    tech_stack = get_builtwith(domain)
    signals.cloud_provider_quality = score_cloud_providers(tech_stack)
    
    # Behavioral (historical analysis)
    historical = get_wayback_snapshots(domain)
    signals.patch_discipline = analyze_update_frequency(historical)
    
    return signals
```

## Data Sources
### Free/Low-Cost:
* SSL Labs API (SSL/TLS assessment)
* SecurityHeaders.com (HTTP header analysis)
* Shodan (open ports, exposed services)
* Have I Been Pwned (breach checking)
* Common Crawl (historical web data)
* Certificate Transparency logs

### Commercial:
* SecurityScorecard ($5-15K/year)
* BitSight ($10-25K/year)
* RiskRecon by Mastercard
* UpGuard
* CyberGRX
* Black Kite

### Industry Databases:
* NVD (National Vulnerability Database)
* CVE (Common Vulnerabilities and Exposures)
* MITRE ATT&CK Framework
* NIST Cybersecurity Framework

## Model Validation
### Backtesting Against Historical Breaches
```python
# Load known breach data
breaches = pd.read_csv('historical_cyber_losses_2020_2024.csv')

# Score companies retrospectively
for idx, breach in breaches.iterrows():
    company = create_company_from_breach_data(breach)
    result = model.price(company)
    
    breaches.loc[idx, 'predicted_probability'] = result.breach_probability
    breaches.loc[idx, 'predicted_loss'] = result.expected_loss
    breaches.loc[idx, 'actual_loss'] = breach['total_cost']

# Calculate accuracy metrics
from sklearn.metrics import roc_auc_score

auc = roc_auc_score(breaches['breached'], breaches['predicted_probability'])
print(f"AUC-ROC: {auc:.3f}")  # Target: >0.70

# Loss prediction accuracy
mae = (breaches['predicted_loss'] - breaches['actual_loss']).abs().mean()
print(f"MAE: ${mae:,.0f}")
```

### Expected Performance
* AUC-ROC: Target >0.70 for breach prediction
* Top vs Bottom Quintile: 60%+ difference in breach rates
* Loss Prediction: Within 30% of actual for 70% of cases
* False Positive Rate: <15% for auto-approvals

## Customization
### Adjusting Base Rates by Market
```python
# Update for hard market conditions
model.base_rates["comprehensive"]["medium"] *= 1.35

# Or load from market data
import json
with open('current_market_rates.json', 'r') as f:
    model.base_rates = json.load(f)
```

### Industry-Specific Adjustments
```python
# Add new industry
model.industry_multipliers[IndustryVertical.CRYPTOCURRENCY] = 1.65

# Adjust for local market
if company.country == "United Kingdom":
    model.industry_multipliers[IndustryVertical.FINANCIAL_SERVICES] *= 0.95
```

### Custom Vulnerability Thresholds
```python
class StrictCyberModel(CyberInsurancePricingModel):
    def calculate_vulnerability_modifier(self, signals):
        modifier, score = super().calculate_vulnerability_modifier(signals)
        
        # Stricter thresholds for healthcare
        if self.current_company.industry == IndustryVertical.HEALTHCARE:
            if score < 75:  # Require higher bar
                modifier *= 1.40
        
        return modifier, score
```

## API Integration
```python
from flask import Flask, request, jsonify

app = Flask(__name__)
model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

@app.route('/api/cyber/quote', methods=['POST'])
def get_quote():
    data = request.json
    
    # Parse company data
    company = CyberCompanyProfile(
        company_name=data['company_name'],
        industry=IndustryVertical(data['industry']),
        annual_revenue=data['revenue'],
        # ... map all fields
    )
    
    # Collect signals (or use provided)
    if 'signals' in data:
        company.signals = CyberSecuritySignals(**data['signals'])
    else:
        company.signals = collect_cyber_signals(data['domain'], data['company_name'])
    
    # Price
    result = model.price(company, requested_limit=data.get('requested_limit'))
    
    return jsonify({
        'premium': result.annual_premium,
        'limit': result.policy_limit,
        'deductible': result.deductible,
        'breach_probability': result.breach_probability,
        'recommendation': result.recommendation,
        'conditions': result.conditions,
        'composite_score': result.composite_score,
        'vulnerability_score': result.vulnerability_score
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
```

## Testing
```bash
# Run full test suite
python -m pytest tests/test_dsi_cyber_pricing.py -v

# Run specific test category
python -m pytest tests/test_dsi_cyber_pricing.py::TestVulnerabilityAssessment -v

# Run with coverage
python -m pytest tests/ --cov=dsi_cyber_pricing --cov-report=html
```

## Performance Considerations
* Signal Collection: Most expensive operation (3-5 seconds per company with API calls)
* Pricing Calculation: <50ms per company
* Batch Processing: Use multiprocessing for portfolios >1000 companies
* Caching: Cache signal results for 24-48 hours to reduce API costs

## Limitations
* Data Availability: Requires 55%+ signal coverage for reliable pricing
* Private Companies: May have limited public security posture data
* Emerging Technologies: Cryptocurrency, AI companies may lack historical data
* APT Threats: Advanced persistent threats may not show in automated scans
* Zero-Days: Unknown vulnerabilities not captured in scoring

## Regulatory Compliance
### Rate Filing Considerations
* Document actuarial basis for all modifiers
* Demonstrate predictive validity through backtesting
* Ensure no prohibited factors (race, gender, etc.) proxied
* Provide clear disclosure of data sources
* Allow for alternative underwriting path

### Data Privacy
* Only use publicly available security data
* No personal employee data collection
* Comply with GDPR/CCPA for data processing
* Provide transparency into scoring methodology
