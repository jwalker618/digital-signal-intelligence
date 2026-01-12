# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.1.0|
|Date|January 2025|
|Classification|technical pricing|

---

# Technical Pricing Module

The core DSI package containing all signal extraction, scoring, pricing, and workflow logic.

## Directory Structure

```
technical_pricing/
├── signals/           # Signal extraction framework
│   ├── extractors/    # Data extraction (stubs and production)
│   │   ├── stubs/     # Stub extractors for testing
│   │   └── production/ # 50 production extractors
│   ├── aggregators/   # Signal aggregation
│   ├── categorisers/  # Score categorization
│   ├── inference/     # Inference functions
│   │   └── functions/routed/  # Multi-source routed functions
│   └── routing/       # Jurisdiction-aware routing
├── coverages/         # Coverage configurations (YAML)
│   ├── aerospace/     # 21 signals
│   ├── cyber/         # 35 signals
│   ├── do/            # 46 signals (Directors & Officers)
│   ├── energy/        # 44 signals
│   ├── fi/            # ~40 signals (Financial Institutions)
│   ├── marine/        # ~38 signals
│   └── pi/            # ~35 signals (Professional Indemnity)
├── model/             # 14-step workflow implementation
│   ├── workflow.py    # Complete orchestration
│   ├── scorer.py      # Signal scoring
│   ├── pricer.py      # Premium calculation
│   ├── config_manager.py  # Config loading
│   └── modifiers/     # Traditional pricing modifiers
├── discovery/         # Entity identification (Step 0)
├── api/               # FastAPI REST API
│   ├── main.py        # Application entry
│   ├── routes/        # Endpoint handlers
│   └── auth/          # JWT & API key auth
├── db/                # Database layer
│   ├── models.py      # SQLAlchemy models
│   └── repositories.py  # Data access
├── orchestration/     # Multi-coverage handling
├── analytics/         # Performance analysis
├── integrations/      # Email, docs, webhooks
├── builder/           # LLM coverage builder
└── tests/             # 380+ tests
```

## Key Components

### Signal Architecture

The signal pipeline follows: **Extractor → Aggregator → Categorizer → Inference**

```python
from technical_pricing.model.workflow import run_assessment

result = run_assessment(
    entity_id="company-001",
    coverage="cyber",
    entity_name="Example Corp",
    domain_hint="example.com"
)
```

### Coverage Configuration

Each coverage has a YAML configuration defining signals, weights, tiers, and pricing:

```yaml
# coverages/cyber/config.yaml
signal_groups:
  - name: technical_infrastructure
    weight: 0.30
    signals:
      - security_headers
      - tls_config
      - email_auth
```

### Production Extractors

50 free production extractors organized by category:

| Category | Count | Examples |
|----------|-------|----------|
| DNS | 4 | email_auth, dnssec, whois |
| HTTP | 2 | security_headers, security_txt |
| Network | 4 | cloud_infra, cdn_usage, tls_config |
| Regulatory | 9 | ofac, epa, osha, faa |
| Sanctions | 10 | opensanctions, uk_ofsi, eu_sanctions |
| Corporate | 5 | companies_house, opencorporates, gleif |

### Routing Module

Jurisdiction-aware signal extraction with multi-source aggregation:

```python
from technical_pricing.signals.routing import JurisdictionRouter

router = JurisdictionRouter()
extractors = router.get_extractors(
    signal_type='sanctions',
    locale='UK',
    strategy=RoutingStrategy.LOCALE_PLUS_GLOBAL
)
```

## Running Tests

```bash
# All tests
pytest technical_pricing/tests/ -v

# With coverage
pytest technical_pricing/tests/ --cov=technical_pricing --cov-report=html

# Specific test file
pytest technical_pricing/tests/unit/test_workflow.py -v
```

## Development

See `SKILL.md` for complete architecture documentation and development workflow.
