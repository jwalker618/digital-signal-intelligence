# Workstream C — Deployment Readiness

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | — (C1–C3 land first in Q1 and gate everything else) |
| Phases | C1–C7 |

---

## Overview

Make DSI production-deployable: real CI deploys (not echo stubs), secrets via External Secrets Operator, OpenTelemetry observability, consolidated seeding under a single `python -m seed` CLI, load + chaos testing, a regulatory artefact kit, and a config health gate enforcing coverage correctness.

---

## C1 — CI Deploy Wiring

**File**: `.github/workflows/ci.yml`

Replace the `deploy-staging` and `deploy-production` echo blocks with real steps:

```yaml
deploy-staging:
  name: Deploy to Staging
  needs: [docker-build, config-health-gate]
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/develop'
  environment: staging
  steps:
    - uses: actions/checkout@v4
    - uses: azure/setup-kubectl@v4
    - name: Configure kubeconfig (OIDC)
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${{ secrets.STAGING_ROLE_ARN }}
        aws-region: ${{ secrets.STAGING_REGION }}
    - name: Update kubeconfig
      run: aws eks update-kubeconfig --name dsi-staging --region ${{ secrets.STAGING_REGION }}
    - name: Preview migrations
      run: alembic upgrade head --sql > migration-preview.sql
    - uses: actions/upload-artifact@v4
      with: { name: migration-preview, path: migration-preview.sql }
    - name: Apply migrations
      run: alembic upgrade head
    - name: Deploy via Argo Rollouts
      run: |
        kubectl argo rollouts set image dsi-api \
          dsi-api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
          -n dsi-staging
        kubectl argo rollouts wait dsi-api -n dsi-staging --timeout=10m
    - name: Smoke test (golden-entity assessment)
      run: |
        curl -sf https://staging.dsi.internal/api/v1/health/ready
        curl -sfX POST https://staging.dsi.internal/api/v1/assess \
          -H "Authorization: Bearer ${{ secrets.STAGING_SMOKE_TOKEN }}" \
          -d @tests/fixtures/smoke/cyber_golden.json
    - name: Rollback on failure
      if: failure()
      run: kubectl argo rollouts undo dsi-api -n dsi-staging
```

`deploy-production` is identical except:
- Gated `if: github.ref == 'refs/heads/main'`.
- `environment: production` (manual approval in GitHub).
- Canary strategy: `setWeight: 20 → pause → setWeight: 50 → pause → setWeight: 100`.
- Smoke test runs against three coverages, not one.

**New manifest**: `deploy/kubernetes/rollout.yaml` replacing `deployment.yaml` for the API. Blue/green is overkill; prefer canary.

**Acceptance**:
- Staging deploy triggered from `develop` branch lands a real image and passes smoke.
- Production deploy from `main` requires manual approval and executes canary.
- Rollback tested by deliberately breaking a smoke test and confirming revert.

---

## C2 — External Secrets Operator

**New manifests**: `deploy/kubernetes/external-secrets/`

```
external-secrets/
├── cluster-secret-store.yaml     # SecretStore (AWS SSM / Vault / GCP SM)
├── externalsecret-api-secrets.yaml
├── externalsecret-db-credentials.yaml
└── externalsecret-extractor-keys.yaml
```

**Managed keys**:
| Secret | Consumer | Source Path |
|--------|----------|-------------|
| `JWT_SECRET_KEY` | API | `/dsi/{env}/jwt-key` |
| `DATABASE_URL` | API, migrations | `/dsi/{env}/db-url` |
| `REDIS_URL` | API, workers | `/dsi/{env}/redis-url` |
| `OFAC_ACCESS_KEY` | extractor-sanctions | `/dsi/{env}/ofac-key` |
| `SHODAN_API_KEY` | extractor-network | `/dsi/{env}/shodan-key` |
| `SSC_API_KEY` | extractor-security-ratings | `/dsi/{env}/ssc-key` |
| `MSCI_API_KEY` | extractor-esg | `/dsi/{env}/msci-key` |
| `CRUNCHBASE_API_KEY` | extractor-corporate | `/dsi/{env}/crunchbase-key` |
| `GITHUB_PAT` | extractor-web | `/dsi/{env}/github-pat` |
| `URLSCAN_API_KEY` | extractor-web | `/dsi/{env}/urlscan-key` |
| `HIBP_API_KEY` | extractor-breach | `/dsi/{env}/hibp-key` |
| `BUILTWITH_API_KEY` | extractor-stack | `/dsi/{env}/builtwith-key` |
| `OPENCORPORATES_API_KEY` | extractor-corporate | `/dsi/{env}/oc-key` |
| `SP_RATINGS_API_KEY` | extractor-ratings | `/dsi/{env}/sp-key` |
| `ISS_API_KEY` | extractor-esg | `/dsi/{env}/iss-key` |
| `OPENSKY_API_KEY` | extractor-aviation | `/dsi/{env}/opensky-key` |

