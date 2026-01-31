# DSI Production Readiness Plan

**Version:** 1.0
**Date:** 2026-01-31
**Status:** PROPOSED
**Prerequisite:** R1-R11 Restructure (COMPLETE)

---

## Context

The R1-R11 restructure delivered config architecture v2.0, the graph runtime, Rust scaffolding, and a validated type system. The codebase has sound internal architecture but cannot process a real insurance submission end-to-end. This plan addresses every identified gap between current state and a deployable system.

### What works today
- 7 coverage YAMLs: v2.0 compliant, validated, internally consistent
- Risk scoring pipeline: types, scorer, pricer (v2.0 actions, comparison operators)
- Graph runtime: 6 node types, 6 edge types, PageRank, 5 derivatives
- Validation framework: catches real config errors
- API skeleton: 28 endpoints, auth, health checks, CORS, logging middleware
- 59 production extractors: Companies House, Email Auth, OFAC, plus 56 more
- Docker + K8s manifests: multi-stage build, rolling update, HPA, probes
- CI/CD: GitHub Actions (lint, test, summary)

### What doesn't work today
- Every path reference in CI, Docker, and pyproject.toml points to `technical_pricing/` — a package that doesn't exist
- `infrastructure/__init__.py` unconditionally imports FastAPI, breaking all infrastructure imports without it
- All data lives in Python dicts — gone on restart
- Inference functions hardwired to stub extractors returning random data
- 59 production extractors exist but are never called
- Rate limiting configured but not enforced
- Prometheus alerts defined but no client instrumentation

---

## Phase P1: Fix Broken Fundamentals

**Objective:** Make the existing code importable, testable, and buildable without workarounds.

**Effort:** Small — these are all one-line to ten-line fixes.

### P1.1 Fix infrastructure/__init__.py import chain

| ID | Task | Details |
|----|------|---------|
| P1.1.1 | Make infrastructure imports lazy | Wrap each import in try/except so missing FastAPI doesn't break builder, validation, analytics, db |
| P1.1.2 | Verify all submodules importable | `from infrastructure import validation` must work without FastAPI installed |

**File:** `infrastructure/__init__.py`
**Change:** Replace unconditional imports with lazy try/except pattern

### P1.2 Fix pyproject.toml paths

| ID | Task | Details |
|----|------|---------|
| P1.2.1 | Fix testpaths | `"technical_pricing/tests"` → `"tests"` |
| P1.2.2 | Fix coverage source | `--cov=technical_pricing` → `--cov=signal_architecture --cov=infrastructure --cov=layers` |
| P1.2.3 | Fix coverage.run source | `source = ["technical_pricing"]` → `["signal_architecture", "infrastructure", "layers"]` |

**File:** `pyproject.toml` (lines 111-135)

### P1.3 Fix CI/CD paths

| ID | Task | Details |
|----|------|---------|
| P1.3.1 | Fix lint paths | `black --check technical_pricing/` → `black --check signal_architecture/ infrastructure/ layers/` |
| P1.3.2 | Fix test paths | `pytest technical_pricing/tests/` → `pytest tests/` |
| P1.3.3 | Fix coverage paths | `--cov=technical_pricing/` → `--cov=signal_architecture --cov=infrastructure --cov=layers` |
| P1.3.4 | Fix mypy paths | `mypy technical_pricing/` → `mypy signal_architecture/ infrastructure/ layers/` |

**File:** `.github/workflows/ci.yml` (lines 46, 49, 54, 69, 106-107)

### P1.4 Fix Dockerfile paths

| ID | Task | Details |
|----|------|---------|
| P1.4.1 | Fix COPY source | `COPY technical_pricing/ ./technical_pricing/` → `COPY signal_architecture/ infrastructure/ layers/ coverages/ schemas/ ./` |
| P1.4.2 | Fix CMD entrypoint | `technical_pricing.api.main:app` → `infrastructure.api.main:app` |
| P1.4.3 | Add requirements.txt or pip install from pyproject.toml | Current references `requirements.txt` which may not exist or be stale |

