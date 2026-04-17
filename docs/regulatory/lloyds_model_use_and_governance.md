# Lloyd's Model Use & Governance (MU&G) — DSI Compliance Statement

**Summary.** DSI operates under a Lloyd's MU&G-aligned governance
framework. Every config change is validated, diffed, calibrated, and
regression-tested before production; every premium traces through a
Merkle-style provenance chain to the underlying raw signals.

## MU&G → DSI artefact mapping

| MU&G expectation | DSI artefact | Code path |
|------------------|--------------|-----------|
| Model inventory | `infrastructure/admin/config_service.py`; Evidence Dashboard | `/api/v1/admin/evidence` |
| Change control | Config Health Gate, Config-Diff PR comment | `.github/workflows/ci.yml#config-health-gate`, `.github/workflows/config-diff.yml` |
| Validation | Calibration harness + Golden-entity regression | `infrastructure/validation/confidence_calibration.py`, `tests/integration/test_golden_entities.py` |
| Monitoring | Drift detector + referral bridge | `world_engine/drift/detector.py`, `world_engine/drift/referral_bridge.py` |
| Data lineage | Provenance chain (Merkle-style) | `signal_architecture/signals/provenance.py` |
| Independent review | External actuary (semi-annual) | Scheduled; `docs/ops/reports/external_counsel.md` |
| User-access control | Auth + RBAC + per-tenant overlays | `infrastructure/api/auth/`, `infrastructure/models/overlay_loader.py` |
| Model documentation | `coverages/<name>/logic.md` (auto-generated) | `coverages/doc_generator.py` |

## Gaps

| Gap | Owner | Due |
|-----|-------|-----|
| Model inventory JSON export signed by Head of MRM | Compliance | 2026-Q4 |
| External actuary engagement | Chief Actuary | 2026-Q3 |
| Cyber-risk-scenario quarterly tabletop | DPO + Platform | 2026-Q4 |
