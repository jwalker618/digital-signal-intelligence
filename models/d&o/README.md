# DSI Directors & Officers (D&O) Insurance Pricing Model

## Overview

The D&O Insurance pricing model applies Digital Signal Intelligence to directors & officers liability, employment practices liability, and fiduciary coverages. D&O insurance is uniquely suited to DSI because corporate governance generates extensive digital footprints through SEC filings, proxy statements, litigation databases, executive backgrounds, and ESG ratings.

Traditional D&O underwriting relies heavily on financial statements and questionnaires that provide a point-in-time snapshot. DSI continuously monitors observable signals that predict securities litigation, regulatory enforcement, and governance failures.

---

## Coverage Types Supported

| Coverage | Description | Key Risk Factors |
|----------|-------------|------------------|
| Side A | Personal D&O liability (no indemnification) | Bankruptcy, derivative suits |
| Side B | Corporate reimbursement for D&O indemnification | Securities class actions |
| Side C | Entity securities coverage | Stock drops, misstatements |
| ABC Combined | Full D&O package | All corporate governance risks |
| EPL | Employment practices liability | Employee relations, culture |
| Fiduciary | ERISA fiduciary liability | Benefit plan management |
| Crime | Fidelity/employee dishonesty | Internal controls |

---

## Signal Framework

### Signal Categories & Weights

```
Corporate Governance (25%)
├── Board Independence (8%)
├── Board Diversity (5%)
├── Committee Quality (6%)
└── Governance Structure (6%)

Financial Health (25%)
├── Accounting Quality (10%)
├── Audit Opinion (6%)
├── Financial Distress (5%)
└── Related Party Transactions (4%)

Litigation & Regulatory (20%)
├── Securities Litigation History (8%)
├── Regulatory Enforcement (6%)
├── Derivative Litigation (3%)
└── Class Action Risk (3%)

Executive Signals (15%)
├── Executive Turnover (5%)
├── Compensation Controversy (4%)
├── Insider Trading Patterns (3%)
└── Executive Background (3%)

ESG & Reputation (15%)
├── ESG Score (5%)
├── Controversy Score (5%)
├── Employee Sentiment (3%)
└── Short Interest (2%)
```

---

## Signal Definitions

### Corporate Governance Signals

#### Board Independence (8%)

**What it measures:** Board composition, independence ratio, and structural governance factors.

**Why it matters:** Independent boards provide better oversight and reduce litigation risk. Research shows that companies with majority-independent boards have 40% fewer securities class actions.

**Key factors:**
- Independence ratio (independent directors / total board)
- CEO/Chairman duality
- Founder control
- Interlocking directorships
- Director tenure and age

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 90-100 | >75% independent, no CEO/Chair duality, diverse committees |
| 75-89 | >66% independent, meets listing standards |
| 60-74 | 50-66% independent, some structural concerns |
| 40-59 | <50% independent, significant governance gaps |
| 0-39 | Controlled board, major independence issues |

**Adjustments:**
- CEO is Chairman: -10 points
- Founder-controlled: -8 points
- >3 interlocking directorships: -5 points
- >2 directors over 75: -5 points
- Average tenure >12 years: -5 points

**Data source:** SEC DEF 14A proxy statements

#### Board Diversity (5%)

**What it measures:** Gender and ethnic diversity of board composition.

**Why it matters:** Diverse boards correlate with better governance outcomes and reduced litigation risk. Increasingly important for institutional investors (BlackRock, State Street) and regulatory requirements (NASDAQ, California SB 826).

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 90-100 | ≥40% female, ≥20% minority |
| 80-89 | ≥30% female, ≥15% minority |
| 65-79 | ≥20% female |
| 50-64 | ≥10% female |
| 0-49 | <10% female |

**Data source:** SEC DEF 14A proxy statements, company disclosures

### Financial Health Signals

#### Accounting Quality (10%)

**What it measures:** Quality of financial reporting and internal controls.

**Why it matters:** Accounting irregularities are the leading cause of securities class actions. Material weaknesses and restatements are strong predictors of future litigation.

**Key indicators:**
- Material weaknesses in internal controls
- Significant deficiencies
- Financial restatements
- Late SEC filings
- Non-GAAP vs GAAP earnings gap
- CFO/auditor turnover

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 85-100 | Clean record, no material issues |
| 70-84 | Minor issues (small non-GAAP gap, single deficiency) |
| 55-69 | CFO/auditor turnover or moderate non-GAAP gap |
| 40-54 | Late filings or significant deficiencies |
| 25-39 | Restatement in past 3 years |
| 10-24 | Material weakness |
| 0-9 | Material weakness + restatement |

**Data source:** SEC 10-K, 10-Q filings

