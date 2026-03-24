# Signal Audit Value API Endpoint - Implementation Plan

## Overview

Create a `POST /api/v1/signals/{quote_code}/override` endpoint that:
1. Accepts a `quote_code` + `signal_code` + `audited_value` (plus metadata)
2. Resolves the quote → latest model version → specific model_version_signal row
3. Creates a **new model version** (lightweight recalc — no re-extraction)
4. Copies all model_version_signal bindings, applying the override to the target signal
5. Recalculates composite score, tier, and pricing from the overridden signal data
6. Records a `signal_audit_record` against the new model_version_signal
7. Updates the quote's `model_version_id` FK to point to the new version
8. Creates a new referral record (always, when decision = refer)
9. Returns a `SignalOverrideResponse` with before/after scoring data

## Files to Modify

### 1. `infrastructure/api/types.py`
- **Update `SignalOverrideRequest`**: Change from `signal_cache_id + signal_code` to `quote_code + signal_code`. Fields:
  - `signal_code: str`
  - `audited_value: float`
  - `rationale: str`
  - `evidence_reference: Optional[str]`
  - `underwriter_id: Optional[str]`
- `SignalOverrideResponse` already has the right shape — no changes needed.

### 2. `infrastructure/api/routes/signals.py` (NEW FILE)
- New route module dedicated to signal audit/override operations
- Single endpoint: `POST /signals/{quote_code}/override`
- **Endpoint logic** (single atomic transaction via shared `db` session):

  **a. Resolve context:**
  - Fetch Quote by `quote_code` → get `model_version_id` and `submission_id`
  - Fetch current ModelVersionRecord by `model_version_id`
  - Fetch all ModelVersionSignal rows for that model version
  - Find the specific signal row matching `signal_code` (join to `signals` table)
  - 404 if quote/signal not found, 400 if quote expired/bound

  **b. Create new model version (lightweight recalc):**
  - Use `ModelVersionRepository.create()` with `version_type="signal_override"`
  - This auto-increments `version_number` and sets `is_latest=True`

  **c. Copy signal bindings with override:**
  - Use `ModelVersionSignalRepository.copy_to_new_version()` passing:
    - `override_signal_id` = the integer signal_id being overridden
    - `override_values` = `{"score": audited_value}` — this replaces the signal's score

  **d. Recalculate composite score + tier + pricing:**
  - Fetch all new model_version_signal rows
  - Compute weighted composite: `sum(score * weight) / sum(weight)` for each group, then weighted group average
  - Use the coverage config to determine new tier from score
  - Use the pricer to recalculate premium from new tier
  - Update the new model version record with recalculated values

  **e. Record signal audit:**
  - Find the new model_version_signal row for the overridden signal
  - Use `SignalAuditRepository.create_override()` with impact tracking:
    - `score_impact` = new_composite - old_composite
    - `tier_impact` = new_tier - old_tier

  **f. Update quote FK:**
  - Use `QuoteRepository.update_model_version_id()` to point to new version
  - Update `recommended_premium` if pricing changed

  **g. Create referral (if decision = refer):**
  - Determine decision from new tier
  - If refer: use `ReferralRepository.create()` with reason "Signal override triggered referral"
  - Always create a new referral regardless of existing ones

  **h. Commit and respond:**
  - Single `await db.commit()` — all operations share the same session
  - Build and return `SignalOverrideResponse`

### 3. `infrastructure/api/routes/__init__.py`
- Add `from . import signals` and include in `__all__`

### 4. `infrastructure/api/main.py`
- Import and include the signals router: `app.include_router(signals.router, prefix="/api/v1", tags=["Signals"])`
- Add `"signals": "/api/v1/signals"` to the api_info endpoint

## Issues Found in Existing API

### quotes.py line 47: Wrong column reference
`Quote.quote_id` should be `Quote.quote_code` — the `Quote` model has `quote_code`, not `quote_id`.

### modelversion.py: Duplicate route paths
All 5 endpoints share the same path `GET /modelversion/{version_code}` — only the first registered will ever match. These need differentiated paths (e.g., query parameter `?projection=base|detail|commentary|loss|exposure`, or subpaths like `/modelversion/{version_code}/base`).

### modelversion.py: Querying Pydantic DTOs instead of ORM models
The endpoints query `select(ModelVersionDBRecord_BaseOnly)` but these are Pydantic models, not SQLAlchemy models. Should query `select(ModelVersionRecord)` and project into the DTO.

### submissions.py line 386: Wrong error message
`raise HTTPException(status_code=404, detail="Referral not found")` should say "Submission not found".

I will fix the `quotes.py` bug and the `submissions.py` error message as part of this change. The modelversion.py issues are structural and out of scope for this PR but flagged for your awareness.
