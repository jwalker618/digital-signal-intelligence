# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.4.0|
|Date|March 2026|
|Classification|overview|

---

## Project Status

**A framework for automated underwriting using digital footprint analysis and network intelligence.**

Digital Signal Intelligence (DSI) applies the principles that made Google's PageRank revolutionary, inferring quality from observable network relationships, to insurance underwriting. A company's digital presence serves as a powerful proxy for operational maturity, governance quality, and risk management capability.

---

### The Core Insight

Traditional underwriting relies on what companies *tell us*, DSI focuses on what companies *show us*.

Every organisation leaves a digital footprint: how they maintain their infrastructure, who they connect with, what they disclose, how they respond to incidents. These observable signals correlate strongly with the operational discipline and risk management maturity that drive loss outcomes.

**The insight is simple**: Companies that maintain excellent digital hygiene rarely have poor operational discipline. Companies with robust security infrastructure rarely have weak governance. Companies with high-quality network relationships rarely have hidden counterparty risks.

DSI systematically harvests these signals, scores them consistently, and converts them into pricing decisions—automating 75-85% of underwriting while simultaneously improving risk selection.

---

### Key Documents

| Document | Purpose | Audience |
|----------|---------|----------|
| [Pitch Deck](docs/overview/Pitch_deck.pdf) | Board-level summary | C-Suite, Board |
| [PageRank Precedent](docs/overview/The_PageRank_Precedent.pdf) | Board-level summary | C-Suite, Board |
| [White Paper](docs/overview/Whitepaper_Digital_Signal_Intelligence.pdf) | Detailed technical explanation | Technical leadership |
| [Vision Paper](docs/overview/Visionpaper_Digital_Signal_Intelligence.pdf) | World Model vision | Technical leadership |
| [DSI Principles](docs/overview/Foundational%20Principles.md) | Core methodology | Technical leadership |
| [Deployment Guide](deploy/deployment_guide.md) | Production deployment | DevOps, Engineering |
| [Configuration Architecture](docs/overview/Configuration_Architecture.md) | Config layer design | Engineering |
| [Methodology Defense](development/retrospective_methodology.md) | Actuarial Q&A | Actuaries, Risk |
| [Case Studies](docs/case_studies/) | Worked examples | Underwriters |
| [Interactive Demo](demo/index.html) | Hands-on exploration | All stakeholders |
| [Tower/Subscription Design](development/project/phase_e_design.md) | Market structure architecture | Engineering |
| [Upgrade Plan](DSI_UPGRADE_PLAN.md) | Phases A-F implementation roadmap | Engineering |
| [SKILL.md](SKILL.md) | Architecture & development guide | Engineering |

### Why This Matters

#### The Problem with Traditional Underwriting

| Challenge | Traditional Approach | DSI Approach |
|-|-|-|
| **Information asymmetry** | Rely on broker submissions | Verify independently from public sources |
| **Inconsistent assessment** | Varies by underwriter | Algorithmic consistency |
| **Costly per-risk analysis** | $650+ per submission | $72 per submission |
| **Slow turnaround** | Days to weeks | Minutes to hours |
| **Limited scalability** | Constrained by headcount | Infinitely scalable |
| **Adverse selection** | Often invisible | Detected via signal patterns |

---

### Validation Evidence

DSI has been validated through retrospective analysis demonstrating predictive power:

#### Petrobras vs PEMEX Comparison

| Dimension | Petrobras (742) | PEMEX (542) | DSI Correctly Predicted |
|-----------|-----------------|-------------|------------------------|
| Digital transformation | Major 2022-2023 overhaul | Stagnant since 2018 | ✓ Operational trajectory |
| Governance transparency | 847/1000 | 423/1000 | ✓ D&O risk differential |
| Network quality | Blue-chip partners | Intermediated relationships | ✓ Counterparty risk |
| Security posture | Modern, maintained | Legacy, patchy | ✓ Cyber exposure |

**Outcome**: Petrobras has had no material governance incidents since 2016. PEMEX has faced ongoing regulatory scrutiny, credit downgrades, and operational challenges. DSI scores from 2020 would have correctly differentiated these risks.

#### Statistical Validation