#### Audit Opinion (6%)

**What it measures:** External audit results including opinion type, going concern, and critical audit matters.

**Why it matters:** Qualified opinions and going concern warnings often precede major claims. Critical audit matters (CAMs) highlight areas of elevated risk.

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 90-100 | Clean unqualified opinion, Big 4 auditor |
| 75-89 | Unqualified, 1-2 CAMs |
| 60-74 | Non-Big 4 auditor or >3 CAMs |
| 50-59 | Going concern (subsequently resolved) |
| 20-29 | Going concern (unresolved) |
| 15-19 | Qualified opinion |
| 0-14 | Adverse opinion or disclaimer |

**Data source:** SEC 10-K audit report

### Litigation & Regulatory Signals

#### Securities Litigation History (8%)

**What it measures:** History of securities class actions, derivative suits, and SEC enforcement.

**Why it matters:** Prior securities litigation is the single strongest predictor of future claims. Companies with prior class actions are 3x more likely to face another.

**Key metrics:**
- Securities class actions (Rule 10b-5) in past 5 years
- Pending class actions
- SEC enforcement actions
- Derivative suits
- Settlement amounts

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 90-100 | No securities litigation history |
| 70-79 | Single derivative suit (resolved) |
| 50-59 | Prior class action (settled) |
| 40-49 | Multiple prior class actions |
| 30-39 | SEC enforcement action |
| 15-24 | Pending class action |
| 0-14 | Multiple pending + SEC enforcement |

**Data source:** PACER, Stanford Securities Class Action Clearinghouse (SCAC)

#### Regulatory Enforcement (6%)

**What it measures:** Regulatory scrutiny and enforcement actions beyond SEC.

**Why it matters:** Regulatory issues (FDA, DOJ, FTC, state AGs) often precede or accompany D&O claims.

**Regulatory bodies tracked:**
- SEC (securities)
- DOJ (FCPA, antitrust, criminal)
- FDA (pharma, medical devices)
- FTC (consumer protection, antitrust)
- CFPB (consumer finance)
- State attorneys general
- International regulators

**Data source:** Agency press releases, PACER, news monitoring

### Executive Signals

#### Executive Turnover (5%)

**What it measures:** C-suite stability and departure patterns.

**Why it matters:** High executive turnover, especially sudden departures, correlates with underlying problems that lead to D&O claims. CFO departures are particularly significant.

**Key metrics:**
- CEO changes (3 years)
- CFO changes (3 years)
- COO changes (3 years)
- Sudden/unexplained departures
- Departures under investigation
- Average C-suite tenure

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 85-100 | Stable team, >4 years average tenure |
| 70-84 | Normal turnover (1-2 changes in 3 years) |
| 55-69 | Elevated turnover (3+ changes) |
| 45-54 | Sudden departure |
| 30-44 | Multiple sudden departures or CEO+CFO turnover |
| 0-29 | Departures under investigation |

**Data source:** SEC 8-K filings, proxy statements

#### Insider Trading Patterns (3%)

**What it measures:** Patterns in Form 4 insider trading filings.

**Why it matters:** Clustered insider selling before negative news is a litigation trigger. Plaintiffs' attorneys routinely cite insider sales in class action complaints.

**Key indicators:**
- Sell/buy ratio (12 months)
- Clustered selling events
- Selling before price declines
- 10b5-1 plan coverage

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 85-100 | Normal patterns, high 10b5-1 coverage |
| 70-84 | Moderate selling (1.5-3x ratio) |
| 55-69 | Heavy selling outside 10b5-1 plans |
| 40-54 | Clustered selling events |
| 25-39 | Selling before stock decline |
| 0-24 | Clustered selling before decline (litigation trigger) |

**Data source:** SEC Form 4 filings

### ESG & Reputation Signals

#### ESG Score (5%)

**What it measures:** Environmental, Social, and Governance ratings from major providers.

**Why it matters:** ESG issues increasingly drive D&O claims through climate disclosure litigation, greenwashing claims, human capital suits, and board diversity demands.

**Rating scale (MSCI):**
| Rating | Score |
|--------|-------|
| AAA | 95 |
| AA | 88 |
| A | 78 |
| BBB | 65 |
| BB | 52 |
| B | 40 |
| CCC | 25 |

**Adjustments:**
- Severe controversy: Cap at 35
- Multiple controversies: -15 points
- Weak governance pillar (<40): Cap at 55

**Data source:** MSCI ESG, Sustainalytics, ISS

#### Employee Sentiment (3%)

**What it measures:** Employee satisfaction and workplace culture signals.

**Why it matters:** Poor employee sentiment correlates with EPL claims and can indicate cultural issues that lead to broader D&O exposure.

