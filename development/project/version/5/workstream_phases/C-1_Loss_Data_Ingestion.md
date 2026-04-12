# Phase C-1: Loss Data Ingestion & Signal-Loss Correlation

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | None -- can start immediately (backend only) |

---

## Overview

Schema and pipeline for ingesting actual loss events and linking them to DSI assessments. Creates signal-to-loss pairs: the entity's signal profile at bind time paired with the actual loss outcome. This is the data foundation for experience-based recalibration.

## Current State

- `infrastructure/db/models.py` -- `ModelVersionRecord` stores complete assessment snapshots. `ModelVersionSignal` stores per-signal scores at assessment time.
- `infrastructure/db/models.py` -- `Quote` with status (DRAFT/READY/BOUND/EXPIRED/DECLINED) -- bound quotes represent policies.
- No loss event model. No loss ingestion API. No signal-loss linking.

## Target State

Loss event lifecycle management, automatic linking to assessment at bind time, signal-loss pair table for recalibration, and bulk import capability.

---

## Implementation Plan

### C-1a: Loss Event Schema

**Migration**: `alembic/versions/016_loss_data.py`

| Table | Key Columns |
|-------|-------------|
| `loss_events` | `id` (UUID), `tenant_id` FK, `entity_id`, `policy_id`, `claim_reference`, `loss_date`, `notification_date`, `loss_type` (enum: frequency category), `incurred_amount`, `paid_amount`, `reserved_amount`, `status` (OPEN/CLOSED/REOPENED), `coverage`, `config_name`, `cause_description`, `linked_assessment_id` FK to `model_version_records` |
| `signal_loss_pairs` | `id`, `assessment_id` FK, `loss_event_id` FK, `signal_scores_at_bind` (JSONB -- snapshot of all signal scores), `tier_at_bind`, `loss_propensity_at_bind`, `composite_score_at_bind`, `time_to_loss` (days between bind and loss event) |

**Indexes**: `loss_events` on (`entity_id`, `loss_date`); on (`coverage`, `status`); on `tenant_id`. `signal_loss_pairs` on (`assessment_id`); on (`loss_event_id`).

### C-1b: Loss Ingestion API

**New file**: `infrastructure/api/loss/routes.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/losses` | POST | Create loss event |
| `/losses/import` | POST | Bulk CSV/JSON import |
| `/losses/{id}` | PUT | Update loss (amount, status) |
| `/losses` | GET | List with filtering by entity, coverage, date, status |
| `/losses/{id}` | GET | Single loss event with linked assessment |

### C-1c: Signal-Loss Linker

**New file**: `infrastructure/recalibration/linker.py`

```python
class SignalLossLinker:
    """Links loss events to assessment signal profiles at bind time."""

    def link(self, loss_event: LossEvent) -> SignalLossPair:
        """
        1. Find the most recent ModelVersionRecord for entity/coverage
           where associated Quote.status = BOUND and
           Quote.created_at <= loss_event.loss_date
        2. Snapshot all signal scores from ModelVersionSignal
        3. Create SignalLossPair with scores, tier, loss propensity, time_to_loss
        """

    def retrospective_link_all(self) -> int:
        """
        Batch: for all loss_events without a linked assessment,
        attempt to find and link historical assessments.
        Returns count of newly linked pairs.
        """
```

Auto-linking triggers on loss event creation (in the POST handler).

### C-1d: Frontend -- Loss Management

**New file**: `frontend/src/app/admin/losses/page.tsx`

- Loss register: table with filtering by entity, coverage, date, status
- Linked assessment details expandable per row

**New file**: `frontend/src/components/admin/LossEntryForm.tsx`
- Manual loss creation with required fields and validation

**New file**: `frontend/src/components/admin/LossBulkImport.tsx`
- CSV upload with column mapping preview, validation summary, import confirmation

---

## Constraints

1. Signal-loss pairs preserve the exact signal state at bind time (immutable snapshot)
2. Loss amounts are decimal with 2dp precision
3. Bulk import validates all rows before committing any (transactional)
4. Loss events are tenant-scoped

## Success Criteria

1. Loss events can be created, updated, and queried
2. Each loss event is automatically linked to the assessment at bind time
3. Signal-loss pair table is populated with signal snapshots
4. Bulk import handles CSV with validation and error reporting
5. Retrospective linker correctly matches historical losses to historical assessments