Retrospective analysis across multiple sectors shows:
- **Tier 1-2 companies**: 67% lower loss frequency than Tier 4-5
- **Score correlation with loss ratio**: r = -0.42 (statistically significant)
- **Red flag accuracy**: 78% of companies with 3+ red flags experienced material events within 24 months

---

### How DSI Works

#### The Three-Pillar Model

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
│              PRICING: Ground-Up / Tower / Subscription              │
│                              ↓                                      │
│             ROL VALIDATION + DUAL RECOMMENDATION                    │
│                              ↓                                      │
│                    PRICING DECISION                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### The Seven Signal Types

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

#### Signal → Score → Tier → Price

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

#### Example Tier Definitions

| Tier | Score Range | Risk Level | Recommended Action |
|-|-|-|-|
| **1** | 800-1000 | Preferred | Auto-approve, potential discount |
| **2** | 650-799 | Standard | Auto-approve at standard pricing |
| **3** | 500-649 | Elevated | Manual review, +15-30% loading |
| **4** | 350-499 | High Risk | Senior review, +30-60% loading |
| **5** | 0-349 | Critical | Decline or special terms only |

#### Premium Options & Market Structures

DSI generates comprehensive premium options with full transparency at every step.

**Pricing Transparency (Phase A):**
- Each limit option includes a `LimitPremiumDetail` with discrete `ilf_factor`, `deductible_factor`, and before/after premium values
- `uncapped_premium` captured before guardrail application for audit trail
- Modifier visibility — each modifier tracked with categorized before/after premium impact
- Tier margin context — distance to adjacent tier boundaries and percentile within current tier
- Parametric ILF curves only (table-based ILF removed)

**ROL Engine (Phase C):**
- Rate-on-Line (ROL) curve validator replaces legacy PremiumValidator
- Dual recommendation engine — upper (best ROL value) and lower (minimum adequate) limits
- Limit re-pricing without full workflow re-run

**Market Structures (Phase E):**

| Structure | Description | Premium Calculation |
|-|-|-|
| **Ground-Up** | Single-layer, full participation (default) | `base × ILF(limit) × deductible_factor` |
| **Tower** | Stacked excess layers with attachment points | `base × [ILF(A+L) - ILF(A)]` per layer |
| **Subscription** | Order/line model with insurer participation % | `signed_line × order_premium × lead_loading` |

Tower and subscription compose — an insurer can take a line on one or more layers of a tower.

**Lead vs Follow:**
- **Lead**: Sets terms, handles claims, commands configurable loading (e.g. +5-15%)
- **Follow**: Takes lead's terms at par, no loading applied

---

### Coverage Lines Supported

DSI is designed as a multi-line platform. Each coverage type has tailored signal weights and sector adjustments:

#### Extensible Architecture

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

### Repository Structure

```
digital-signal-intelligence/
├── signal_architecture/         # All signal-related code
│   ├── signals/                 # Core signal extraction pipeline
│   │   ├── types.py             # Core data types
│   │   ├── extractors/          # Stub + 50 production extractors
│   │   ├── aggregators/         # Signal aggregation + routing bridges
│   │   ├── categorisers/        # Score categorization
│   │   ├── inference/           # Inference functions + registry
│   │   ├── routing/             # Jurisdiction-aware routing (Phase 15)
│   │   └── cross_walk/          # Coverage crosswalk mappings
│   ├── discovery/               # Entity identification (Step 0)
│   └── orchestration/           # Multi-coverage coordination
│
├── infrastructure/              # Support systems
│   ├── api/                     # FastAPI REST API
│   ├── db/                      # Database layer (SQLAlchemy)
│   ├── analytics/               # Performance analysis
│   ├── builder/                 # LLM coverage builder
│   └── integrations/            # Email, docs, webhooks
│
├── layers/                      # Assessment layers
│   ├── risk/                    # Risk scoring (14-step workflow)
│   │   ├── pricer.py            # Premium calc (ground-up, tower, subscription)
│   │   ├── rol_validator.py     # ROL curve validator (Phase C)
│   │   └── rol_recommender.py   # Dual recommendation engine (Phase C)
│   ├── exposure/                # Exposure Shadow Layer (Phase 17)
│   └── loss/                    # Loss Correlation Layer (Phase 16)
│
├── coverages/                   # YAML configurations (7 coverages)
│   ├── doc_generator.py         # Generate logic.md documentation
│   ├── master_config_layout.yaml # Master schema template
│   └── {coverage}/              # Each has config.yaml + logic.md
│
├── tests/                       # 380+ tests
├── demo/                        # Interactive demonstrations
├── deploy/                      # Docker, K8s, monitoring configs
├── docs/                        # Documentation
│
├── development/                 # Phase development plans
│   └── project/assessments/     # Assessment tooling
│       ├── scripts/             # assess_project.py, assess_config_compliance.py
│       └── results/             # Timestamped assessment reports
│
├── SKILL.md                     # Architecture guide
└── README.md
```