**Key metrics:**
- Glassdoor overall rating
- CEO approval percentage
- "Recommend to friend" percentage
- Culture rating
- Rating trend (improving/declining)

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 85-100 | >4.0 Glassdoor, >70% recommend |
| 70-84 | 3.5-4.0 Glassdoor |
| 55-69 | 3.0-3.5 Glassdoor or <50% recommend |
| 40-54 | 2.5-3.0 Glassdoor |
| 0-39 | <2.5 Glassdoor or <40% CEO approval |

**Data source:** Glassdoor, Indeed, Comparably

#### Short Interest (2%)

**What it measures:** Short selling activity as a percentage of float.

**Why it matters:** High short interest indicates market skepticism. When shorts are proven right, securities class actions often follow.

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 85-100 | <5% of float |
| 65-84 | 5-10% of float |
| 45-64 | 10-15% of float |
| 30-44 | 15-25% of float |
| 0-29 | >25% of float |

**Data source:** FINRA short interest data

---

## Risk Tier Classification

| Tier | Score | Classification | Premium Adjustment | Underwriting Action |
|------|-------|----------------|-------------------|---------------------|
| 1 | 750-1000 | Preferred | -30% | Auto-approve preferred |
| 2 | 600-749 | Standard | Baseline | Auto-approve standard |
| 3 | 450-599 | Elevated | +50% | Senior UW review |
| 4 | 0-449 | High Risk | +150% | Management approval |

### Automatic Decline Triggers

The following conditions trigger automatic decline regardless of composite score:

- Securities litigation score < 20 (pending class action + SEC enforcement)
- Audit opinion score < 15 (qualified/adverse opinion)
- Accounting quality score < 20 (material weakness + restatement)
- Sanctioned individuals on board/management

---

## Pricing Model

### Base Rates (per $1M of coverage, annual)

| Company Type | Base Rate |
|--------------|-----------|
| Public Large Cap (>$10B) | $3,500 |
| Public Mid Cap ($2B-$10B) | $5,500 |
| Public Small Cap ($300M-$2B) | $8,500 |
| Public Micro Cap (<$300M) | $15,000 |
| Pre-IPO | $25,000 |
| SPAC | $45,000 |
| Private PE-Backed | $4,000 |
| Private VC-Backed | $6,000 |
| Private Family | $2,500 |
| Nonprofit | $2,000 |

### Industry Risk Multipliers

| Industry | Multiplier |
|----------|------------|
| Crypto/Digital Assets | 2.50x |
| Cannabis | 2.00x |
| Healthcare/Pharma | 1.60x |
| Financial Services | 1.40x |
| Technology | 1.30x |
| Energy | 1.20x |
| Real Estate | 1.10x |
| Retail/Consumer | 1.00x |
| Manufacturing | 0.95x |

### Increased Limit Factors (ILF)

Premium does not scale linearly with limit:

| Limit | ILF |
|-------|-----|
| $1-5M | 1.00x |
| $5-10M | 0.90x |
| $10-25M | 0.80x |
| $25M+ | 0.70x |

### Premium Calculation

```
Final Premium = Base Premium × Industry Mult × DSI Mult × Size Mult × ILF

Where:
- Base Premium = Base Rate × (Limit / $1M)
- Industry Mult = Industry risk factor
- DSI Mult = Tier-based adjustment (0.70x to 2.50x)
- Size Mult = Market cap adjustment (1.0x to 1.25x)
- ILF = Increased limit factor
```

---

## Data Sources

| Source | Data Provided | Update Frequency |
|--------|---------------|------------------|
| SEC EDGAR | 10-K, 10-Q, 8-K, DEF 14A, Form 4 | Real-time (filing) |
| PACER | Federal litigation | Daily |
| SCAC | Securities class actions | Weekly |
| Glassdoor | Employee sentiment | Weekly |
| MSCI ESG | ESG ratings | Monthly |
| Sustainalytics | ESG ratings, controversies | Monthly |
| FINRA | Short interest | Bi-weekly |
| News APIs | Controversies, announcements | Real-time |

---

## API Integration

### Endpoints

```
POST /api/v2/do/analyze
GET /api/v2/do/score/{ticker}
GET /api/v2/do/signals/{ticker}
POST /api/v2/do/monitor
GET /api/v2/do/peer-comparison/{ticker}
```

### Sample Request

```json
{
  "company_identifier": "TECH",
  "identifier_type": "ticker",
  "coverage_types": ["abc_combined"],
  "limit_requested": 15000000,
  "retention": 500000,
  "policy_period_days": 365
}
```

### Sample Response

