# Digital Signal Intelligence (DSI) for Insurance Pricing

**A production-ready framework for automated underwriting using digital footprint analysis and network intelligence.**

DSI applies the principles that made Google's PageRank revolutionary—inferring quality from observable network relationships—to insurance underwriting. A company's digital presence serves as a powerful proxy for operational maturity, governance quality, and risk management capability.

---

## The Core Insight

Traditional underwriting relies on what companies *tell us*. DSI focuses on what companies *show us*.

Every organisation leaves a digital footprint: how they maintain their infrastructure, who they connect with, what they disclose, how they respond to incidents. These observable signals correlate strongly with the operational discipline and risk management maturity that drive loss outcomes.

**The insight is simple**: Companies that maintain excellent digital hygiene rarely have poor operational discipline. Companies with robust security infrastructure rarely have weak governance. Companies with high-quality network relationships rarely have hidden counterparty risks.

DSI systematically harvests these signals, scores them consistently, and converts them into pricing decisions—automating 75-85% of underwriting while simultaneously improving risk selection.

---

## Why This Matters

### The Problem with Traditional Underwriting

| Challenge | Traditional Approach | DSI Approach |
|-----------|---------------------|--------------|
| **Information asymmetry** | Rely on broker submissions | Verify independently from public sources |
| **Inconsistent assessment** | Varies by underwriter | Algorithmic consistency |
| **Costly per-risk analysis** | $650+ per submission | $72 per submission |
| **Slow turnaround** | Days to weeks | Minutes to hours |
| **Limited scalability** | Constrained by headcount | Infinitely scalable |
| **Adverse selection** | Often invisible | Detected via signal patterns |

### The Business Case

| Metric | Impact |
|--------|--------|
| Combined Ratio Improvement | 26-34 points |
| 5-Year Cumulative Profit | $275-350M |
| Return on Investment | 1,800%+ |
| Straight-Through Processing | 75-85% of submissions |
| Cost per Submission | $72 (vs $650 traditional) |

---

## How DSI Works

### The Three-Pillar Model

DSI augments (not replaces) traditional underwriting by adding a third analytical dimension:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DSI PRICING FRAMEWORK                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   PILLAR 1              PILLAR 2              PILLAR 3              │
│   Loss History          Loss Prevention       Digital Signals       │
│   (Traditional)         (Enhanced)            (Revolutionary)       │
│                                                                     │
│   • Claims data         • Control adequacy    • Infrastructure      │
│   • Frequency/severity  • Risk engineering    • Content/Disclosure  │
│   • Trends              • Compliance          • Network Quality     │
│                         • Certifications      • Behavioral Patterns │
│                                                                     │
│   ───────────────────────────────────────────────────────────────── │
│                              ↓                                      │
│                    UNIFIED DSI SCORE (0-1000)                       │
│                              ↓                                      │
│                    TIER ASSIGNMENT (1-5)                            │
│                              ↓                                      │
│                    PRICING DECISION                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### The Seven Signal Types

DSI organises signals into seven categories, each capturing different aspects of organisational quality:

| Type | Name | What It Measures | Example Signals |
|------|------|------------------|-----------------|
| **1** | Network Authority | Who trusts this entity | Customer quality, partner ecosystem, certifications |
| **2** | Technical Infrastructure | How they build and maintain | Security headers, TLS config, email authentication |
| **3** | Asset Telemetry | Third-party assessments | Security ratings, vulnerability scans, dark web presence |
| **4** | Structured Data | Industry benchmarks | Credit ratings, ESG scores, regulatory standing |
| **5** | Corporate Footprint | How they present themselves | Security pages, leadership visibility, hiring patterns |
| **6** | Public Records | What history reveals | Breach history, regulatory actions, litigation |
| **7** | Direct Inquiry | What they tell us (optional) | Questionnaire responses, attestations |

### Signal → Score → Tier → Price