**Kustomize overlays**: `deploy/kubernetes/overlays/{staging,production}/` each reference a different SecretStore. `kustomization.yaml` in each overlay lists only the ExternalSecrets valid for that env (staging can use mock keys; production must have all).

**Deprecation**: `deploy/kubernetes/secrets-template.yaml` stays as documentation only with a banner comment "use External Secrets Operator in real deployments."

**Acceptance**:
- `kubectl get externalsecret -n dsi-prod` shows Synced for all listed keys.
- API pods can start without any hard-coded secret in manifests.
- Rotating a secret in the backing store propagates within the configured refresh window (60s default).

---

## C3 — Observability

**New package**: `infrastructure/api/observability/otel.py`

Instruments:
- FastAPI via `opentelemetry-instrumentation-fastapi`.
- SQLAlchemy via `opentelemetry-instrumentation-sqlalchemy`.
- Redis via `opentelemetry-instrumentation-redis`.
- Outbound HTTP via `opentelemetry-instrumentation-requests` + `httpx`.

**Per-extractor spans**: hook in `signal_architecture/signals/extractors/production/base.py`:
```python
class ProductionExtractor:
    def extract(self, entity_id, context):
        with tracer.start_as_current_span(
            f"extractor.{self.SOURCE_NAME}",
            attributes={
                "dsi.entity_id": entity_id,
                "dsi.coverage": context.coverage,
                "dsi.config": context.config_name,
                "dsi.cost_tier": self.get_cost_tier(),
                "dsi.cache_hit": False,  # updated below
            },
        ) as span:
            ...
```

**Four Gold-Signal SLOs** (`deploy/monitoring/slos.yaml`):
| SLO | Target | Burn-rate alert |
|-----|--------|-----------------|
| Availability | 99.5% monthly | 14.4× for 1h, 6× for 6h |
| Latency p95 (`/api/v1/assess`) | < 5s | breach sustained 10m |
| Error rate | < 0.5% | breach sustained 5m |
| Saturation (DB conns) | < 80% | breach sustained 15m |

**Grafana dashboards** (`deploy/monitoring/grafana/`):
- `api-overview.json` — RED method + SLO burn.
- `extractors.json` — per-extractor latency, cache hit rate, error rate, cost-tier cost estimate.
- `configs.json` — active config version per pod, calibration status per coverage, drift alert count.
- `world-engine.json` — maturity stage, population size, drift detections, scanner cadence.

**Config-activity metric**: `dsi_config_version_active{coverage, config, version}` emitted on every pod at `/metrics`. This is how on-call tells which config is serving traffic.

**Acceptance**:
- OTLP collector receives traces for every assessment; one assessment produces a trace with spans for discovery, every extractor, scoring, pricing, decision.
- Grafana dashboards populated from staging within 1 hour of deploy.
- One synthetic SLO breach triggers a PagerDuty alert in staging.

---

## C4 — Seed Consolidation

**New package layout**:

```
seed/
├── __init__.py
├── cli.py                # python -m seed <command>
├── bench.py              # was seed_dsi_bench.py -> `seed bench`
├── v5.py                 # was seed_v5.py        -> `seed v5`
├── synthetic.py          # was synthetic_generator.py -> `seed synthetic`
├── reset.py              # new: truncate + reseed in dependency order
├── verify.py             # assert expected row counts per table
├── fixtures/             # YAML/JSON fixtures extracted from code
│   ├── tenants.yaml
│   ├── demo_users.yaml
│   ├── golden_entities.yaml (shared with E5)
│   └── synthetic_profiles.yaml
└── README.md
```

**CLI**:
```bash
python -m seed init --tenant dsi-demo --entities 500    # runs reset + bench + v5 + synthetic
python -m seed bench                                     # just the bench portion
python -m seed v5                                        # v5 augment only
python -m seed synthetic --coverage cyber --n 100
python -m seed reset --confirm
python -m seed verify                                    # asserts expected counts
```

**Execution order enforced by `init`**: `reset` → `bench` → `v5` → `synthetic` — never touched twice.

### Phase steps

1. **C4a (interim, Q1)**: Create `seed/` package with bench + v5 + synthetic moved verbatim into the new modules, exposed via the CLI. Old scripts remain but emit a `DeprecationWarning` and internally delegate.
2. **C4b (final, Q4)**: Delete `seed_dsi_bench.py`, `seed_v5.py`, `synthetic_generator.py`, `synthetic_generator.py.bak` (if present) from the repo root. Update Makefile, CI, docs, SKILL.md, README.md. Add `seed verify` to the nightly CI job against staging.

**Acceptance**:
- `python -m seed init --tenant dsi-demo --entities 500` runs idempotently against a fresh PostgreSQL, leaving the DB in a known-good state.
- `python -m seed verify` returns 0 differences against the documented row-count contract.
- Repo root is clean of seeding scripts after C4b.

---

## C5 — Load + Chaos Testing

### C5a — Load testing

