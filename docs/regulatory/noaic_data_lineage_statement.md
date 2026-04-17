# Data Lineage Statement (Chain-of-Custody)

**Summary.** Every premium produced by DSI traces end-to-end through a
verifiable Merkle-style hash chain. Regulators and reinsurers can
re-derive the hash of any raw extracted response and verify it matches
the stored provenance; any tampering up-chain invalidates the
downstream self-hash.

## Chain components

1. **Raw extractor response** — sha256 hashed as `response_hash` at
   extraction time (see `signal_architecture/signals/provenance.py`).
2. **Provenance record** — `source_name`, `source_url`,
   `request_timestamp`, `response_etag`, `response_status_code`,
   `cache_hit`, `extractor_version`, `parent_hashes`.
3. **`self_hash`** — sha256 over the Provenance payload + the parent
   hashes. Any tamper up-chain invalidates this.
4. **Quote-level chain** — every signal contributing to a quote is
   linked via `provenance_chain(parent_hash, child_hash, assessment_id)`.
5. **Audit retrieval** — `GET /api/v1/quotes/{id}/provenance` (landing
   Q4) returns the full chain, verifiable via `verify_chain()`.

## Verification procedure

```python
from signal_architecture.signals.provenance import verify_chain, build_provenance
chain = [build_provenance(...) for node in stored_nodes]
assert verify_chain(chain)
```

## Gaps

| Gap | Owner | Due |
|-----|-------|-----|
| Alembic migration 021_signal_provenance | Platform | 2026-Q4 |
| API endpoint `/api/v1/quotes/{id}/provenance` | Platform | 2026-Q4 |
| Reinsurer-facing verification CLI (`dsi verify-chain`) | Platform | 2027-Q1 |