```
Raw Signals                 Normalised Scores           Tier Assignment
─────────────               ─────────────────           ───────────────
TLS Grade: A+         →      95/100                      
Security Headers: 6/7 →      86/100              →       Tier 2
DMARC: Enforced       →      100/100                     (Standard)
Breach History: 1     →      60/100                      
...                         ...                         
                                                        ↓
                            Weighted Average            
                            = 742/1000           →      0.95x Premium
                                                        Auto-approve
```

### Tier Definitions

| Tier | Score Range | Risk Level | Recommended Action |
|------|-------------|------------|-------------------|
| **1** | 800-1000 | Preferred | Auto-approve, potential discount |
| **2** | 650-799 | Standard | Auto-approve at standard pricing |
| **3** | 500-649 | Elevated | Manual review, +15-30% loading |
| **4** | 350-499 | High Risk | Senior review, +30-60% loading |
| **5** | 0-349 | Critical | Decline or special terms only |

---

## Coverage Lines Supported

DSI is designed as a multi-line platform. Each coverage type has tailored signal weights and sector adjustments:

### Currently Implemented

| Coverage | Key Signal Focus | Primary Use Case |
|----------|-----------------|------------------|
| **Cyber** | Technical infrastructure, breach history, security posture | Tech, Healthcare, Retail |
| **Financial Institutions** | Regulatory standing, network authority, governance | Banks, Asset Managers, FinTech |
| **Energy** | OT/IT convergence, safety culture, operational discipline | Upstream, Midstream, Downstream |
| **Marine** | Classification society, flag state, operator quality | Hull, Cargo, P&I |
| **Directors & Officers** | Governance transparency, litigation patterns, ESG | Public companies, PE-backed |
| **Professional Indemnity** | TBC | TBC |
| **Aerospace** | TBC | TBC |

### Extensible Architecture

New coverage lines can be added by registering signal weights:

```python
CoverageLineRegistry.register(
    coverage_type=CoverageType.PROFESSIONAL_INDEMNITY,
    name="Professional Indemnity",
    signal_weights={
        'network_authority': 0.20,
        'technical_infrastructure': 0.10,
        'structured_data': 0.25,
        'corporate_footprint': 0.25,
        'public_records': 0.20,
    }
)
```

---

## Repository Structure

```
dsi-insurance-pricing/
│
├── api/
|
├── docs/
│   ├── Executive summary.pdf
│   ├── The PageRank precedent.pdf
|   ├── Foundational Principles.md
│   ├── An Agentic Future - Global Pricing Methodology.pdf
│   │
│   └── demos and case-studies/
|       ├──case_studies
|       |   ├──assessment case_studies.md
|       |   ├──retrospective case_study validation.md
|       |   └──retrospective executive summary.md
|       ├──demos
|       |   ├──dsi_demo_dashboard.html
|       |   └──dsi_portfolio_dashboard.html
|       └──validation
|           └──dsi_methodology.md
|
├── models/
│   ├── cyber/
│   │   └── dsi_cyber_pricing.py   
│   │
│   ├── d&o/
│   │   └── dsi_do_pricing.py   
│   │
│   ├── energy/
│   │   └── dsi_energy_pricing.py   
│   │
│   ├── financial_institutions/
│   │   └── dsi_fi_pricing.py   
│   │
│   ├── marine/
│   │   └── dsi_marine_pricing.py
│   │
│   ├── pi/
│   │   └── dsi_pi_pricing.py
│   │
│   ├── aerospace/
│   │   └── dsi_aerospace_pricing.py
│   │
│   ├── portfolio/
│   │   └── dsi_portfolio_analytics.py   
│   │
│   ├── signal_collection/
│   │   └── dsi_signal_collection.py   
│   │
│   ├── website_discovery/
│   │   └── dsi_website_discovery.py   
│
└── README.md
```

---

## Core Modules

### 1. Website Discovery (`models/website_discovery/dsi_website_discovery.py`)