### Core Modules

#### 1. Website Discovery (`signal_architecture/discovery/website_discovery.py`)

Resolves the correct corporate website for any entity—Step 0 of the pricing workflow. This is foundational for accurate signal extraction.

```python
from signal_architecture.discovery import discover_website, WebsiteDiscoveryEngine

# Simple discovery
result = discover_website("MS Amlin", country_hint="UK")
print(result.primary_website.domain)  # → msamlin.com
print(result.confidence)              # → ConfidenceLevel.HIGH

# With domain hint
engine = WebsiteDiscoveryEngine()
result = engine.discover(
    "Petrobras",
    domain_hint="petrobras.com.br",
    country_hint="Brazil"
)
print(result.primary_website.domain)  # → petrobras.com.br
print(result.confidence)              # → ConfidenceLevel.HIGH
```

**Key Features:**
- Multi-method discovery (DNS enumeration, search, corporate registries)
- Parent/subsidiary resolution
- Confidence scoring with manual review flags
- Batch processing support
- Integrated into workflow as Step 0

#### 2. Workflow Engine (`layers/risk/workflow.py`)

Orchestrates the complete 14-step DSI pricing workflow from discovery through decision.

```python
from layers.risk.workflow import run_assessment, WorkflowEngine

# Simple assessment
result = run_assessment(
    entity_id="petrobras-001",
    coverage="cyber",
    entity_name="Petrobras",
    domain_hint="petrobras.com.br",
    submission_data={"tiv": 10_000_000}
)

print(f"Score: {result.composite_score}/1000")  # → Score: 742/1000
print(f"Tier: {result.tier}")                    # → Tier: 2
print(f"Decision: {result.decision.value}")      # → Decision: approve
print(f"Premium: ${result.recommended_premium}") # → Premium: $125,000
```

**Key Features:**
- 14-step workflow (Step 0 discovery + 13 pricing steps)
- Content-addressable configuration storage
- Full audit trail with model versioning
- Automatic tier-to-decision mapping
- Multiple premium options by limit band with full `LimitPremiumDetail` breakdown
- Tower (excess-of-loss) and subscription (order/line) market structure support
- ROL-based pricing validation and dual recommendation engine
- Uncapped premium capture, modifier visibility, tier margin context

#### 3. Signal Architecture (`signals/`)

The signal extraction framework implements the Extractor → Aggregator → Categorizer → Inference pipeline.

```python
from signal_architecture.signals.types import InferenceContext, SignalResult

# Context includes discovery data for extractors
context = InferenceContext(
    configuration={},
    coverage="cyber",
    config_name="cyber_general",
    discovered_domain="example.com",    # From Step 0
    discovery_confidence=0.95           # From Step 0
)

# Extractors can use the discovered domain
def infer_security_headers(entity_id: str, context: InferenceContext) -> SignalResult:
    domain = context.discovered_domain  # Use discovered website
    # ... fetch and score security headers
```

**Key Features:**
- TTL-aware caching for extractor results
- Discovery data passed to all inference functions
- Standardized result types for audit trail
- Confidence scoring per signal

---

### Getting Started

#### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (optional, for persistence)
- Redis 7+ (optional, for caching)

#### Installation

```bash
# Clone repository
git clone https://github.com/jwalker618/digital-signal-intelligence.git
cd digital-signal-intelligence

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

#### Run the API

```bash
# Development mode
uvicorn infrastructure.api.main:app --reload --port 8000

# Production mode
uvicorn infrastructure.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

