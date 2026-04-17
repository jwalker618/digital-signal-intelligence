# DSI Chaos Manifests (V6/C5b)

Chaos-Mesh CRDs targeting the staging cluster. Expected behaviour is
documented with each manifest — the weekly chaos report (see
`docs/ops/reports/`) asserts every scenario passed.

| Scenario | Blast radius | Expected |
|----------|-------------|----------|
| `kill-api-replica.yaml` | 1 pod hourly | HPA recovery < 60s, no 5xx |
| `redis-partition.yaml` | 60s daily | Fallback to uncached extraction + confidence penalty |
| `extractor-latency-inject.yaml` | 2s jitter weekly | Span exceeds threshold → shed path |
| `pg-readonly.yaml` | 90s weekly | Degrade to read-only, serve cached quotes |

## Manual replay

```
kubectl apply -f kill-api-replica.yaml
kubectl delete -f kill-api-replica.yaml
```
