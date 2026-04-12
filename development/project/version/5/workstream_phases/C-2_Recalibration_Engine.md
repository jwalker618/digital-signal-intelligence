# Phase C-2: Recalibration Engine

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | C-1 (loss data and signal-loss pairs) |

---

## Overview

The analytical engine that consumes signal-loss pairs and proposes config adjustments. This is the "propose" half of propose-and-approve. It analyses per-signal predictive power, optimises weights, evaluates tier boundaries, and generates fully-evidenced proposals with impact assessments.

## Current State

- `signal_loss_pairs` table from C-1 provides the input data
- `layers/risk/calibration_harness.py` -- `CalibrationHarness` validates pricing sanity but does not perform experience-based recalibration
- `infrastructure/analytics/signal_analytics.py` -- Signal contribution analysis exists but not tied to loss outcomes
- `analysis_outputs/{coverage}_v{date}.yaml` files defined in architecture but not auto-generated
- No automated recalibration capability

## Target State

Recalibration engine that analyses signal-loss correlation, proposes weight/threshold changes with full statistical evidence, computes book-wide impact, and stores proposals for governance review.

---

## Implementation Plan

### C-2a: Recalibration Schema

**Migration**: `alembic/versions/017_recalibration.py`

| Table | Key Columns |
|-------|-------------|
| `recalibration_proposals` | `id` (UUID), `tenant_id`, `coverage`, `config_name`, `proposed_at`, `proposed_by` ("system" or user_id), `status` (DRAFT/PENDING_REVIEW/APPROVED/REJECTED/DEPLOYED), `signal_report_cards` (JSONB), `weight_changes` (JSONB), `tier_threshold_changes` (JSONB), `impact_assessment` (JSONB), `statistical_evidence` (JSONB), `reviewer_id`, `review_decision`, `review_rationale`, `reviewed_at` |

### C-2b: Signal Predictive Power Analysis

**New file**: `infrastructure/recalibration/signal_analysis.py`

```python
class SignalAnalyser:
    """Per-signal predictive power analysis against loss outcomes."""

    def analyse(self, coverage: str, config_name: str) -> list[SignalReportCard]:
        """
        For each signal in the config:
        1. Discrimination: Mann-Whitney U between loss/no-loss entity scores
        2. Monotonicity: Spearman correlation between score and loss outcome
        3. Stability: discrimination computed in rolling time windows
        4. Contribution: Information Value (IV) or Gini coefficient
        Output: report card with current weight vs evidence-supported weight
        """

class SignalReportCard(BaseModel):
    signal_id: str
    group_code: str
    current_weight: float
    discrimination_u_stat: float
    discrimination_p_value: float
    monotonicity_rho: float
    stability_coefficient: float       # CV of discrimination across windows
    information_value: float
    evidence_supported_weight: float    # What the data suggests
    alignment: str                      # well_calibrated | adjustment_suggested | significant_misalignment
```

### C-2c: Weight Optimiser

**New file**: `infrastructure/recalibration/weight_optimiser.py`

```python
class WeightOptimiser:
    """Computes optimal weight vector maximising loss discrimination."""

    def optimise(
        self, signal_loss_data: DataFrame, current_config: CoverageConfig
    ) -> list[WeightChange]:
        """
        Constrained optimisation (scipy.optimize):
        - Weights sum to group totals (normalised)
        - No negative weights
        - No single signal > max_weight cap (prevents overfitting)
        Method: logistic regression coefficients normalised to weight scale,
        or gradient-based with constraints.
        """
```

### C-2d: Tier Threshold Analysis

**New file**: `infrastructure/recalibration/tier_analysis.py`

```python
class TierAnalyser:
    """Evaluates whether tier boundaries optimally separate loss frequency."""

    def analyse(self, coverage: str, config_name: str) -> list[TierThresholdChange]:
        """
        Compute loss rate per current tier band.
        If adjacent tiers have similar loss rates, boundary should shift.
        Propose threshold adjustments with statistical evidence.
        """
```

### C-2e: Proposal Generator

**New file**: `infrastructure/recalibration/proposal.py`

```python
class ProposalGenerator:
    """Packages analysis into a RecalibrationProposal with impact assessment."""

    def generate(self, coverage: str, config_name: str) -> RecalibrationProposal:
        """
        1. Run SignalAnalyser -> report cards
        2. Run WeightOptimiser -> weight changes
        3. Run TierAnalyser -> threshold changes
        4. Run ImpactAssessment:
           - Rerun proposed weights against current assessment database
           - Compute tier migration (how many entities change tier)
           - Compute aggregate premium impact
           - Compute discrimination improvement
        5. Package into RecalibrationProposal, store with status=DRAFT
        """
```

**New file**: `infrastructure/recalibration/impact.py`

```python
class ImpactAssessor:
    """Computes real-world impact of proposed config changes."""

    def assess(self, proposal: RecalibrationProposal) -> ImpactAssessment:
        """
        Rerun ModelScorer with proposed weights on all assessments in DB.
        Compare: tier migrations, premium deltas, discrimination improvement.
        """
```

### C-2f: Orchestrator & Scheduling

**New file**: `infrastructure/recalibration/engine.py`

```python
class RecalibrationEngine:
    """Main orchestrator for the recalibration pipeline."""

    def run(self, coverage: str, config_name: str, trigger: str = "manual") -> RecalibrationProposal:
        """Full pipeline: analyse -> optimise -> assess impact -> generate proposal."""

    def should_run(self, coverage: str) -> bool:
        """
        Run if:
        - Loss events since last run > 50
        - OR time since last run > 90 days
        - OR manual trigger by actuarial user
        """
```

---

## Constraints

1. Use `scipy.stats` for statistical tests, `scipy.optimize` for constrained optimisation. No custom statistics.
2. Weight optimisation respects config architecture: weights sum to group totals, no negatives
3. Proposals are read-only after creation -- amendments create new proposals
4. Minimum sample size: refuse to generate proposals with < 30 signal-loss pairs

## Success Criteria

1. Signal report cards correctly identify high/low predictive signals in synthetic data
2. Weight optimiser produces valid weight vectors that respect constraints
3. Tier analysis correctly identifies suboptimal boundaries
4. Proposals include full statistical evidence and impact assessment
5. The engine runs end-to-end on seed data with synthetic losses