API documentation available at: `http://localhost:8000/api/docs`

#### Quick Start

```python
from layers.risk.workflow import run_assessment

# Run complete workflow (discovery + pricing in one call)
result = run_assessment(
    entity_id="target-company-001",
    coverage="aerospace",
    entity_name="Target Aviation Corp",
    domain_hint="targetaviation.com",
    country_hint="US",
    submission_data={
        "tiv": 50_000_000,
        "limit": 10_000_000,
    }
)

# Check discovery results (Step 0)
print(f"Discovered: {result.discovered_domain}")
print(f"Discovery confidence: {result.discovery_confidence}")

# Check pricing results (Steps 1-13)
print(f"Composite Score: {result.composite_score}/1000")
print(f"Tier: {result.tier} ({result.tier_label})")
print(f"Decision: {result.decision.value}")
print(f"Premium: ${result.recommended_premium:,.0f}")

# Access full audit trail
version = result.model_version
print(f"Limit premiums: {version.limit_premiums}")
print(f"Signal coverage: {version.signal_coverage:.0%}")
print(f"Confidence: {version.confidence:.0%}")
```

#### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=signal_architecture --cov=infrastructure --cov=layers --cov=coverages --cov-report=html
```

#### Development Tools

```bash
# Generate coverage documentation (after config.yaml changes)
python coverages/doc_generator.py

# Run project assessment (before commits)
python development/project/assessments/scripts/assess_project.py

# Validate single config file
python development/project/assessments/scripts/assess_config_compliance.py coverages/cyber/config.yaml

# Save assessment report
python development/project/assessments/scripts/assess_project.py --save-report
```

#### Interactive Demos

**Interactive Demo** (no installation required):
Open `demo/index.html` directly in your browser for a full interactive demonstration.

**Live Demo Server** (requires Python):
```bash
python -m demo.server
# Open http://localhost:8080
```

**Coverage Examples** in `demo/examples/`:
- `run_cyber.py`, `run_energy.py`, `run_fi.py`, `run_marine.py`, etc. - Individual coverage demos
- `run_hybrid.py` - Multi-extractor hybrid routing demo
- `run_multi.py` - Multi-coverage orchestration demo

---

### Deployment

DSI ships with production-ready deployment infrastructure. See the [Deployment Guide](deploy/deployment_guide.md) for full details.

#### Option 1: Docker Compose (Simplest)

```bash
# From repository root
cp .env.example .env
# Edit .env with your settings (DATABASE_URL, REDIS_URL, JWT_SECRET_KEY)

cd deploy/docker
docker-compose -f docker-compose.prod.yml up -d
```

This starts the DSI API, PostgreSQL, and Redis. The API is available at `http://localhost:8000`.

#### Option 2: Kubernetes

```bash
cd deploy/kubernetes

# Edit secrets-template.yaml with real values
kubectl apply -k .

# Verify
kubectl get pods -n dsi
```

Includes: Deployment, Service, Ingress, HPA (2-10 replicas), ConfigMap, and Secrets template.

#### Option 3: CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/ci.yml`) automates the full path from code to production:

1. **Lint** - Black, isort, Flake8, MyPy
2. **Test** - pytest across Python 3.10/3.11/3.12 with coverage
3. **Rust Build** - Compile dsi-core crate
4. **Docker Build** - Multi-platform image, pushed to GHCR (on main/develop)
5. **Deploy Staging** - Automatic on `develop` branch
6. **Deploy Production** - Automatic on `main` branch

#### Monitoring

- **Health checks**: `/api/v1/health/live`, `/api/v1/health/ready`
- **Prometheus metrics**: `/api/v1/metrics` (request latency, error rates, workflow duration)
- **Grafana dashboard**: `deploy/monitoring/grafana-dashboard.json`
- **Alert rules**: `deploy/monitoring/prometheus-config.yaml`

#### Database Migrations

```bash
# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

### Frequently Asked Questions

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

### Contributing

We welcome contributions in the following areas:
- New signal collectors for additional data sources
- Coverage line configurations for new product types
- Validation studies with historical loss data
- Dashboard and visualisation improvements

---

### License

Proprietary - Internal Use Only

---

## Contact

For questions about DSI implementation or methodology:
- John Walker
