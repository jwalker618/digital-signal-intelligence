# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## Data Persistence Architecture

| Item | Value |
|-|-|
|Version|1.0|
|Date|November 2025|
|Classification|Technical Specification|

---

### Overview

The DSI persistence layer provides a comprehensive solution for managing:

1. **Signal Cache** - Store and reuse extracted signals within configurable TTLs
2. **Model Registry** - Version control for pricing models with lifecycle management
3. **Quote Repository** - Complete audit trail of all pricing decisions

This architecture enables the "minimum viable interaction" by ensuring that signals are never unnecessarily re-fetched and quotes are always traceable back to the exact model version and signals used.

---

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DSI Workflow                                 │
├─────────────────────────────────────────────────────────────────────┤
│  WorkflowRequest ──► SignalExtractor ──► PricingEngine ──► Quote    │
│         │                   │                  │              │     │
│         ▼                   ▼                  ▼              ▼     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │               DSIPersistenceService                            │ │
│  ├────────────────┬──────────────────┬────────────────────────────┤ │
│  │  SignalCache   │  ModelRegistry   │    QuoteRepository         │ │
│  │  ┌──────────┐  │  ┌───────────┐   │    ┌───────────────┐       │ │
│  │  │  Store   │  │  │  Version  │   │    │   Save Quote  │       │ │
│  │  │  Lookup  │  │  │  Active   │   │    │   Get History │       │ │
│  │  │  TTL     │  │  │  Activate │   │    │   Analytics   │       │ │
│  │  └──────────┘  │  └───────────┘   │    └───────────────┘       │ │
│  └────────────────┴──────────────────┴────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     StorageBackend                             │ │
│  ├────────────────┬──────────────────┬────────────────────────────┤ │
│  │  InMemory      │     Redis        │      PostgreSQL            │ │
│  │  (Dev/Test)    │  (Signal Cache)  │   (Quotes/Models)          │ │
│  └────────────────┴──────────────────┴────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Signal Caching Strategy

#### TTL by Signal Category

| Category | TTL | Examples | Rationale |
|----------|-----|----------|-----------|
| **STATIC** | 90 days | Company registration, founding date, SIC code | Never/rarely changes |
| **SEMI_STATIC** | 7 days | Financial strength, certifications, employee count | Changes quarterly |
| **DYNAMIC** | 4 hours | Security ratings, vulnerability counts, news | Changes frequently |
| **REAL_TIME** | 0 (no cache) | Stock price, active incidents | Always fetch fresh |

#### Cache Key Schema

```
signal:{entity_id}:{signal_type}
bundle:{bundle_id}
entity_signals:{entity_id}  (index of all signals for entity)
```

#### Cache Workflow

```python
# 1. Check cache first
cached = cache.get_signals(entity_id, required_signals)

# 2. Identify what needs extraction
to_extract = [s for s in required_signals if cached[s] is None]

# 3. Extract only missing signals
if to_extract:
    new_signals = extractor.fetch(entity_id, to_extract)
    for signal in new_signals:
        cache.store_signal(signal)  # Stored with category-appropriate TTL

# 4. Return all signals (cached + fresh)
return {**cached, **new_signals}
```

#### Example: Requote Efficiency

When a requote is requested (e.g., different limit):

| Scenario | First Quote | Requote |
|----------|-------------|---------|
| Signal Extraction | 8 API calls | 0 API calls |
| Processing Time | ~3000ms | ~50ms |
| Cache Hit Rate | 0% | 100% |

---

### Model Versioning

#### Model Lifecycle

```
DRAFT ──► TESTING ──► ACTIVE ──► DEPRECATED ──► RETIRED
  │          │           │           │
  │          │           │           └── No longer available
  │          │           └── Production use
  │          └── Under validation
  └── In development
```

#### Version Control Features

1. **Semantic Versioning**: Major.Minor.Patch (e.g., 2.1.0)
2. **Immutable Versions**: Once registered, cannot be modified
3. **Active Pointer**: Only one active version per coverage type
4. **Parent Lineage**: Track which version spawned variants
5. **Configuration Storage**: Complete model config preserved
6. **Checksum**: Integrity verification

#### Model Registry API

```python
# Register new model
registry.register_model(ModelVersion(...))

# Activate for production
registry.activate_model("cyber", "2.1.0")

# Get active model (auto-selects current production version)
model = registry.get_active_model("cyber")

# Create variant with modified parameters
variant = registry.create_variant(
    base_model, 
    new_version="2.1.1",
    config_overrides={"base_rate": 2800},
    description="Rate adjustment for Q4"
)
```

---

### Quote Persistence

#### Quote Record Structure

Every quote captures:

```python
Quote(
    # Identity
    quote_id: str,
    entity_id: str,
    entity_name: str,
    
    # Model Reference (exact version used)
    model_id: str,
    model_version: str,
    
    # Request Parameters
    coverage_type: str,
    requested_limit: float,
    requested_currency: str,
    effective_date: datetime,
    deductible: float,
    
    # Assessment Results
    composite_score: float,
    tier: int,
    tier_label: str,
    confidence: float,
    signal_coverage: float,
    
    # Pricing
    gross_premium: float,
    rate_per_million: float,
    tier_modifier: float,
    
    # Decision
    decision_path: str,  # straight_through, referred, declined
    decision_reasons: List[str],
    green_flags: List[Dict],
    red_flags: List[Dict],
    
    # References
    signal_bundle_id: str,  # Link to signals used
    parent_quote_id: str,   # For requotes
    
    # Lifecycle
    status: QuoteStatus,
    created_at: datetime,
    expires_at: datetime,
)
```

#### Quote Lineage

Track quote modifications:

```
Original Quote (Q1)
     │
     ├──► Requote with higher limit (Q2) ──► parent_quote_id = Q1
     │
     └──► Requote with different deductible (Q3) ──► parent_quote_id = Q1
              │
              └──► Further modification (Q4) ──► parent_quote_id = Q3
```

#### Audit Trail

Every status change is logged:

```python
QuoteAudit(
    quote_id: str,
    action: str,        # created, referred, approved, bound, declined
    old_status: str,
    new_status: str,
    changed_by: str,    # underwriter_id or "system"
    change_reason: str,
    metadata: Dict,
    timestamp: datetime,
)
```

---

### Storage Backend Options

#### In-Memory (Development/Testing)

```python
storage = InMemoryStorage()
service = DSIPersistenceService(storage)
```

Best for: Unit tests, local development, demos

#### Redis (Signal Cache)

```python
from redis_storage import create_redis_storage

storage = create_redis_storage({
    "host": "redis.example.com",
    "port": 6379,
    "password": "secret",
    "prefix": "dsi:",
    "with_metrics": True,
})
```

Features:
- Sub-millisecond lookups
- Native TTL support
- Connection pooling
- Cluster mode for horizontal scaling
- Built-in metrics collection

#### PostgreSQL (Quotes & Models)

```python
from postgres_storage import create_postgres_storage

storage = create_postgres_storage({
    "host": "db.example.com",
    "port": 5432,
    "database": "dsi",
    "user": "dsi_app",
    "password": "secret",
})
```

Features:
- ACID compliance for quotes
- Complex queries and analytics
- JSONB for flexible signal storage
- Audit logging
- Partitioning for time-series data

#### Hybrid Architecture (Recommended for Production)

```
┌─────────────────────────────────────────────────────────────┐
│                     DSI Persistence                         │
├──────────────────────┬──────────────────────────────────────┤
│      Redis           │           PostgreSQL                 │
│  ┌────────────────┐  │    ┌──────────────────────────┐      │
│  │ Signal Cache   │  │    │ dsi_quotes               │      │
│  │ (4hr-90d TTL)  │  │    │ dsi_models               │      │
│  └────────────────┘  │    │ dsi_quote_audit          │      │
│                      │    │ dsi_signal_bundles       │      │
│  Fast, ephemeral     │    │                          │      │
│  High read volume    │    │ Durable, queryable       │      │
│                      │    │ Analytics & compliance   │      │
└──────────────────────┴──────────────────────────────────────┘
```

---

### Integration Example

#### Complete Workflow

```python
from dsi_workflow import DSIWorkflow, WorkflowRequest, create_workflow, initialize_models

# 1. Initialize (production)
workflow = create_workflow(
    storage_type="redis",
    storage_config={
        "host": "redis.prod.internal",
        "port": 6379,
        "password": os.environ["REDIS_PASSWORD"],
    }
)

# 2. Initialise models (once at startup)
initialize_models(workflow)

# 3. Process quote request
request = WorkflowRequest(
    entity_id="acme-corp-001",
    entity_name="Acme Corporation",
    coverage_type="cyber",
    limit=5_000_000,
    currency="USD",
    deductible=50_000,
    direct_inquiry={
        "pending_claims": False,
        "pending_regulatory": False,
        "coverage_declined": False,
    }
)

response = workflow.process(request)

# 4. Results
print(f"Quote: {response.quote.quote_id}")
print(f"Score: {response.quote.composite_score}")
print(f"Premium: ${response.quote.gross_premium:,.2f}")
print(f"Path: {response.decision_path}")
print(f"Cache Hit Rate: {response.cache_stats['hit_rate']:.0%}")
print(f"Processing: {response.processing_time_ms:.0f}ms")

# 5. Requote with different limit (signals reused from cache)
requote_response = workflow.requote(
    response.quote.quote_id,
    limit=10_000_000
)

print(f"Requote Premium: ${requote_response.quote.gross_premium:,.2f}")
print(f"Cache Hit Rate: {requote_response.cache_stats['hit_rate']:.0%}")  # 100%

# 6. Bind the quote
bound_quote = workflow.bind_quote(
    requote_response.quote.quote_id,
    underwriter_id="UW-12345"
)
```

---

### Performance Characteristics

#### Signal Cache Performance

| Operation | In-Memory | Redis | PostgreSQL |
|-----------|-----------|-------|------------|
| Single lookup | <1ms | 1-2ms | 5-10ms |
| Bulk lookup (10 signals) | <1ms | 2-5ms | 10-20ms |
| Store signal | <1ms | 1-2ms | 5-10ms |

#### Quote Processing Time

| Scenario | Time |
|----------|------|
| First quote (all signals extracted) | 2-5 seconds |
| Requote (all signals cached) | 50-100ms |
| Cached + partial refresh | 500ms-1s |

#### Recommended Monitoring

```python
# Built-in metrics (RedisStorageWithMetrics)
metrics = storage.get_metrics()
print(f"Cache hit rate: {metrics['hit_rate']:.1%}")
print(f"Total gets: {metrics['gets']}")
print(f"Total sets: {metrics['sets']}")
```

---

### Files Reference

| File | Purpose |
|------|---------|
| `dsi_persistence.py` | Core persistence layer with all data classes |
| `dsi_workflow.py` | Integrated workflow orchestration |
| `redis_storage.py` | Redis storage backend |
| `postgres_storage.py` | PostgreSQL storage backend |

---

### Summary

The DSI persistence layer enables:

1. **Efficient Signal Reuse**: 100% cache hit rate on requotes
2. **Model Versioning**: Complete traceability of which model priced each quote
3. **Quote Lineage**: Track all modifications and audit trail
4. **Flexible Storage**: Swap backends without code changes
5. **Production Ready**: Connection pooling, metrics, error handling