Resolves the correct corporate website for any entity—a foundational step before signal collection.

```python
from website_discovery import WebsiteDiscoveryEngine

engine = WebsiteDiscoveryEngine()
result = engine.discover("MS Amlin", country_hint="UK")

print(result.primary_website.domain)  # → msamlin.com
print(result.confidence)              # → ConfidenceLevel.HIGH
print(result.company_identity.parent) # → MS&AD Insurance Group Holdings
```

**Key Features:**
- Multi-method discovery (DNS, search, registries)
- Parent/subsidiary resolution
- Confidence scoring with manual review flags
- Batch processing support

### 2. Signal Collection (`models/signal_collection/dsi_signal_collection.py`)

Harvests and scores signals from multiple sources into a unified DSI assessment.

```python
from signal_collection import create_signal_engine, ModelType

engine = create_signal_engine(ModelType.CYBER)
result = engine.collect("Petrobras", domain_hint="petrobras.com.br")

print(f"Score: {result.overall_score}/1000")  # → Score: 742/1000
print(f"Tier: {result.tier}")                  # → Tier: 2
print(f"Red Flags: {result.red_flags}")        # → Red Flags: []
```

**Key Features:**
- Modular collector architecture
- Model-specific signal weighting
- Multiple scoring methods (binary, linear, logarithmic, threshold)
- Red flag / green flag detection
- Quality-adjusted scoring

### 3. Portfolio Management (`models/portfolio/dsi_portfolio_analytics.py`)

The primary human interface—orchestrates all DSI functionality for portfolio-level oversight.

```python
from portfolio_management import DSIPortfolioManager, CoverageType

manager = DSIPortfolioManager()

# Add risks
manager.add_risk("Acme Corp", CoverageType.CYBER, metadata=metadata, assessment=assessment)

# Get portfolio metrics
metrics = manager.calculate_metrics()
print(f"Average Score: {metrics.average_score}")
print(f"Tier Distribution: {metrics.risks_by_tier}")

# Check alerts
alerts = manager.get_active_alerts(severity=AlertSeverity.HIGH)

# Natural language query
results = manager.query("show me tier 4 cyber risks")

# Generate dashboard
dashboard = manager.generate_dashboard()
```

**Key Features:**
- Multi-line portfolio management
- Real-time alerting (concentration, deterioration, tier migration)
- Natural language queries
- Drill-down analysis and peer comparison
- Scenario modeling ("what-if" analysis)
- Export to JSON/CSV

---

## Validation Evidence

DSI has been validated through retrospective analysis demonstrating predictive power:

### Petrobras vs PEMEX Comparison

| Dimension | Petrobras (742) | PEMEX (542) | DSI Correctly Predicted |
|-----------|-----------------|-------------|------------------------|
| Digital transformation | Major 2022-2023 overhaul | Stagnant since 2018 | ✓ Operational trajectory |
| Governance transparency | 847/1000 | 423/1000 | ✓ D&O risk differential |
| Network quality | Blue-chip partners | Intermediated relationships | ✓ Counterparty risk |
| Security posture | Modern, maintained | Legacy, patchy | ✓ Cyber exposure |

**Outcome**: Petrobras has had no material governance incidents since 2016. PEMEX has faced ongoing regulatory scrutiny, credit downgrades, and operational challenges. DSI scores from 2020 would have correctly differentiated these risks.

### Statistical Validation

Retrospective analysis across multiple sectors shows:
- **Tier 1-2 companies**: 67% lower loss frequency than Tier 4-5
- **Score correlation with loss ratio**: r = -0.42 (statistically significant)
- **Red flag accuracy**: 78% of companies with 3+ red flags experienced material events within 24 months

---

## Getting Started

### Prerequisites

- Python 3.9+
- Modern web browser (for dashboards)

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/dsi-insurance-pricing.git
cd dsi-insurance-pricing

