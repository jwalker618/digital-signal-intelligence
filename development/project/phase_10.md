# Phase 10: Multi‑Coverage Orchestration

## Status
✅ Complete

## Purpose
Enable the DSI engine to run multiple coverages in parallel, orchestrate jurisdiction‑aware routing, and unify results across lines of business.

## Key Deliverables
- Multi‑coverage orchestration engine
- Locale detection
- Configuration‑driven routing
- Unified scoring and pricing outputs

## Detailed Plan

This phase enables automatic pricing across multiple coverages and locales from a single submission.

### 10.1 The Multi-Coverage Problem

When a submission arrives, we may want to:
- **Price Multiple Lines**: FI, PI, D&O, Cyber for the same client
- **Test Multiple Locales**: FI in US, UK, Europe to find the best fit
- **Unknown Locale Resolution**: Client name only, no country hint
- **Cost Optimization**: Only run expensive signals when needed

### 10.2 Multi-Coverage Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  MULTI-COVERAGE ORCHESTRATOR                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    SUBMISSION INPUT                      │   │
│  │                                                          │   │
│  │  Entity: "Global Bank Ltd"                               │   │
│  │  Mode: "multi_coverage" | "multi_locale" | "auto_detect" │   │
│  │  Coverages: ["fi", "do", "cyber"] (or auto)              │   │
│  │  Locales: ["US", "UK", "EU"] (or auto-detect)            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   ROUTING ENGINE                         │   │
│  │                                                          │   │
│  │  1. Determine applicable coverages (from hints or rules) │   │
│  │  2. Determine applicable locales (from discovery)        │   │
│  │  3. Generate execution plan                              │   │
│  │  4. Estimate cost (signal calls)                         │   │
│  │  5. Get approval if cost exceeds threshold               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   PARALLEL EXECUTOR                      │   │
│  │                                                          │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │   │
│  │  │FI - US  │  │FI - UK  │  │D&O - US │  │Cyber    │      │   │
│  │  │Workflow │  │Workflow │  │Workflow │  │Workflow │      │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │   │
│  │                                                          │   │
│  │  Shared signal cache across parallel runs                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   RESULTS AGGREGATOR                     │   │
│  │                                                          │   │
│  │  • Best locale match per coverage                        │   │
│  │  • Consolidated quote package                            │   │
│  │  • Cross-coverage discounts                              │   │
│  │  • Package recommendations                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 Data Structures

```python
@dataclass
class MultiCoverageRequest:
    """Request for multi-coverage pricing"""
    entity_name: str
    domain_hint: Optional[str] = None

    # Coverage selection
    coverages: List[str] = None  # None = auto-detect
    coverage_rules: Dict[str, Any] = None  # Rules for auto-selection

    # Locale selection
    locales: List[str] = None  # None = auto-detect from discovery
    locale_detection_mode: str = "discovery"  # discovery, all, explicit

    # Cost control
    max_cost_units: int = None  # Max signal calls
    require_approval_above: int = 50  # Prompt if exceeds

    # Execution options
    parallel: bool = True
    share_cache: bool = True  # Share signal cache across runs
    fail_fast: bool = False  # Stop on first failure

@dataclass
class ExecutionPlan:
    """Plan for multi-coverage execution"""
    runs: List[PlannedRun]
    estimated_cost_units: int
    estimated_duration_seconds: float
    shared_signals: List[str]  # Signals that can be shared
    requires_approval: bool

@dataclass
class PlannedRun:
    coverage: str
    locale: str
    configuration: str
    estimated_signals: int
    estimated_cost: float

@dataclass
class MultiCoverageResult:
    """Combined results from multi-coverage pricing"""
    entity_name: str
    discovered_domain: str
    detected_locale: str

    # Per-coverage results
    coverage_results: Dict[str, WorkflowResult]

    # Best matches
    best_locale_per_coverage: Dict[str, str]
    recommended_package: List[str]

    # Aggregate metrics
    total_cost_units: int
    total_duration_seconds: float
    cache_hit_rate: float

    # Package discount (if applicable)
    package_discount: float
    combined_premium: float
```

### 10.4 Configuration

```yaml
multi_coverage:
  # Auto-detection rules
  coverage_detection:
    default_coverages: ["cyber"]  # Always include
    conditional_coverages:
      - coverage: "fi"
        condition: "sic_code in ['6021', '6022', '6029']"
      - coverage: "do"
        condition: "is_public_company"
      - coverage: "marine"
        condition: "has_vessels"

  # Locale detection
  locale_detection:
    use_discovery: true  # Use website discovery TLD
    fallback_locales: ["US", "UK"]  # Try if no hint

  # Cost control
  cost_limits:
    approval_threshold: 50  # Cost units
    max_parallel_runs: 10
    signal_cache_ttl: 3600  # Share within session

  # Package discounts
  package_discounts:
    - coverages: ["fi", "do"]
      discount: 0.05  # 5% for FI + D&O
    - coverages: ["fi", "do", "cyber"]
      discount: 0.10  # 10% for full package
```

### 10.5 Implementation Tasks

| Task | File | Status |
|-|-|-|
| Create MultiCoverageOrchestrator | `orchestration/multi_coverage.py` | ✅ Complete |
| Create LocaleDetector | `orchestration/locale_detection.py` | ✅ Complete |
| Create ResultAggregator | `orchestration/aggregator.py` | ✅ Complete |
| Implement shared signal cache | `orchestration/multi_coverage.py` | ✅ Complete |
| Add package discount logic | `orchestration/multi_coverage.py` | ✅ Complete |
| Create orchestration types | `orchestration/types.py` | ✅ Complete |
| Add configuration schema | `coverages/*/config.yaml` | ✅ Complete |
| Add unit tests | `tests/unit/test_multi_coverage.py` | ✅ Complete |

