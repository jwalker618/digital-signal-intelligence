# Phase 6: Discovery Integration

## Purpose
Integrate the website discovery engine (Step 0) into the full model workflow, enabling automated identification of the primary corporate website.

## Key Deliverables
- Discovery engine
- Enhanced inference context
- Workflow integration (Step 0)
- Identity + confidence scoring

## Implementation Summary
This phase adds a discovery step before signal extraction. It identifies candidate websites, validates them, and selects the primary corporate domain. The discovered URL becomes the anchor for all downstream extractors.

## Detailed Plan

This phase integrates website discovery as a pre-processing step before signal extraction.

### 6.1 The Discovery Problem

When a submission arrives, it typically contains:
- Company name (e.g., "MS Amlin", "Petrobras", "Lufthansa")
- Optional domain hint (e.g., "msamlin.com")
- Optional country/region hint

**Challenge**: The same company name can have multiple web presences:
- Corporate parent vs subsidiary
- Regional variations (petrobras.com vs petrobras.com.br)
- Marketing sites vs investor relations

**Solution**: Discovery module identifies the correct corporate website before signal extraction begins.

### 6.2 Discovery Module (`discovery/`)

Located in `technical_pricing/discovery/`:

```python
from technical_pricing.discovery import (
    WebsiteDiscoveryEngine,
    discover_website,
    DiscoveryResult,
    WebsiteCandidate,
)

# Simple discovery
result = discover_website("MS Amlin")
print(result.primary_website.domain)  # "msamlin.com"
print(result.confidence)              # 0.95

# Discovery with hints
result = discover_website(
    "Petrobras",
    domain_hint="petrobras.com.br",
    country_hint="Brazil"
)
```

**Key Classes:**

```python
@dataclass
class WebsiteCandidate:
    """A potential website match"""
    domain: str
    url: str
    confidence: float
    discovery_method: DiscoveryMethod
    website_type: WebsiteType
    evidence: List[str]

@dataclass
class DiscoveryResult:
    """Complete discovery output"""
    query: str
    primary_website: WebsiteCandidate
    alternate_websites: List[WebsiteCandidate]
    corporate_identity: CompanyIdentity
    relationships: List[CorporateRelationship]
    confidence: float
    discovery_time_ms: float
```

### 6.3 Extended Workflow (Step 0)

The complete workflow is 14 steps (Step 0 discovery + Steps 1-13 pricing):

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTENDED WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STEP 0: DISCOVERY (NEW)                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Company Name + Hints → Website Discovery → Domain        │   │
│  │                                                          │   │
│  │ Outputs:                                                 │   │
│  │ - Primary website URL/domain                             │   │
│  │ - Corporate identity (parent, subsidiaries)              │   │
│  │ - Confidence score                                       │   │
│  │ - Alternate websites for manual review                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  STEPS 1-13: EXISTING WORKFLOW                                  │
│  (Now with discovered website context for extractors)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.4 Integration Points

**WorkflowEngine Changes:**

```python
class WorkflowEngine:
    def __init__(
        self,
        config_manager: ConfigManager,
        data_manager: ModelDataManager,
        scorer: ModelScorer,
        query_evaluator: QueryEvaluator,
        pricer: ModelPricer,
        discovery_engine: WebsiteDiscoveryEngine = None  # NEW
    ):
        self.discovery_engine = discovery_engine or WebsiteDiscoveryEngine()

    def run_workflow(
        self,
        entity_name: str,              # Company name for discovery
        coverage: str,
        submission_data: dict,
        domain_hint: str = None,       # Optional domain hint
        country_hint: str = None,      # Optional country hint
        skip_discovery: bool = False,  # Skip if domain already known
        **kwargs
    ) -> WorkflowResult:
        # Step 0: Discovery
        if not skip_discovery:
            discovery = self.discovery_engine.discover(
                entity_name,
                domain_hint=domain_hint,
                country_hint=country_hint
            )
            entity_id = discovery.primary_website.domain
            submission_data["discovered_website"] = discovery.primary_website.url
            submission_data["discovery_confidence"] = discovery.confidence
        else:
            entity_id = domain_hint or entity_name

        # Steps 1-13: Existing workflow
        # ...
```

**InferenceContext Enhancement:**

```python
@dataclass
class InferenceContext:
    # Existing fields
    configuration: dict
    coverage: str
    config_name: str

    # NEW: Discovery context for extractors
    discovered_website: str = None
    discovered_domain: str = None
    corporate_identity: dict = None
    discovery_confidence: float = 1.0
```

### 6.5 Extractor Usage of Discovery

Extractors can use the discovered website to fetch data:

```python
class SecurityHeadersExtractor(StubExtractor):
    def extract(self, entity_id: str, context: InferenceContext) -> ExtractorResult:
        # Use discovered website if available
        url = context.discovered_website or f"https://{entity_id}"

        # In production: fetch and analyze headers
        # In stub mode: return realistic mock data
        return self._generate_stub_data(entity_id, url)
```

### 6.6 File Structure for Phase 6

```
technical_pricing/
├── discovery/
│   ├── __init__.py              ✅ Package exports
│   └── website_discovery.py     ✅ Core discovery engine
├── model/
│   ├── types.py                 ✅ DiscoveryResult integrated
│   └── workflow.py              ✅ Step 0 discovery integrated
└── signals/
    └── types.py                 ✅ InferenceContext enhanced
```

### 6.7 Implementation Tasks

| Task | File | Status |
|-|-|-|
| Add discovery types to model | `model/types.py` | ✅ Complete |
| Enhance InferenceContext | `signals/types.py` | ✅ Complete |
| Integrate discovery into workflow | `model/workflow.py` | ✅ Complete |
| Add discovery tests | `tests/unit/test_discovery.py` | ✅ Complete |
| Update integration tests | `tests/integration/` | ✅ Complete |

