# DSI Financial Institutions Pricing Model - Quick Reference

## Overview
Specialized pricing model for banks, asset managers, insurance companies, and other financial institutions with emphasis on regulatory compliance and governance.

## Key Features
### 10 Institution Types
Commercial Bank, Investment Bank, Asset Manager
Insurance Company, Broker-Dealer, Hedge Fund
Private Equity, Fintech, Credit Union, Payment Processor

### 7 Coverage Types
D&O (Directors & Officers)
EPL (Employment Practices Liability)
Fiduciary Liability
Crime (Financial Institution Bond)
E&O (Professional Liability)
Cyber Liability
Regulatory Defense

### 36 Specialized Signals (6 categories)
1/. Regulatory & Compliance (25% weight) - CRITICAL
* Regulatory disclosures, enforcement history
* Complaint resolution, licensing status
* Audit transparency, regulatory cooperation

2/. Governance & Leadership (20% weight)
* Board composition, management experience
* Compensation disclosure, succession planning
* Risk committee, ethics program

3/. Financial Transparency (20% weight)
* Financial reporting, auditor quality
* Financial stability, revenue transparency
* Risk disclosure, third-party ratings

4/. Operational Controls (15% weight)
* Compliance program, internal controls
* Vendor management, business continuity
* Incident reporting, insurance coverage

5/. Market & Reputation (10% weight)
* Media sentiment, client reviews
* Industry recognition, litigation history
* Regulatory citations, social responsibility

6/. Technology & Security (10% weight)
* Cybersecurity posture, technology investment
* Data protection, system resilience
* Innovation signals, RegTech adoption

## Unique Characteristics
### Regulatory Emphasis
* Regulatory score can override all other factors
* Multiple enforcement actions = automatic decline
* Clean regulatory record gives 30% credit

### Enforcement History Impact
```
0 actions:   0.95x modifier
1 action:    1.20x modifier
2 actions:   1.50x modifier
3+ actions:  2.00x modifier + likely decline
```

### Governance Critical for D&O
* Governance score weighted 30% higher for D&O coverage
* Poor governance (<50) with D&O = Tier 5 risk
* Board composition heavily weighted

### Jurisdiction Complexity
* US Federal (SEC): 1.25x
* Multiple jurisdictions: 1.40x
* Cross-border operations add 20% complexity

## Example Pricing Outputs
### Strong Regional Bank
* Composite: 820/1000
* Regulatory: 92/100
* Premium: $425K for $450M revenue
* Recommendation: Auto-Approve - Preferred
* Conditions: Standard annual questionnaire

### Hedge Fund with Issues
* Composite: 545/1000
* Regulatory: 48/100
* Premium: $1.8M for $200M revenue
* Recommendation: Manual Review - High Risk
* Conditions: Senior approval, remediation plan, enhanced monitoring
* Restrictions: Prior acts exclusions, sub-limits on regulatory defense

### Emerging Fintech
* Composite: 715/1000
* Regulatory: 75/100
* Premium: $285K for $75M revenue
* Recommendation: Auto-Approve - Standard
* Conditions: Quarterly regulatory updates, maintain compliance program

## Critical Decline Triggers
1/. Regulatory Score <50: Systemic compliance failure
2/. 3+ Enforcement Actions (5yr): Pattern of violations
3/. Settlement >$100M: Material regulatory breach
4/. Multiple Active Investigations: Ongoing scrutiny
5/. Governance Score <50 (D&O): Board dysfunction

## Data Sources
### Regulatory (Public)
* SEC EDGAR filings
* FINRA BrokerCheck
* OCC enforcement actions
* State regulatory databases
* FDIC actions

### Governance (Public)
* Proxy statements (DEF 14A)
* 10-K annual reports
* Board composition disclosures
* Executive biographies

### Financial (Public/Commercial)
* Audited financial statements
* Credit ratings (S&P, Moody's, Fitch)
* Analyst reports
* Regulatory capital filings

### Reputation (Public/Commercial)
* Media monitoring
* Litigation databases (PACER, state courts)
* Customer review platforms
* Industry rankings

## Usage Example
```python
from dsi_financial_pricing import (
    FinancialInstitutionProfile, FinancialInstitutionSignals,
    FinancialInstitutionType, FICoverageType, RegulatoryJurisdiction,
    FinancialInstitutionPricingModel
)

# Create institution profile
bank = FinancialInstitutionProfile(
    institution_name="Regional Bank",
    institution_type=FinancialInstitutionType.COMMERCIAL_BANK,
    primary_jurisdiction=RegulatoryJurisdiction.US_FEDERAL,
    revenue=450_000_000,
    total_assets=15_000_000_000,
    regulatory_actions_5yr=0,
    signals=FinancialInstitutionSignals(
        regulatory_disclosures=92,
        enforcement_history=100,
        board_composition=85,
        # ... other signals
    )
)

# Price D&O coverage
model = FinancialInstitutionPricingModel(FICoverageType.DNO)
result = model.price(bank)

print(f"Premium: ${result.annual_premium:,.0f}")
print(f"Regulatory Risk: {result.regulatory_action_probability:.1%}")
print(f"Decision: {result.recommendation}")
```

## Policy Structure Recommendations
### D&O Limits
* Based on 1-3% of revenue
* Minimum: $1M
* Typical range: $10M-$250M
* Mega banks: $500M+

### Deductibles
* 1.5-2.5% of limit
* Minimum: $25K
* Typical: $250K-$5M

### Retentions (Excess)
* 10% of limit
* Minimum: $500K
* Typical: $2M-$25M

## Key Differentiators from Other Models
* Regulatory Focus: 25% weight vs 15-20% in other models
* Enforcement History: Exponential impact vs linear
* Governance Premium: 30% higher weight for D&O
* Jurisdiction Complexity: Multi-regulator penalty
* Coverage Restrictions: Detailed exclusions for prior acts
* Confidence Threshold: Requires 65%+ vs 55% in other models