**File:** `Dockerfile` (lines 63, 78)

### P1.5 Fix layers/__init__.py exports

| ID | Task | Details |
|----|------|---------|
| P1.5.1 | Add exposure and loss to exports | `__all__ = ["risk", "exposure", "loss"]` |

**File:** `layers/__init__.py`

### P1.6 Fix tests/conftest

| ID | Task | Details |
|----|------|---------|
| P1.6.1 | Rename conftest_layers.py → conftest.py | Or create a proper conftest.py that imports from conftest_layers |
| P1.6.2 | Verify pytest discovers all 496+ tests from `pytest tests/` | Must work from root with no path arguments |

### P1 Deliverables
- [ ] `pytest tests/` runs all tests from root directory
- [ ] `from infrastructure import validation` works without FastAPI
- [ ] `docker build .` produces working image
- [ ] CI pipeline lints and tests the actual codebase

### P1 Validation
```bash
# All must pass
python -c "from infrastructure import validation; print('OK')"
python -c "from infrastructure import builder; print('OK')"
python -c "from layers import exposure, loss; print('OK')"
pytest tests/ --co -q | tail -1  # Should show 496+ tests collected
```

---

## Phase P2: Database Persistence

**Objective:** Replace in-memory dicts with PostgreSQL persistence so submissions survive restarts.

**Effort:** Medium — SQLAlchemy models and repositories already exist in `infrastructure/db/`. This is wiring, not greenfield.

### P2.1 Database schema

| ID | Task | Details |
|----|------|---------|
| P2.1.1 | Create Alembic migration setup | `alembic init`, configure for async engine |
| P2.1.2 | Create submissions table | id, entity_name, domain_hint, country, coverage_id, status, config_hash, submission_data (JSONB), created_at, updated_at |
| P2.1.3 | Create quotes table | id, submission_id (FK), coverage, tier, premium, signals (JSONB), score, status, created_at |
| P2.1.4 | Create jobs table | id, submission_id (FK), status, progress, result (JSONB), error, created_at, completed_at |
| P2.1.5 | Create referrals table | id, submission_id (FK), reason, underwriter_id, decision, notes, created_at |
| P2.1.6 | Create init-db.sql | For docker-compose postgres initialisation |
| P2.1.7 | Create initial Alembic migration | Generate from models |

### P2.2 Repository layer

| ID | Task | Details |
|----|------|---------|
| P2.2.1 | Create SubmissionRepository | CRUD operations on submissions table |
| P2.2.2 | Create QuoteRepository | CRUD + status transitions (draft → bound → declined) |
| P2.2.3 | Create JobRepository | Status tracking, result storage |
| P2.2.4 | Create ReferralRepository | Assignment, decision recording |
| P2.2.5 | Add connection pooling config | Pool size from DB_POOL_SIZE env, overflow from DB_MAX_OVERFLOW |

### P2.3 Route rewiring

| ID | Task | Details |
|----|------|---------|
| P2.3.1 | Replace `_submissions` dict | Inject SubmissionRepository via FastAPI dependency |
| P2.3.2 | Replace `_quotes` dict | Inject QuoteRepository |
| P2.3.3 | Replace `_jobs` dict | Inject JobRepository |
| P2.3.4 | Wire referrals routes | Connect to ReferralRepository |
| P2.3.5 | Wire analytics routes | Query from database, not return mock data |
| P2.3.6 | Add pagination | Replace in-memory slicing with SQL LIMIT/OFFSET |

### P2 Deliverables
- [ ] `docker-compose up` starts API + Postgres + Redis
- [ ] POST /submissions persists to database
- [ ] GET /submissions returns from database
- [ ] Data survives `docker-compose restart`
- [ ] Alembic migration runs on startup

### P2 Validation
```bash
docker-compose -f deploy/docker/docker-compose.prod.yml up -d
curl -X POST http://localhost:8000/api/v1/submissions -H 'Content-Type: application/json' -d '{"entity_name":"Test","coverage":"cyber"}'
docker-compose restart api
curl http://localhost:8000/api/v1/submissions  # Must return the submission
```

---