**New directory**: `tests/performance/k6/`

```
k6/
├── scenarios/
│   ├── single_assessment.js         # Baseline: one coverage assessment
│   ├── multiplex_race.js            # All candidate configs concurrent
│   └── extractor_timeout_storm.js   # Slow external APIs, measure shedding
├── reports/                          # Output HTML + JSON
└── run.sh                            # CI entry
```

**Acceptance targets**:
- Single assessment: p95 < 5s at 50 RPS, p99 < 10s.
- Multiplex race: p95 < 8s at 20 RPS, no cross-config leakage.
- Timeout storm: graceful degradation (shed → neutral score + confidence penalty), no 5xx spikes.

**CI integration**: nightly job against staging; uploaded k6 HTML report + JSON summary artefact.

### C5b — Chaos testing

**New directory**: `tests/chaos/`

Chaos Mesh manifests (CRDs):
- `kill-api-replica.yaml` — terminate 1 of N API pods; expect HPA recovery.
- `redis-partition.yaml` — partition Redis for 60s; expect fallback to uncached extraction + degraded confidence, no 5xx.
- `extractor-latency-inject.yaml` — 2s latency injection on one extractor; expect span to exceed threshold, shedding to kick in.
- `pg-readonly.yaml` — flip DB primary to read-only; expect API to degrade to read-only mode, serve cached quotes.

**CI integration**: weekly chaos run against staging; report uploaded.

**Acceptance**:
- Every chaos scenario has a documented expected behaviour and is green in last run.
- Nightly perf-report.md + weekly chaos-report.md published in `docs/ops/reports/`.

---

## C6 — Regulatory Artefact Kit

**New directory**: `docs/regulatory/`

| File | Purpose |
|------|---------|
| `lloyds_model_use_and_governance.md` | Lloyd's MU&G compliance statement, citing the 14-step workflow + audit trail. |
| `naic_model_risk_management.md` | NAIC MRM alignment: model inventory, validation, change control (maps to our config-version audit). |
| `fca_fg21_3_algorithmic_pricing.md` | UK FCA FG21/3 alignment on algorithmic pricing, inc. fairness testing. |
| `gdpr_dpia.md` | Data Protection Impact Assessment template — entity profiling under Article 35. |
| `eu_ai_act_risk_classification.md` | DSI's AI-Act risk classification (likely high-risk via Annex III creditworthiness-adjacent use). |
| `us_state_doi_rate_filing_template.md` | Template for SERFF filings — IL/CA/TX first. |
| `noaic_data_lineage_statement.md` | Chain-of-custody statement (ties to E2 provenance hash). |
| `fairness_testing_report_template.md` | Disparate-impact testing template for protected classes where applicable. |

**Delivery**: each file must carry (a) one-sentence summary, (b) mapping table from regulatory requirement → DSI artefact/code path, (c) gaps with owner + due date. Not prose-for-prose's-sake; templates that regulators can read.

**Acceptance**:
- Legal / compliance reviewer signs off on each template.
- CI job verifies every link inside these docs resolves (internal references only).
- External counsel review scheduled (out-of-scope for this workstream, tracked separately).

---

## C7 — Config Health Gate (shared with E2; owned here from CI perspective)

**New CI job**: `config-health-gate`

Runs:
1. `python development/project/assessments/scripts/assess_project.py --save-report --fail-on-warning`.
2. `python development/project/assessments/scripts/assess_config_compliance.py coverages/{name}/config.yaml` for every coverage.
3. `python -m infrastructure.builder.cli calibrate --all --strict`.
4. `python -m coverages.doc_generator --check` (fails if `logic.md` is out-of-date w.r.t. `config.yaml`).

**Enforcement**: Required check on `main` and `develop` branches — merges blocked until green.

**Config-diff comment**: On every PR touching `coverages/**/config.yaml`, a GitHub comment is posted containing:
- Diff of `logic.md` (rendered).
- Changed signal weights, grouped by dimension (risk/loss/exposure).
- Change in theoretical premium for the 10 golden entities of that coverage.
- ILF-curve delta at key limit anchor points.

Implemented in `.github/workflows/config-diff.yml` calling `infrastructure/builder/cli.py diff-config`.

**Acceptance**:
- A PR that breaks `calibrate` is blocked.
- A PR that touches a config shows a rich diff comment within 2 minutes of push.
- The nightly job also runs the gate against `main` and opens an issue if drift is detected.

---

## Acceptance for Workstream C

- `kubectl get rollout dsi-api -n dsi-production` shows a successful canary deploy from `main`.
- All 16 ExternalSecrets are Synced in production.
- OpenTelemetry traces visible in the chosen backend for every assessment.
- Single `python -m seed init` command bootstraps a clean environment.
- Nightly load report green; weekly chaos report green.
- `docs/regulatory/` populated with all eight templates and reviewed internally.
- Config health gate required and enforced on `main` + `develop`.
- Three-legacy-seed-scripts deleted from repo root.
