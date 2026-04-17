# NAIC Model Risk Management (MRM) — DSI Alignment

**Summary.** DSI provides the NAIC MRM control set (inventory,
validation, change control) end-to-end through CI automation +
provenance + golden-entity regression.

## Control mapping

| NAIC MRM element | DSI control |
|------------------|-------------|
| Model inventory | `dsi_config_version_active{coverage, config, version}` Prometheus gauge |
| Validation | Nightly `calibration-nightly.yml` workflow, ECE threshold 0.10 |
| Change control | Required `config-health-gate` CI check on `main` + `develop` |
| Documentation | `coverages/<name>/logic.md` regenerated on every config PR |
| Independent testing | 220-entity golden regression on every PR |
| Governance oversight | Quarterly MRM committee review |
| Data quality | Provenance chain (V6/E2) + absence-as-signal principle |

## Gaps

| Gap | Owner | Due |
|-----|-------|-----|
| Formal MRM committee charter | Compliance + Chief Actuary | 2026-Q3 |
| Annual model inventory certification | Compliance | 2026-Q4 |
| Third-party data vendor due diligence attestations | DPO | 2026-Q4 |