## Phase P3: Production Extractor Wiring

**Objective:** Connect inference functions to real data sources instead of stubs. At minimum, one full coverage line (cyber) must run against production extractors.

**Effort:** Medium — extractors exist, the gap is dispatch and configuration.

### P3.1 Extractor factory

| ID | Task | Details |
|----|------|---------|
| P3.1.1 | Audit `extractors/production/factory.py` | Understand existing factory pattern |
| P3.1.2 | Implement extractor selection by env | `FEATURE_USE_STUBS=false` → production factory; `true` → stub factory |
| P3.1.3 | Update `extractors/__init__.py` | Conditional imports based on feature flag |
| P3.1.4 | Add API key/credential management | Production extractors need API keys (Companies House, etc.) |

### P3.2 Cyber coverage production wiring

| ID | Task | Details |
|----|------|---------|
| P3.2.1 | Map cyber signals to production extractors | Which of the 59 production extractors serve which cyber signal? |
| P3.2.2 | Update cyber inference functions | Replace stub extractor imports with factory-resolved extractors |
| P3.2.3 | Handle missing extractors gracefully | If a production extractor has no API key configured, fall back to stub for that signal |
| P3.2.4 | Integration test: cyber end-to-end | Submit a real domain, get real signals, produce a real price |

### P3.3 Remaining coverages

| ID | Task | Details |
|----|------|---------|
| P3.3.1 | Map signals → extractors for all 6 remaining coverages | Create mapping document |
| P3.3.2 | Wire remaining inference functions | Same pattern as cyber |
| P3.3.3 | Graceful degradation per signal | Partial extraction → partial scoring with confidence penalties |

### P3 Deliverables
- [ ] Cyber coverage produces real scores from real data sources
- [ ] `FEATURE_USE_STUBS=false` activates production extractors
- [ ] Missing API keys fall back to stubs per-signal (not per-coverage)
- [ ] Mapping document: signal_id → extractor → data source

### P3 Validation
```bash
FEATURE_USE_STUBS=false python -c "
from signal_architecture.signals.inference.functions.cyber.signals import *
# Run one signal against a real domain
result = ssl_certificate_quality_basefunction('example.com', {})
print(result.score, result.confidence)
assert result.confidence > 0.5  # Not a stub default
"
```

---

## Phase P4: End-to-End Integration Testing

**Objective:** Prove that a submission flows through the full pipeline: API → signal extraction → scoring → graph → pricing → response.

**Effort:** Medium — requires P1-P3 to be complete.

### P4.1 Integration test harness

| ID | Task | Details |
|----|------|---------|
| P4.1.1 | Create test fixtures with real-ish data | A curated submission for each coverage with known expected outputs |
| P4.1.2 | Create end-to-end test: stub mode | POST submission → wait → GET quote, verify structure and ranges |
| P4.1.3 | Create end-to-end test: with graph | Verify graph builder runs during assessment, derivatives computed |
| P4.1.4 | Create end-to-end test: multi-coverage | Submit 3 coverages, verify package discount applied |
| P4.1.5 | Create end-to-end test: referral flow | Submit data that triggers REFER action, verify referral created |

### P4.2 Score regression suite

| ID | Task | Details |
|----|------|---------|
| P4.2.1 | Create golden file per coverage | Known input → known output for each coverage config |
| P4.2.2 | Test score stability | Same input must produce same output (deterministic with stubs) |
| P4.2.3 | Test tier boundaries | Inputs at tier boundaries produce correct tier assignments |
| P4.2.4 | Test score_condition actions | FLAG captured, MODIFIER applied multiplicatively, REFER triggers referral |

### P4.3 API contract tests

| ID | Task | Details |
|----|------|---------|
| P4.3.1 | Test all 28 endpoints return correct status codes | 200, 201, 404, 422 as appropriate |
| P4.3.2 | Test response schemas | Pydantic models match actual responses |
| P4.3.3 | Test auth enforcement | Requests without API key → 401 |
| P4.3.4 | Test error responses | Malformed input → structured error response |

