# Phase 8: Deterministic Referral Management & Signal Auditing

## Context & Problem Statement
In traditional underwriting, a "Referral" initiates a negotiation. Underwriters apply subjective, discretionary credits or debits to a premium to win a deal. In the DSI framework, this breaks the mathematical integrity of the system and corrupts the feedback loop; as the Whitepaper mandates, "No subjective adjustments are permitted". 

If an underwriter manually alters the final premium, the system can no longer mathematically correlate the input signals to the loss ratio. 

## Phase 8 Objective
To build a deterministic Referral Management workflow where underwriters do not negotiate *outputs* (the premium), but rather audit and correct *inputs* (the signals). 
Crucially, **the original inferred signal must be preserved permanently** to track the accuracy of our external data providers and trigger automated feedback loops.

## 8.1 The Data Model: Preserving the Original Signal
To allow an underwriter to alter a signal while preserving the original inference, the signal payload must be refactored to support an `audit_trail`.

**Old Signal Payload (Phase 7):**
```json
{
  "signal_id": "psc_detention",
  "value": true,
  "source": "inference_engine"
}
```

**New Signal Payload (Phase 8):**

```json
{
  "signal_id": "psc_detention",
  "inferred_value": true,          // PERMANENT: The original machine extraction
  "audited_value": false,          // MUTABLE: The value actually used in the math engine
  "is_overridden": true,
  "audit_trail": {
    "overridden_by": "usr_8921",
    "timestamp": "2026-02-16T08:30:00Z",
    "rationale": "Verified via direct vessel log provided by broker.",
    "evidence_reference": "doc_4492.pdf"
  }
}
```

Architecture Rule: The Pricing Engine and Scorer must always calculate using the audited_value. If is_overridden is false, audited_value simply mirrors inferred_value.

## 8.2 Backend Implementation: The Model Cycle
When an underwriter submits a Factual Signal Override from the UI:

The backend receives the override payload and updates the audited_value.

The backend triggers a new Model Cycle.

The engine recalculates the composite score, risk tier, and final premium based on the new truth.

The output is saved as a new Model Version, ensuring that both the original machine-priced version (v1) and the human-audited version (v2) exist immutably in the database.

## 8.3 Frontend UX/UI Guidelines
The Referral screen must guide the user into the "Signal Auditing" mindset.

The Referral Trigger: A high-visibility banner identifying exactly which direct_query or score_condition halted straight-through processing.

The Signal Ledger: A list of all signals. Signals must display padlock icons. Clicking the padlock opens an "Override Modal" requiring the new value and a mandatory text rationale.

The Decision Block: If the signals are 100% factually correct but the risk is poor, the underwriter cannot change the premium. They are presented with the engine's calculated technical premium and two buttons: Approve Quote or Decline Risk, alongside a mandatory decision rationale box.

## 8.4 Engineering Tasks
[ ] Refactor infrastructure/api/schemas.py to support the audited_value and audit_trail fields.

[ ] Update layers/risk/scorer.py to ensure all weighting and scoring strictly pull from audited_value.

[ ] Build the /api/v1/submissions/{id}/override endpoint to accept signal corrections and trigger a new Model Cycle.
