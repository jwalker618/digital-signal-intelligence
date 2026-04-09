# Phase C-3: Recalibration Governance UI

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | A-1 (auth -- recalibration:approve permission), A-2 (audit trail), B-2 (config management pipeline for deployment), C-2 (recalibration engine) |

---

## Overview

The "approve" half of propose-and-approve. A dedicated interface where the actuarial/product team reviews, approves, or rejects recalibration proposals before deployment. Closes the feedback loop: loss event -> signal-loss pair -> proposal -> review -> approval -> deployment -> new config version.

## Current State

- C-2 produces `RecalibrationProposal` objects stored in `recalibration_proposals` table
- B-2 provides the config deployment pipeline (version, validate, calibrate, deploy)
- A-1 provides `recalibration:approve` permission
- A-2 provides audit trail
- No governance UI exists

## Target State

Recalibration dashboard with proposal review, signal report cards, impact simulation, approval/rejection with rationale, and deployment through B-2's config management pipeline.

---

## Implementation Plan

### C-3a: Proposal API

**New file**: `infrastructure/api/recalibration/routes.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/recalibration/proposals` | GET | List proposals (filterable by coverage, status, date) |
| `/recalibration/proposals/{id}` | GET | Full proposal detail with evidence |
| `/recalibration/proposals/{id}/approve` | POST | Approve with mandatory rationale (requires `recalibration:approve`) |
| `/recalibration/proposals/{id}/reject` | POST | Reject with mandatory rationale |
| `/recalibration/proposals/{id}/deploy` | POST | Deploy approved proposal (triggers B-2 config pipeline) |
| `/recalibration/proposals/{id}/simulate` | POST | Run proposed weights against current book without deploying |
| `/recalibration/trigger` | POST | Manually trigger recalibration engine for a coverage |

**File to modify**: `infrastructure/api/main.py` -- Mount recalibration router.

### C-3b: Deployment Integration

**New file**: `infrastructure/recalibration/deployer.py`

```python
class ProposalDeployer:
    """Deploys an approved proposal through the B-2 config management pipeline."""

    def deploy(self, proposal_id: str, deployer_id: str) -> None:
        """
        1. Load approved proposal
        2. Generate modified config YAML (apply weight_changes + tier_threshold_changes)
        3. Create config draft via ConfigService (B-2)
        4. Run validation via ConfigService
        5. Run calibration harness via ConfigService
        6. If both pass: deploy via ConfigService
        7. Update proposal status to DEPLOYED
        8. Audit log: full chain from proposal -> config version -> deployment
        """
```

### C-3c: Frontend -- Recalibration Dashboard

**New file**: `frontend/src/app/admin/recalibration/page.tsx`
- Proposal list with status badges (draft, pending, approved, rejected, deployed)
- Filterable by coverage, status, date

**New file**: `frontend/src/app/admin/recalibration/[id]/page.tsx`
- **Proposal detail view** -- the core governance interface:

1. **Signal Report Cards**: Per-signal analysis table. Current weight, evidence-supported weight, discrimination, monotonicity, stability. Traffic-light indicators (green/amber/red alignment).

2. **Weight Change Summary**: Before/after weights for every changed signal. Sortable by magnitude of change.

3. **Tier Threshold Analysis**: Current vs proposed boundaries with loss rate overlay chart.

4. **Impact Assessment**: Tier migration table (entity counts per tier before/after), aggregate premium impact, discrimination improvement metric.

5. **Simulation**: "What-if" button that runs proposed weights against current book, displays results without deploying.

6. **Approval/Rejection**: Action buttons with mandatory rationale text field. Only visible to users with `recalibration:approve`.

**New file**: `frontend/src/components/admin/SignalReportCardTable.tsx`
**New file**: `frontend/src/components/admin/ImpactAssessmentPanel.tsx`
**New file**: `frontend/src/components/admin/TierBoundaryChart.tsx`

### C-3d: Historical Proposals

**In proposal detail page**: Tab showing past proposals (approved, rejected, deployed) for the same coverage, with outcomes and post-deployment loss performance if available.

---

## Constraints

1. Approval requires `recalibration:approve` permission (typically ACTUARIAL or ADMIN)
2. Approval/rejection requires mandatory rationale (non-empty string)
3. Deployment must pass both validation and calibration harness before promoting
4. The entire chain (loss -> pair -> proposal -> review -> deploy -> config version) must be traceable in the audit log
5. Proposals cannot be modified after creation -- amendments create new proposals

## Success Criteria

1. Proposals display with full signal report cards and impact assessment
2. Simulation runs correctly and shows book-wide impact
3. Approval/rejection requires rationale and creates audit entry
4. Deployment updates config.yaml, runs calibration harness, creates new config version
5. The complete chain from loss event to deployed config version is traceable
6. Non-actuarial users cannot approve proposals (permission-gated)