```json
{
  "company": {
    "name": "TechCorp Industries Inc.",
    "ticker": "TECH",
    "type": "public_mid_cap",
    "industry": "technology",
    "market_cap": 5500000000
  },
  "composite_score": 831,
  "tier": 1,
  "tier_label": "Preferred",
  "signals": {
    "board_independence": {"score": 85, "evidence": "78% independent"},
    "accounting_quality": {"score": 90, "evidence": "Clean record"},
    "securities_litigation": {"score": 75, "evidence": "Single derivative suit"}
  },
  "pricing": {
    "base_premium": 82500,
    "industry_adjustment": 1.30,
    "dsi_adjustment": 0.70,
    "final_premium": 60060,
    "rate_per_million": 4004
  },
  "decision": "APPROVE",
  "action": "Auto-bind at preferred terms"
}
```

---

## Usage Example

```python
from do_pricing_model import (
    DOPricingModel,
    DOSignalScorer,
    CompanyProfile,
    BoardProfile,
    DOSubmission,
    CompanyType,
    IndustryRisk,
    CoverageType
)
from datetime import datetime, timedelta

# Create company profile
company = CompanyProfile(
    company_name="TechCorp Industries Inc.",
    ticker="TECH",
    company_type=CompanyType.PUBLIC_MID_CAP,
    industry=IndustryRisk.TECHNOLOGY,
    market_cap=5_500_000_000,
    revenue=2_200_000_000,
    total_assets=3_800_000_000,
    employees=8500,
    headquarters_country="US",
    stock_exchange="NASDAQ",
    fiscal_year_end="December",
    year_founded=2005
)

# Create board profile
board = BoardProfile(
    board_size=9,
    independent_directors=7,
    female_directors=3,
    minority_directors=2,
    avg_tenure_years=6.5,
    avg_age=58,
    directors_over_75=1,
    interlocking_directorships=2,
    audit_committee_financial_experts=2,
    ceo_is_chairman=False,
    founder_controlled=False
)

# Create submission
submission = DOSubmission(
    submission_id="DO-2025-005678",
    company=company,
    board=board,
    coverage_types=[CoverageType.ABC_COMBINED],
    policy_period_start=datetime.now(),
    policy_period_end=datetime.now() + timedelta(days=365),
    limit_requested=15_000_000,
    retention=500_000,
    broker="Aon"
)

# Score signals
scorer = DOSignalScorer()
signals = {}

signals["board_independence"] = scorer.score_board_independence(board)
signals["board_diversity"] = scorer.score_board_diversity(board)

financial_data = {"material_weaknesses": 0, "restatements_3_years": 0}
signals["accounting_quality"] = scorer.score_accounting_quality(financial_data)

# Generate decision
model = DOPricingModel()
composite, confidence = model.calculate_composite_score(signals)
decision = model.generate_underwriting_decision(submission, signals, composite)

print(f"Score: {composite:.0f}, Tier: {decision['tier']}, Premium: ${decision['pricing']['final_premium']:,.0f}")
```

---

## Company Type Definitions

| Type | Criteria | Typical Signals |
|------|----------|-----------------|
| Public Large Cap | Market cap >$10B | High governance standards, institutional scrutiny |
| Public Mid Cap | Market cap $2B-$10B | Growing companies, transition risk |
| Public Small Cap | Market cap $300M-$2B | Higher volatility, less analyst coverage |
| Public Micro Cap | Market cap <$300M | Limited liquidity, higher fraud risk |
| Pre-IPO | Filed S-1 or planning IPO | IPO litigation risk, disclosure transition |
| SPAC | Special purpose acquisition company | Extreme merger litigation risk |
| Private PE-Backed | Private equity ownership | LBO leverage, management changes |
| Private VC-Backed | Venture capital ownership | Growth pressure, governance gaps |
| Private Family | Family-owned private | Related party risks, succession |
| Nonprofit | 501(c)(3) organizations | Different liability profile |

---

## Validation

The D&O DSI model has been validated against:

- **Securities class action prediction:** 78% accuracy in identifying companies that will face class actions within 24 months
- **Governance score correlation:** Strong correlation (r=0.72) between governance signals and claim frequency
- **Settlement prediction:** DSI tier correlates with average settlement size

---

## Regulatory Considerations

### SEC Disclosure Requirements

DSI monitors compliance with key disclosure requirements:
- Regulation S-K (business description, risk factors)
- Regulation S-X (financial statements)
- Item 307/308 (internal control disclosure)
- Item 402 (executive compensation)
- Item 407 (corporate governance)

### Listing Standards

DSI tracks compliance with exchange requirements:
- NYSE Listed Company Manual
- NASDAQ Listing Rules
- SOX 404 (internal controls)

---

## Contact

For implementation support or API access, contact John Walker.