# Install dependencies
pip install -r requirements.txt
```

### Quick Start

```python
from signal_collection import create_signal_engine, ModelType
from portfolio_management import DSIPortfolioManager, CoverageType

# Assess a single risk
engine = create_signal_engine(ModelType.CYBER)
assessment = engine.collect("Target Company", domain_hint="targetcompany.com")
print(f"DSI Score: {assessment.overall_score}, Tier: {assessment.tier}")

# Manage a portfolio
portfolio = DSIPortfolioManager()
portfolio.add_risk("Target Company", CoverageType.CYBER, assessment=assessment)
dashboard = portfolio.generate_dashboard()
```

### View Interactive Dashboards

Open any `.html` file in `docs/demos and case_studies/demos/` directly in a browser:
- `DSI_Dashboard_v2.html` - Signal-level analysis
- `DSI_Portfolio_Dashboard.html` - Portfolio management interface

---

## Implementation Roadmap

### Phase 1: Proof of Concept (6 months)
- D&O validation with 5,000+ company retrospective
- Statistical validation of signal-loss correlation
- API infrastructure build-out
- **Investment**: $0.8-1.2M

### Phase 2: Multi-Coverage Expansion (6 months)
- Extend to Cyber, E&O, Credit
- Real-time monitoring capabilities
- System integration with underwriting platforms
- **Investment**: $1.5-2.2M

### Phase 3: Full Automation (12 months)
- Zero-touch workflow for Tier 1-2 risks
- Global deployment across all regions
- ML optimization of signal weights
- **Investment**: $2.5-3.5M

**Total 24-Month Investment**: $4.8-6.9M  
**Expected 36-Month ROI**: 300-500%

---

## Key Documents

| Document | Purpose | Audience |
|----------|---------|----------|
| [Executive One-Pagers](docs/overview/Executive%20summary.pdf ) | Board-level summary | C-Suite, Board |
| [PageRank Precedent](docs/overview/The%20PageRank%20precedent.pdf) | Board-level summary | C-Suite, Board |
| [White Paper](docs/overview/An%20Agentic%20Future%20-%20Global%20Technical%20Pricing.pdf) | Detailed Explanation | Technical leadership |
| [DSI Principles](docs/overview/Foundational%20Principles.md) | Core methodology | Technical leadership |
| [Methodology Defense](docs/demos%20and%20case_studies/validation/dsi_methodology.md) | Actuarial Q&A | Actuaries, Risk |
| [Case Studies](docs/demos%20and%20case_studies/case-studies/) | Worked examples | Underwriters |
| [Demos](docs/demos%20and%20case_studies/demos/) | Examples | All stakeholders |

---

## Frequently Asked Questions

**Q: Does DSI replace underwriters?**  
A: No. DSI automates routine decisions (Tier 1-2) so underwriters can focus on complex risks (Tier 3-5) where human judgment adds value.

**Q: How is this different from SecurityScorecard/BitSight?**  
A: Those tools provide *inputs* to DSI. DSI is a complete *pricing framework* that converts signals into underwriting decisions with actuarially-grounded tier assignments.

**Q: What if a company has no digital presence?**  
A: Lack of digital presence is itself a signal (and typically a negative one). DSI handles this through confidence scoring and manual review flagging.

**Q: How do you prevent gaming?**  
A: Signal diversity (50+ signals across 7 types), behavioral analysis (patterns over time), and cross-validation make gaming impractical.

**Q: Is this compliant with insurance regulations?**  
A: DSI uses only publicly available data and produces explainable, auditable decisions. The methodology is designed to meet regulatory requirements for pricing transparency.

---

## Contributing

We welcome contributions in the following areas:
- New signal collectors for additional data sources
- Coverage line configurations for new product types
- Validation studies with historical loss data
- Dashboard and visualisation improvements

---

## License

Proprietary - Internal Use Only

---

## Contact

For questions about DSI implementation or methodology:
- John Walker