### P4 Deliverables
- [ ] End-to-end test passes for all 7 coverages
- [ ] Golden file regression for each coverage
- [ ] API contract tests for all endpoints
- [ ] Tests runnable in CI without external dependencies (stub mode)

---

## Phase P5: Observability

**Objective:** Production operators can see what the system is doing, diagnose failures, and set alerts.

### P5.1 Structured logging

| ID | Task | Details |
|----|------|---------|
| P5.1.1 | Add JSON log formatter | Structured logs for log aggregation (ELK/CloudWatch/Datadog) |
| P5.1.2 | Create logging configuration | `logging.conf` or programmatic setup from env (LOG_LEVEL, LOG_FORMAT) |
| P5.1.3 | Add correlation IDs | Thread request_id through signal extraction, scoring, graph building |
| P5.1.4 | Add signal extraction logging | Log which signals extracted, from which source, with what latency |

### P5.2 Prometheus metrics

| ID | Task | Details |
|----|------|---------|
| P5.2.1 | Add prometheus_client dependency | To pyproject.toml and requirements |
| P5.2.2 | Create /metrics endpoint | Prometheus scrape target |
| P5.2.3 | Instrument request latency | Histogram: `dsi_request_duration_seconds` by endpoint |
| P5.2.4 | Instrument signal extraction | Histogram: `dsi_signal_extraction_seconds` by signal_id |
| P5.2.5 | Instrument scoring pipeline | Histogram: `dsi_scoring_duration_seconds` by coverage |
| P5.2.6 | Add business metrics | Counter: submissions, quotes, referrals, binds, declines |
| P5.2.7 | Add error counters | Counter: `dsi_errors_total` by error_type |
| P5.2.8 | Wire Prometheus scrape config | Update deploy/monitoring/prometheus-config.yaml annotations |

### P5.3 Rate limiting enforcement

| ID | Task | Details |
|----|------|---------|
| P5.3.1 | Implement rate limiting middleware | Sliding window or token bucket per API key |
| P5.3.2 | Use Redis for rate limit state | Distributed rate limiting across multiple API instances |
| P5.3.3 | Return X-RateLimit headers | X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset |
| P5.3.4 | Return 429 on limit exceeded | With Retry-After header |

### P5 Deliverables
- [ ] JSON-formatted logs with correlation IDs
- [ ] `/metrics` endpoint returns Prometheus format
- [ ] Rate limiting enforced per API key via Redis
- [ ] Grafana dashboard importable from JSON (optional)

---

## Phase P6: Deployment Pipeline

**Objective:** Code merged to main automatically builds, tests, and deploys.

### P6.1 CI fixes and hardening

| ID | Task | Details |
|----|------|---------|
| P6.1.1 | Fix all path references (from P1.3) | Already done in P1 |
| P6.1.2 | Add Rust build step | `cargo build --release --lib` in CI |
| P6.1.3 | Add requirements.txt generation | `pip-compile` from pyproject.toml or maintain manually |
| P6.1.4 | Add integration test step | Run P4 tests after unit tests |
| P6.1.5 | Add test coverage threshold | Fail CI if coverage < 80% on new code |

### P6.2 Docker image build

| ID | Task | Details |
|----|------|---------|
| P6.2.1 | Fix Dockerfile (from P1.4) | Already done in P1 |
| P6.2.2 | Add Docker build step to CI | Build image on main/develop push |
| P6.2.3 | Add Docker image push | Push to container registry (GitHub Container Registry / ECR / etc.) |
| P6.2.4 | Tag images | `latest` + git SHA + semver |

### P6.3 Deployment automation

| ID | Task | Details |
|----|------|---------|
| P6.3.1 | Add staging deployment step | Auto-deploy to staging on develop push |
| P6.3.2 | Add production deployment step | Manual approval gate, then deploy to prod on main |
| P6.3.3 | Add smoke test post-deploy | Hit /health and /submissions endpoints after deploy |
| P6.3.4 | Add rollback mechanism | Document kubectl rollout undo or equivalent |
| P6.3.5 | Create K8s secrets template | DATABASE_URL, REDIS_URL, API_KEY_SALT, JWT_SECRET |

### P6 Deliverables
- [ ] Push to develop → build → test → deploy to staging (automated)
- [ ] Push to main → build → test → approval → deploy to prod
- [ ] Smoke tests run post-deploy
- [ ] Container images tagged and pushed to registry

---

## Phase P7: Performance Validation

**Objective:** Verify the system handles production load and the Rust components deliver claimed speedups.

### P7.1 Python baseline

| ID | Task | Details |
|----|------|---------|
| P7.1.1 | Benchmark signal extraction per coverage | Time all signals for one entity |
| P7.1.2 | Benchmark scoring pipeline per coverage | Time score calculation |
| P7.1.3 | Benchmark graph construction | Time full graph build for various entity sizes |
| P7.1.4 | Benchmark API response time | End-to-end submission → quote latency |

### P7.2 Rust integration

| ID | Task | Details |
|----|------|---------|
| P7.2.1 | Run `maturin develop` successfully | Build and install dsi_core Python package |
| P7.2.2 | Create Python adapter layer | Try Rust, fall back to Python if unavailable |
| P7.2.3 | Benchmark Rust PageRank vs Python | Measure actual speedup on 100/1000/5000 node graphs |
| P7.2.4 | Benchmark Rust derivatives vs Python | Measure actual speedup |
| P7.2.5 | Benchmark Rust validation vs Python | Measure actual speedup on all 7 configs |

### P7.3 Load testing

| ID | Task | Details |
|----|------|---------|
| P7.3.1 | Create load test script | Locust or k6 against staging |
| P7.3.2 | Sustained load test | 10 concurrent users, 100 submissions, measure p50/p95/p99 |
| P7.3.3 | Spike test | 50 concurrent submissions, verify no crashes |
| P7.3.4 | Document capacity limits | Max submissions/minute before degradation |

### P7 Deliverables
- [ ] Performance baseline document (Python latencies per component)
- [ ] Rust speedup measurements (actual, not theoretical)
- [ ] Load test results with capacity numbers
- [ ] Bottleneck identification and remediation plan

---

## Execution Order and Dependencies

```
P1 (Fix Fundamentals)  ──────────────────────────────────────► Can start immediately
  │
  ├── P2 (Database)     ──────────────────────────────────────► Requires P1
  │     │
  ├── P3 (Extractors)   ──────────────────────────────────────► Requires P1
  │     │
  │     ├── P4 (Integration Tests)  ───────────────────────────► Requires P2 + P3
  │     │
  │     ├── P5 (Observability)      ───────────────────────────► Requires P2
  │     │     │
  │     │     └── P6 (Deployment Pipeline) ────────────────────► Requires P1 + P4
  │     │           │
  │     │           └── P7 (Performance)   ────────────────────► Requires P6
```

P2 and P3 can run in parallel after P1.
P5 can start as soon as P2 is done (needs database for rate limiting).
P4 needs both P2 and P3 to write meaningful integration tests.
P6 needs P1 (paths) and P4 (tests to run).
P7 is last — needs a deployed system to test against.

---

## Out of Scope (Deferred)

These are real concerns but not blockers for initial production deployment:

| Item | Reason to defer |
|------|-----------------|
| WASM compilation of validation | Rust crate compiles to cdylib, WASM is a separate target — nice to have |
| Cohort comparison (drift derivative) | Requires historical data from production; can't meaningfully test without it |
| Multi-tenancy | Single-tenant is fine for initial deployment |
| Real-time streaming signals | Batch/request-time extraction is the current architecture |
| Browser-based config editor | The YAML validation works; a UI can come later |

---

## Success Criteria

The system is production-ready when:

1. `docker-compose up` starts API + Postgres + Redis with zero manual steps
2. POST a submission for any of the 7 coverages → receive a priced quote
3. Data persists across restarts
4. At least cyber coverage runs against real data sources
5. CI pipeline passes (lint + test + build) on every push
6. Operators can view request logs, error rates, and latency via Prometheus
7. Load test demonstrates >10 submissions/minute sustained throughput
